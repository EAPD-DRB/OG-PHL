"""
Run a SAM-calibrated multi-industry (M=8, I=5) version of OG-PHL.

Unlike ``run_og_phl_multi_industry.py`` (a hand-coded 2-sector informal/formal
demo), this example loads the packaged multi-industry calibration overlay
``ogphl_multisector_default_parameters.json`` -- generated (rarely) by
``ogphl.create_multisector_calibration`` from the 2018 IFPRI SAM and the PSA
Labor Force Survey -- and solves its steady state. The overlay contains:

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

The 8 industries (Manufacturing kept last as the OG-Core numeraire / sole
investment-good producer) are: Agriculture & Fishing, Mining, Electricity,
Water, Construction, Trade & Transport, Services, Manufacturing.

Interpreting the steady state (these are structural OG-Core open-economy
features, not Z artifacts -- a Z=1 control reproduces them):
  * Manufacturing's NOMINAL output share (~72%) is mechanically inflated:
    OG-Core routes all non-consumption final demand (investment, government,
    net capital outflows) through the single numeraire industry. It is not
    comparable to its ~19% value-added share in the data; the value-added /
    consumption composition is the data-comparable object.
  * The foreign-owned capital share (K_f/K ~0.96) follows from the
    open-economy parameters (zeta_K=0.9, world_int_rate < domestic r), a
    modeling choice separate from the TFP calibration.
  * C/Y is reported at purchaser prices (p_tilde * C / Y, ~0.37).

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

from ogphl.constants import PROD_DICT

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


def _load_defaults():
    return _load_params("ogphl_default_parameters.json")


def _load_multisector():
    """Load the packaged multi-industry calibration overlay.

    Built by ``ogphl.create_multisector_calibration`` (a rare event); the model
    run only reads it. Returns the OG-Core ``update_specifications`` overlay
    dict with M, I, alpha_c, io_matrix, gamma, epsilon, gamma_g, Z, c_min,
    cit_rate, tau_c.
    """
    return _load_params("ogphl_multisector_default_parameters.json")


def build_specifications(gamma, Z, baseline, output_base, baseline_dir=None):
    """
    Build a Specifications object from the packaged single-industry defaults,
    the packaged multi-industry overlay, and the supplied gamma and Z (which
    the continuation morphs toward the calibrated values). Only gamma and Z
    vary along the homotopy; M, I, io_matrix, alpha_c, gamma_g, epsilon,
    cit_rate and tau_c come from the calibration JSON.
    """
    p = Specifications(
        baseline=baseline,
        num_workers=1,
        baseline_dir=baseline_dir or output_base,
        output_base=output_base,
    )
    p.update_specifications(_load_defaults())
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
        "(single-industry baseline reference: K/Y 5.33, C/Y 0.35, "
        "r 0.048, K_f/K 0.81)"
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


def main(time_path=False):
    save_dir = os.path.join(CUR_DIR, "OG-PHL-MultiIndustry")
    work_dir = os.path.join(save_dir, "continuation")

    ms = _load_multisector()
    print(f"M = {ms['M']} industries, I = {ms['I']} consumption goods")
    print(f"calibrated gamma (capital share) = {np.round(ms['gamma'], 4)}")
    print(f"calibrated sector TFP Z_m (Mfg=1) = {np.round(ms['Z'][0], 4)}")

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
