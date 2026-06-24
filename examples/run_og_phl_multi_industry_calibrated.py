"""
Run a SAM-calibrated multi-industry (M=8, I=5) version of OG-PHL.

Unlike ``run_og_phl_multi_industry.py`` (a hand-coded 2-sector informal/formal
demo), this example builds the multi-industry parameters from the packaged 2018
IFPRI Social Accounting Matrix:

  * ``alpha_c``   - household consumption shares across the 5 consumption goods
  * ``io_matrix`` - 5x8 domestic value-added content of each consumption good
                    by industry (input-output / Leontief; see
                    input_output.get_io_matrix_value_added)
  * ``gamma``     - per-industry capital share of value added (from SAM factor
                    rows), the one production parameter the SAM identifies

The remaining production parameters are set to defensible, documented values
(matching the practice of the sibling country models OG-IDN/ETH/ZAF):

  * ``epsilon = 1``   - Cobb-Douglas; no Philippine substitution-elasticity
                        estimate exists, and this is the OG-Core default.
  * ``gamma_g = .05`` - public capital's output share, kept at the
                        single-industry OG-PHL value (the model already carries
                        a positive public capital stock, initial_Kg_ratio=0.2,
                        so the same infrastructure role applies to every
                        industry). Dropping it to zero forces all capital to be
                        privately/foreign funded and collapses domestic
                        consumption, so it is retained here.
  * ``Z = 1``         - sector TFP normalized to one. No published Philippine
                        industry-TFP levels exist; constructing relative Z_m is
                        a documented follow-on.
  * ``cit_rate = .25``- CREATE Act statutory corporate income tax, applied
                        uniformly (sector-effective rates are not published).
  * ``tau_c = .12``   - standard VAT, applied uniformly across goods.

The 8 industries (Manufacturing kept last as the OG-Core numeraire / sole
investment-good producer) are: Agriculture & Fishing, Mining, Electricity,
Water, Construction, Trade & Transport, Services, Manufacturing.

Solving the steady state directly fails to converge: OG-Core seeds the
industry-price guess at p_m = 1 for every industry, but with heterogeneous
capital shares the equilibrium relative prices are far from one, and the
built-in guess sweep only varies r and TR (never p_m). We therefore solve by
*continuation* (homotopy): first solve a flat-gamma economy (where p_m = 1 is
correct), then morph gamma toward the SAM values in steps, each step reusing
the previous step's solution as its starting guess.

Run steady state only (fast validation):

    uv run python examples/run_og_phl_multi_industry_calibrated.py

Run the full transition path off the converged steady state (slow):

    uv run python examples/run_og_phl_multi_industry_calibrated.py --tpi
"""

import os
import sys
import json
import time
import shutil
import importlib.resources
import multiprocessing
import numpy as np

from ogcore.parameters import Specifications
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle

from ogphl import input_output as io

CUR_DIR = os.path.dirname(os.path.realpath(__file__))

# Economy-wide capital share (the single-industry OG-PHL value, from the
# ILOSTAT labor share). The SAM's industry capital shares are rescaled to this
# value-added weighted average: their raw average (~0.62) is biased upward by
# self-employed mixed income booked as capital, and an aggregate that high has
# no steady state under these depreciation/openness parameters. Rescaling keeps
# the SAM's cross-industry *pattern* (Electricity/Mining capital-intensive,
# Agriculture/Services labor-intensive) while pinning the *level* to the
# economy-wide share. The continuation anchor is this same flat value, so only
# the dispersion of gamma changes along the path (the aggregate is constant),
# which is what makes the homotopy converge.
ECONOMY_WIDE_GAMMA = 0.53785
ANCHOR_GAMMA = ECONOMY_WIDE_GAMMA

# Public capital's output share, kept at the single-industry OG-PHL value.
PUBLIC_CAPITAL_SHARE = 0.05


def _load_defaults():
    with (
        importlib.resources.files("ogphl")
        .joinpath("ogphl_default_parameters.json")
        .open() as f
    ):
        return json.load(f)


