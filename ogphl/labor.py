"""
Labor supply targets and the chi_n calibration for OG-PHL (ported from
OG-ETH's ogeth/labor.py).

chi_n, the age profile of the disutility of labor, is calibrated so that
the model's average labor supply by age matches hours worked per person in
the Philippine Labor Force Survey (ILOSTAT, 2024). The calibration solves the
steady state repeatedly, rescaling chi_n between solves by the ratio of
marginal disutilities at the model's and the data's labor supply, which is
the exact adjustment when consumption and prices are held fixed.

    python -m ogphl.labor

runs it and writes chi_n into the packaged parameters.
"""

import copy
import json
import os

import numpy as np
from ogcore import SS, household

from ogphl import income, warm_start

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
JSON_PATH = os.path.join(CUR_PATH, "ogphl_default_parameters.json")

HOURS_YEAR = 2024
# OG-USA's convention: labor supply is the share of a 16-hour waking day,
# seven days a week
WEEKLY_TIME_ENDOWMENT = (24 - 8) * 7
# beyond the survey's last band (65+, at its midpoint) the target tapers with
# the NTA per-capita labor income profile, and never below this share of the
# time endowment
OLDEST_SURVEY_AGE = 67
MIN_LABOR_SUPPLY = 0.02
# ages over which the fit is judged; older households supply little labor
# and their targets are extrapolated
FIT_AGES = (20, 80)
DEFAULT_MAX_ITER = 40
DEFAULT_TOL = 0.02
# each step moves chi_n half way, in logs, to the exact rescaling: from the
# OG-USA profile the full step is 4-5 times at prime ages and over 100 at the
# youngest and oldest
STEP_DAMPING = 0.5
# OG-Core's upper bound on chi_n; it binds only at the oldest ages, where
# the target is an extrapolation and little labor is supplied anyway
MAX_CHI_N = 10000.0


def model_ages(E, S):
    """Age in years of each model period (one period per year)."""
    return np.arange(E, E + S)


def labor_supply_target(E, S, ltilde=1.0):
    """
    Average labor supply by model age, as a share of the time endowment,
    from Labor Force Survey hours per person.

    Args:
        E (int): age at which agents become economically active
        S (int): number of model periods in a lifetime
        ltilde (float): time endowment per period

    Returns:
        target (Numpy array): average labor supply by age, length S

    """
    ages = model_ages(E, S)
    hours = income.hours_per_person("PHL", HOURS_YEAR, ages)
    target = hours / WEEKLY_TIME_ENDOWMENT * ltilde
    old = ages > OLDEST_SURVEY_AGE
    if old.any():
        nta = income._load_nta_profile("PHL")
        nta = nta[max(nta)]
        taper = (
            nta[np.minimum(ages[old], len(nta) - 1)] / nta[OLDEST_SURVEY_AGE]
        )
        # the NTA profile stops at 80; beyond it the floor applies
        taper = np.nan_to_num(taper, nan=0.0)
        target[old] = target[ages == OLDEST_SURVEY_AGE][0] * taper
    return np.maximum(target, MIN_LABOR_SUPPLY * ltilde)


def average_labor_supply(n, omega_SS):
    """
    Population-weighted average labor supply by age.

    Args:
        n (Numpy array): labor supply by age and group, size (S, J)
        omega_SS (Numpy array): joint population distribution, size (S, J)

    Returns:
        n_avg (Numpy array): average labor supply by age, length S

    """
    return (n * omega_SS).sum(axis=1) / omega_SS.sum(axis=1)


def marginal_disutility(n, p):
    """
    Marginal disutility of labor with unit weights, from OG-Core's
    elliptical utility function.

    Args:
        n (Numpy array): labor supply, length S
        p (OG-Core Specifications object): model parameters

    Returns:
        mdu (Numpy array): marginal disutility at each labor supply

    """
    n = np.asarray(n, dtype=float)
    return household.marg_ut_labor(n, np.ones_like(n), p)


def chi_n_step(chi_n, n_model, n_target, p, damping=1.0):
    """
    Rescale chi_n so that, at fixed consumption and prices, the labor
    supply first-order condition holds at the target instead of the model
    value. With damping below one the rescaling is raised to that power.

    Args:
        chi_n (Numpy array): current disutility weights, length S
        n_model (Numpy array): model average labor supply, length S
        n_target (Numpy array): target average labor supply, length S
        p (OG-Core Specifications object): model parameters
        damping (float): power on the exact rescaling, in (0, 1]

    Returns:
        chi_n_new (Numpy array): updated disutility weights, length S

    """
    ratio = marginal_disutility(n_model, p) / marginal_disutility(n_target, p)
    return np.minimum(chi_n * ratio**damping, MAX_CHI_N)


def steady_state_chi_n(p):
    """
    The steady-state row of chi_n, whatever its stored shape.

    Args:
        p (OG-Core Specifications object): model parameters

    Returns:
        chi_n (Numpy array): disutility weights by age, length S

    """
    chi_n = np.asarray(p.chi_n, dtype=float)
    if chi_n.ndim == 2:
        chi_n = chi_n[-1]
    return chi_n.copy()


