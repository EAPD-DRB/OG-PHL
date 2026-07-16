"""
Run a SAM-calibrated multi-industry (M=8, I=5) version of OG-PHL.

Unlike ``run_og_phl_multi_industry.py`` (a hand-coded 2-sector informal/formal
demo), this example loads the packaged, self-sufficient multi-industry
calibration ``ogphl_multisector_default_parameters.json`` -- generated (rarely)
by ``ogphl.create_multisector_calibration`` from the 2018 IFPRI SAM and the PSA
Labor Force Survey -- and runs a full baseline plus a trivial reform scenario
(a corporate-income-tax cut), comparing them as the other examples do. It is a
full OG-Core parameter set (the single-industry base with the multi-industry
values applied), so the run depends on no other parameter file. The calibration
contains:

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
  * ``Z``             - per-industry TFP, the Solow residual of OG-Core's
                        production technology with public capital,
                        Y_m / (K_m**gamma_m * K_g**gamma_g
                        * L_m**(1-gamma_m-gamma_g)); the common K_g term
                        cancels under the numeraire normalization.
                        Employment from the PSA Labor Force Survey; capital
                        allocated by capital-income share (national level
                        from the Penn World Table K/Y); normalized so
                        Manufacturing = 1. See input_output.get_Z.
  * ``cit_rate = .25``- CREATE Act statutory corporate income tax, applied
                        uniformly (sector-effective rates are not published).
  * ``tau_c = .12``   - standard VAT, applied uniformly across goods.
  * ``chi_b``/``chi_n`` - the base utility weights converted for the
                        multi-good composite-consumption units. OG-Core's
                        composite price index is unnormalized, so I=5 shrinks
                        composite-consumption units by
                        k = prod(alpha_c**-alpha_c) ~ 2.97 while the weights
                        are fixed numbers set in single-industry units;
                        scaling both by k**(sigma-1) ~ 1.72 is the exact
                        FOC-preserving conversion and keeps household saving
                        and labor supply aligned with the single-industry
                        baseline (see create_multisector_calibration).

The 8 industries (Manufacturing kept last as the OG-Core numeraire / sole
investment-good producer) are: Agriculture & Fishing, Mining, Electricity,
Water, Construction, Trade & Transport, Services, Manufacturing.

Interpreting the steady state (these are structural OG-Core open-economy
features, not Z artifacts -- a Z=1 control reproduces them):
  * Manufacturing's NOMINAL output share (~65%) is mechanically inflated:
    OG-Core routes all non-consumption final demand (investment, government,
    net capital outflows) through the single numeraire industry. It is not
    comparable to its ~19% value-added share in the data; the value-added /
    consumption composition is the data-comparable object.
  * The foreign-owned capital share (K_f/K ~0.34, vs 0.26 in the
    single-industry baseline) follows from the open-economy parameters
    (zeta_K=0.4, world_int_rate < domestic r) plus a residual composition
    effect of the multi-good consumption basket, a modeling structure
    separate from the TFP calibration.
  * C/Y is reported at purchaser prices (p_tilde * C / Y, ~0.50).

Solving the steady state directly fails to converge: OG-Core seeds the
industry-price guess at p_m = 1 for every industry, but with heterogeneous
capital shares the equilibrium relative prices are far from one, and the
built-in guess sweep only varies r and TR (never p_m). We therefore solve by
*continuation* (homotopy): first solve a flat-gamma economy (where p_m = 1 is
correct), then morph gamma toward the SAM values in steps, each step reusing
the previous step's solution as its starting guess.

The calibrated steady state cannot be re-solved from a cold start, so the
baseline transition path reuses the continuation's converged SS (see
run_baseline_tpi); the reform re-solves its SS warm-started off the baseline,
which converges because it is only a small policy perturbation.

Run the full baseline + reform comparison (default; SS continuation, then both
transition paths -- slow, tens of minutes):

    uv run python examples/run_og_phl_multi_industry_calibrated.py

Quick steady-state-only check (continuation + validation, no transition path):

    uv run python examples/run_og_phl_multi_industry_calibrated.py --ss-only
"""

import os
import sys
import json
import time
import shutil
import pickle
import importlib.resources
import multiprocessing

import cloudpickle
import numpy as np
import matplotlib.pyplot as plt
from distributed import Client

from ogcore.parameters import Specifications
from ogcore.execute import runner
from ogcore import TPI
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.utils import safe_read_pickle

from ogphl.constants import PROD_DICT

# Use a custom matplotlib style file for plots (matches the other examples)
plt.style.use("ogcore.OGcorePlots")

CUR_DIR = os.path.dirname(os.path.realpath(__file__))

# Flat capital share used as the continuation anchor (a solver device, not a
# calibrated value). It equals the value-added weighted mean that the packaged
# gamma was rescaled to, so morphing from this anchor to the calibrated gamma
# holds the aggregate constant and only varies the cross-industry dispersion --
# which is what makes the homotopy converge.
ANCHOR_GAMMA = 0.53785