def get_sam_calibration():
    """Return the SAM-derived (alpha_c, io_matrix, gamma, M, I).

    Capital shares are rescaled to a value-added weighted average of
    ECONOMY_WIDE_GAMMA; ``ogphl.input_output.get_gamma`` returns the raw SAM
    values when called without ``target_avg``.
    """
    alpha_c = np.array(list(io.get_alpha_c().values()))
    io_matrix = io.get_io_matrix_value_added().values
    gamma = np.array(
        list(io.get_gamma(target_avg=ECONOMY_WIDE_GAMMA).values())
    )
    n_cons, n_ind = io_matrix.shape
    return alpha_c, io_matrix, gamma, n_ind, n_cons


def build_specifications(gamma, baseline, output_base, baseline_dir=None):
    """
    Build a Specifications object overlaid with the SAM-calibrated
    multi-industry structure, using the supplied capital-share vector.
    """
    p = Specifications(
        baseline=baseline,
        num_workers=1,
        baseline_dir=baseline_dir or output_base,
        output_base=output_base,
    )
    p.update_specifications(_load_defaults())

    alpha_c, io_matrix, _, n_ind, n_cons = get_sam_calibration()
    p.update_specifications(
        {
            "M": n_ind,
            "I": n_cons,
            "alpha_c": alpha_c.tolist(),
            "io_matrix": io_matrix.tolist(),
            "c_min": [0.0] * n_cons,
            "gamma": list(gamma),
            "epsilon": [1.0] * n_ind,
            "gamma_g": [PUBLIC_CAPITAL_SHARE] * n_ind,
            "Z": [[1.0] * n_ind],
            "cit_rate": [[0.25]],
            "tau_c": [[0.12]],
        }
    )
    return p


def solve_ss_by_continuation(work_dir, dt0=0.125, dt_min=0.01):
    """
    Solve the heterogeneous-gamma steady state by adaptive continuation.

    A flat-gamma baseline is solved first (its equilibrium prices are all 1,
    matching OG-Core's guess). Then gamma is walked toward the SAM values: each
    step solves as a reform reusing the previous step's steady state, the step
    size grows after a success and halves after a failure. Adaptive stepping is
    needed because the capital-intensive sectors (Mining, Electricity ~0.88)
    move the relative prices enough that a fixed step overshoots.

    Returns:
        (ss, p, out_dir): the final steady-state dict, its parameters, and dir
    """
    _, _, gamma_target, M, _ = get_sam_calibration()
    anchor = np.full(M, ANCHOR_GAMMA)
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

    # Flat-gamma baseline.
    base_dir = os.path.join(work_dir, "anchor")
    os.makedirs(os.path.join(base_dir, "SS"), exist_ok=True)
    p = build_specifications(anchor, baseline=True, output_base=base_dir)
    print("  solving flat-gamma anchor economy ...", flush=True)
    t0 = time.time()
    runner(p, time_path=False, client=None)
    print(f"    anchor solved in {time.time() - t0:.1f}s", flush=True)

    good_dir, good_p = base_dir, p
    t, dt, idx = 0.0, dt0, 0
    while t < 1.0 - 1e-9:
        t_try = min(t + dt, 1.0)
        gamma = (1 - t_try) * anchor + t_try * gamma_target
        idx += 1
        out_dir = os.path.join(work_dir, f"t{idx}")
        os.makedirs(os.path.join(out_dir, "SS"), exist_ok=True)
        p = build_specifications(
            gamma, baseline=False, output_base=out_dir, baseline_dir=good_dir
        )
        t0 = time.time()
        try:
            runner(p, time_path=False, client=None)
            t, good_dir, good_p = t_try, out_dir, p
            print(
                f"  step to t={t:.3f} (dt={dt:.3f}) solved in "
                f"{time.time() - t0:.1f}s",
                flush=True,
            )
            dt = min(dt * 1.5, 0.25)
        except Exception:
            dt /= 2.0
            print(
                f"  step to t={t_try:.3f} failed; reducing dt -> {dt:.4f}",
                flush=True,
            )
            if dt < dt_min:
                raise RuntimeError(
                    f"continuation stalled at t={t:.3f} (dt below {dt_min})"
                )

    ss = safe_read_pickle(os.path.join(good_dir, "SS", "SS_vars.pkl"))
    return ss, good_p, good_dir