def estimate_chi_n(
    p,
    client=None,
    max_iter=DEFAULT_MAX_ITER,
    tol=DEFAULT_TOL,
    verbose=True,
    warm=None,
):
    """
    Calibrate chi_n to the Labor Force Survey labor supply profile by
    repeated steady-state solves.

    Args:
        p (OG-Core Specifications object): model parameters
        client (Dask client object): client for parallel computation
        max_iter (int): maximum number of steady-state solves
        tol (float): largest acceptable relative gap between model and
            target labor supply over FIT_AGES
        verbose (bool): print the gap after each solve
        warm (dict): a solved steady state for nearby parameters to start
            the first solve from; OG-Core's cold start when None

    Returns:
        chi_n (Numpy array): calibrated disutility weights, length S
        target (Numpy array): target labor supply by age, length S
        history (list): one dict per solve with the chi_n used, the model
            labor supply, the largest gap and the solved r, TR and factor

    """
    p = copy.deepcopy(p)
    target = labor_supply_target(p.E, p.S, p.ltilde)
    ages = model_ages(p.E, p.S)
    fit = (ages >= FIT_AGES[0]) & (ages < FIT_AGES[1])
    chi_n = steady_state_chi_n(p)
    history = []
    ss = None
    prev = warm
    for iteration in range(max_iter):
        # each solve after the first starts from the last solved state: from
        # OG-Core's flat seeds the steady state does not solve once chi_n
        # has moved (ogphl/warm_start.py)
        if prev is None:
            ss = SS.run_SS(p, client=client)
        else:
            ss = warm_start.solve_ss_from(p, prev, client=client)
        prev = ss
        n_model = average_labor_supply(ss["n"], p.omega_SS)
        # ages where chi_n sits at OG-Core's cap cannot be fitted
        gap = np.abs(n_model / target - 1)[fit & (chi_n < MAX_CHI_N)].max()
        history.append(
            {
                "iteration": iteration,
                "chi_n": chi_n.copy(),
                "n_model": n_model,
                "max_gap": gap,
                "r": float(np.squeeze(ss["r"])),
                "TR": float(np.squeeze(ss["TR"])),
                "factor": float(np.squeeze(ss["factor"])),
            }
        )
        if verbose:
            print(
                f"chi_n iteration {iteration}: largest relative gap "
                f"{gap:.3f}, r {history[-1]['r']:.4f}, "
                f"factor {history[-1]['factor']:.0f}",
                flush=True,
            )
        if gap < tol:
            break
        chi_n = chi_n_step(chi_n, n_model, target, p, STEP_DAMPING)
        p.update_specifications({"chi_n": chi_n.tolist()})
    else:
        print(
            f"chi_n did not converge in {max_iter} solves; keeping the "
            "last solved profile"
        )
        chi_n = history[-1]["chi_n"]
    return chi_n, target, history


def fit_table(target, n_model, E, S):
    """
    Model and target labor supply averaged over age bands.

    Args:
        target (Numpy array): target labor supply by age, length S
        n_model (Numpy array): model labor supply by age, length S
        E (int): age at which agents become economically active
        S (int): number of model periods in a lifetime

    Returns:
        rows (list of tuple): age band, target and model labor supply as
            shares of the time endowment and as weekly hours per person

    """
    ages = model_ages(E, S)
    bands = [(20, 25), (25, 30), (30, 35), (35, 40), (40, 45), (45, 50)]
    bands += [(50, 55), (55, 60), (60, 65), (65, 70), (70, 80), (80, 100)]
    rows = []
    for lo, hi in bands:
        sel = (ages >= lo) & (ages < hi)
        t, m = target[sel].mean(), n_model[sel].mean()
        rows.append(
            (
                f"{lo}-{hi - 1}",
                t,
                m,
                t * WEEKLY_TIME_ENDOWMENT,
                m * WEEKLY_TIME_ENDOWMENT,
            )
        )
    return rows


def main():
    """
    Calibrate chi_n on the packaged parameters and write it back into the
    packaged JSON.
    """
    import argparse
    import multiprocessing

    from distributed import Client
    from ogcore.parameters import Specifications
    from ogcore.utils import safe_read_pickle

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--warm", default=None, help="SS_vars.pkl to start the first solve"
    )
    args = ap.parse_args()

    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    p = Specifications(baseline=True, num_workers=num_workers)
    with open(JSON_PATH, encoding="utf-8") as f:
        p.update_specifications(json.load(f))
    warm = safe_read_pickle(args.warm) if args.warm else None
    chi_n, target, history = estimate_chi_n(p, client=client, warm=warm)
    client.close()
    last = history[-1]
    print(f"{'ages':8s} {'target':>7s} {'model':>7s} {'hours':>6s} {'':>6s}")
    for band, t, m, th, mh in fit_table(target, last["n_model"], p.E, p.S):
        print(f"{band:8s} {t:7.3f} {m:7.3f} {th:6.1f} {mh:6.1f}")
    with open(JSON_PATH, encoding="utf-8") as f:
        params = json.load(f)
    params["chi_n"] = [round(float(v), 4) for v in chi_n]
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=4)
        f.write("\n")
    print(f"wrote chi_n to {JSON_PATH}")


if __name__ == "__main__":
    main()