def _load_params(name):
    with importlib.resources.files("ogphl").joinpath(name).open() as f:
        return json.load(f)


def _load_multisector():
    """Load the packaged, self-sufficient multi-industry calibration.

    Built by ``ogphl.create_multisector_calibration`` (a rare event); the
    model run only reads it. It is a full OG-Core parameter set -- the
    single-industry base with the multi-industry values applied -- so the run
    loads this one file alone (no dependency on the single-industry JSON).
    """
    return _load_params("ogphl_multisector_default_parameters.json")


def build_specifications(gamma, Z, baseline, output_base, baseline_dir=None):
    """
    Build a Specifications object from the packaged, self-sufficient
    multi-industry calibration JSON and the supplied gamma and Z (which the
    continuation morphs toward the calibrated values). Only gamma and Z vary
    along the homotopy; M, I, io_matrix, alpha_c, gamma_g, epsilon, cit_rate
    and tau_c come from the calibration JSON.
    """
    p = Specifications(
        baseline=baseline,
        num_workers=1,
        baseline_dir=baseline_dir or output_base,
        output_base=output_base,
    )
    p.update_specifications(_load_multisector())
    p.update_specifications({"gamma": list(gamma), "Z": [list(Z)]})
    return p


def solve_ss_by_continuation(work_dir, dt0=0.125, dt_min=0.01):
    """
    Solve the heterogeneous-gamma, heterogeneous-Z steady state by adaptive
    continuation.

    A homogeneous baseline (flat gamma and Z = 1) is solved first: its
    equilibrium prices are all 1, matching OG-Core's guess. Then gamma and the
    sector TFP Z are walked together toward their calibrated values; each step
    solves as a reform reusing the previous step's steady state, the step size
    grows after a success and halves after a failure. Adaptive stepping is
    needed because the capital-intensive sectors (Mining, Electricity ~0.88)
    and the TFP dispersion move the relative prices enough that a fixed step
    overshoots.

    Returns:
        (ss, p, out_dir): the final steady-state dict, its parameters, and dir
    """
    ms = _load_multisector()
    gamma_target = np.array(ms["gamma"])
    Z_target = np.array(ms["Z"][0])
    M = ms["M"]
    anchor = np.full(M, ANCHOR_GAMMA)
    Z_anchor = np.ones(M)
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

    # Homogeneous baseline: flat gamma and Z = 1 (equilibrium prices all 1).
    base_dir = os.path.join(work_dir, "anchor")
    os.makedirs(os.path.join(base_dir, "SS"), exist_ok=True)
    p = build_specifications(
        anchor, Z_anchor, baseline=True, output_base=base_dir
    )
    print("  solving homogeneous anchor economy ...", flush=True)
    t0 = time.time()
    runner(p, time_path=False, client=None)
    print(f"    anchor solved in {time.time() - t0:.1f}s", flush=True)

    good_dir, good_p = base_dir, p
    t, dt, idx = 0.0, dt0, 0
    while t < 1.0 - 1e-9:
        t_try = min(t + dt, 1.0)
        gamma = (1 - t_try) * anchor + t_try * gamma_target
        Z = (1 - t_try) * Z_anchor + t_try * Z_target
        idx += 1
        out_dir = os.path.join(work_dir, f"t{idx}")
        os.makedirs(os.path.join(out_dir, "SS"), exist_ok=True)
        p = build_specifications(
            gamma,
            Z,
            baseline=False,
            output_base=out_dir,
            baseline_dir=good_dir,
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
    industries = list(PROD_DICT.keys())
    Y_m = np.atleast_1d(np.squeeze(ss["Y_m"]))
    K_m = np.atleast_1d(np.squeeze(ss["K_m"]))
    L_m = np.atleast_1d(np.squeeze(ss["L_m"]))
    p_m = np.atleast_1d(np.squeeze(ss["p_m"]))
    Y, K, C = s(ss["Y"]), s(ss["K"]), s(ss["C"])
    # ss["C"] is composite consumption (in consumption-good units, price
    # p_tilde); Y is nominal output at producer prices (numeraire p_m[-1]=1).
    # Value C at p_tilde before dividing -- else C/Y is understated by the
    # factor p_tilde (~5.5 here), a units artifact, not a collapse of C.
    p_tilde = float(np.squeeze(ss.get("p_tilde", 1.0)))
    C_share = p_tilde * C / Y
    print("\n================ STEADY-STATE VALIDATION ================")
    print(f"Aggregate Y = {Y:.4f}   K = {K:.4f}   L = {s(ss['L']):.4f}")
    print(
        f"K/Y = {K / Y:.3f}   C/Y = {C_share:.3f}   r = {s(ss['r']):.4f}   "
        f"w = {s(ss['w']):.4f}"
    )
    print(f"K_f/K (foreign-owned capital share) = {s(ss['K_f']) / K:.3f}")
    print(
        "(single-industry baseline reference: K/Y 4.29, C/Y 0.51, "
        "r 0.0708, K_f/K 0.26)"
    )
    print("\nPer-industry steady state:")
    print(
        f"{'industry':24s}{'gamma':>8s}{'Z':>7s}{'p_m':>9s}"
        f"{'Y_m':>11s}{'Y share':>9s}"
    )
    nominal = p_m * Y_m
    Yshare = nominal / nominal.sum()
    Z_m = np.atleast_1d(np.squeeze(p.Z[-1]))
    for i, name in enumerate(industries):
        print(
            f"{name:24s}{p.gamma[i]:8.3f}{Z_m[i]:7.3f}{p_m[i]:9.3f}"
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


# Trivial reform scenario: cut the corporate income tax from 25% to 20%.
REFORM_PARAMS = {"cit_rate": [[0.20]]}


def run_baseline_tpi(p_base, ss_source_dir, client):
    """Run the baseline transition path, reusing the continuation's SS.

    The calibrated steady state cannot be re-solved from a cold start (OG-Core
    seeds industry prices at p_m = 1 and only the continuation warm-starts
    them), so rather than call ``runner`` -- which would re-solve the SS and
    diverge -- we place the continuation's converged SS as the baseline SS and
    run only the TPI off it. This mirrors what ``runner`` writes to disk.
    """
    ss_dir = os.path.join(p_base.output_base, "SS")
    os.makedirs(ss_dir, exist_ok=True)
    shutil.copyfile(
        os.path.join(ss_source_dir, "SS", "SS_vars.pkl"),
        os.path.join(ss_dir, "SS_vars.pkl"),
    )
    with open(os.path.join(p_base.output_base, "model_params.pkl"), "wb") as f:
        cloudpickle.dump(p_base, f)
    tpi_output = TPI.run_TPI(p_base, client=client)
    tpi_dir = os.path.join(p_base.output_base, "TPI")
    os.makedirs(tpi_dir, exist_ok=True)
    with open(os.path.join(tpi_dir, "TPI_vars.pkl"), "wb") as f:
        pickle.dump(tpi_output, f)


def main(time_path=True):
    save_dir = os.path.join(CUR_DIR, "OG-PHL-MultiIndustry")
    work_dir = os.path.join(save_dir, "continuation")
    base_dir = os.path.join(save_dir, "OUTPUT_BASELINE")
    reform_dir = os.path.join(save_dir, "OUTPUT_REFORM")

    ms = _load_multisector()
    gamma = np.array(ms["gamma"])
    Z = np.array(ms["Z"][0])
    print(f"M = {ms['M']} industries, I = {ms['I']} consumption goods")
    print(f"calibrated gamma (capital share) = {np.round(gamma, 4)}")
    print(f"calibrated sector TFP Z_m (Mfg=1) = {np.round(Z, 4)}")

    # Solve the calibrated baseline SS by continuation; then validate.
    start = time.time()
    ss, _, good_dir = solve_ss_by_continuation(work_dir)
    print(f"\nTotal SS continuation time = {time.time() - start:.1f}s")
    p_base = build_specifications(
        gamma, Z, baseline=True, output_base=base_dir
    )
    ok = validate_ss(p_base, ss)

    # --ss-only stops here (fast check of the calibrated steady state).
    if not time_path:
        sys.exit(0 if ok else 1)

    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    try:
        # Baseline: reuse the converged SS, solve its transition path.
        start = time.time()
        run_baseline_tpi(p_base, good_dir, client)
        print(f"Baseline TPI run time = {time.time() - start:.1f}s")

        # Reform (trivial scenario): a small CIT cut, warm-started off the
        # baseline SS, so its SS re-solve converges without continuation.
        p_reform = build_specifications(
            gamma,
            Z,
            baseline=False,
            output_base=reform_dir,
            baseline_dir=base_dir,
        )
        p_reform.update_specifications(REFORM_PARAMS)
        start = time.time()
        runner(p_reform, time_path=True, client=client)
        print(f"Reform SS+TPI run time = {time.time() - start:.1f}s")
    finally:
        client.close()

    # Compare the baseline and reform transition paths (as in the other
    # examples), then plot and save.
    base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    reform_tpi = safe_read_pickle(
        os.path.join(reform_dir, "TPI", "TPI_vars.pkl")
    )
    reform_params = safe_read_pickle(
        os.path.join(reform_dir, "model_params.pkl")
    )
    ans = ot.macro_table(
        base_tpi,
        base_params,
        reform_tpi=reform_tpi,
        reform_params=reform_params,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params.start_year,
    )
    op.plot_all(base_dir, reform_dir, os.path.join(save_dir, "plots"))
    print("\nPercentage changes, reform vs baseline (first 10 years):")
    print(ans)
    ans.to_csv(os.path.join(save_dir, "OG-PHL_MultiIndustry_output.csv"))


if __name__ == "__main__":
    main(time_path="--ss-only" not in sys.argv)