def validate_ss(p, ss):
    """Print and sanity-check key steady-state results."""
    s = lambda x: float(np.squeeze(x))  # noqa: E731  SS scalars are 0-d arrays
    industries = list(io.get_gamma().keys())
    Y_m = np.atleast_1d(np.squeeze(ss["Y_m"]))
    K_m = np.atleast_1d(np.squeeze(ss["K_m"]))
    L_m = np.atleast_1d(np.squeeze(ss["L_m"]))
    p_m = np.atleast_1d(np.squeeze(ss["p_m"]))
    Y, K, C = s(ss["Y"]), s(ss["K"]), s(ss["C"])
    print("\n================ STEADY-STATE VALIDATION ================")
    print(f"Aggregate Y = {Y:.4f}   K = {K:.4f}   L = {s(ss['L']):.4f}")
    print(
        f"K/Y = {K / Y:.3f}   C/Y = {C / Y:.3f}   r = {s(ss['r']):.4f}   "
        f"w = {s(ss['w']):.4f}"
    )
    print(f"K_f/K (foreign-owned capital share) = {s(ss['K_f']) / K:.3f}")
    print(
        "(single-industry baseline reference: K/Y 5.33, C/Y 0.35, "
        "r 0.048, K_f/K 0.81)"
    )
    print("\nPer-industry steady state:")
    print(
        f"{'industry':24s}{'gamma':>8s}{'p_m':>9s}{'Y_m':>11s}{'Y share':>9s}"
    )
    nominal = p_m * Y_m
    Yshare = nominal / nominal.sum()
    for i, name in enumerate(industries):
        print(
            f"{name:24s}{p.gamma[i]:8.3f}{p_m[i]:9.3f}"
            f"{Y_m[i]:11.4f}{Yshare[i]:9.1%}"
        )

    # Structural checks: the steady state exists and is internally consistent.
    # (C/Y and K_f/K levels are governed by the multi-good consumption mapping
    # and the open-economy zeta_K, not by these checks.)
    checks = {
        "all Y_m > 0": bool((Y_m > 0).all()),
        "all K_m > 0": bool((K_m > 0).all()),
        "all L_m > 0": bool((L_m > 0).all()),
        "all p_m > 0": bool((p_m > 0).all()),
        "numeraire p_m[-1] == 1": bool(np.isclose(p_m[-1], 1.0)),
        "r in (0, 0.2)": bool(0.0 < s(ss["r"]) < 0.2),
        "K/Y in (1, 8)": bool(1.0 < K / Y < 8.0),
        "Y shares sum to 1": bool(np.isclose(Yshare.sum(), 1.0)),
    }
    print("\nChecks:")
    all_ok = True
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        all_ok = all_ok and ok
    print("=========================================================")
    return all_ok


def main(time_path=False):
    save_dir = os.path.join(CUR_DIR, "OG-PHL-MultiIndustry")
    work_dir = os.path.join(save_dir, "continuation")

    _, _, gamma, n_ind, n_goods = get_sam_calibration()
    print(f"M = {n_ind} industries, I = {n_goods} consumption goods")
    print(f"SAM-derived gamma (capital share) = {np.round(gamma, 4)}")

    start = time.time()
    ss, p, final_dir = solve_ss_by_continuation(work_dir)
    print(f"\nTotal SS continuation time = {time.time() - start:.1f}s")
    ok = validate_ss(p, ss)

    if time_path:
        # Solve the transition path off the converged multi-industry SS.
        from distributed import Client

        num_workers = min(multiprocessing.cpu_count(), 7)
        client = Client(n_workers=num_workers, threads_per_worker=1)
        start = time.time()
        runner(p, time_path=True, client=client)
        print(f"SS + TPI run time = {time.time() - start:.1f}s")
        client.close()

    if not time_path:
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main(time_path="--tpi" in sys.argv)
