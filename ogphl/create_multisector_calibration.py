"""
Build the OG-PHL multi-industry (M=8, I=5) calibration overlay and write it
to the packaged ``ogphl_multisector_default_parameters.json``.

Calibration is a rare event. Run this ONLY to (re)generate the packaged
multi-industry parameter file from the underlying data (the 2018 IFPRI SAM
and the PSA Labor Force Survey):

    uv run python -m ogphl.create_multisector_calibration

The model itself loads the JSON; it does not call these functions at run time.
The construction tools live in ``ogphl.input_output`` (``get_alpha_c``,
``get_io_matrix_value_added``, ``get_gamma``, ``get_Z``, ``get_employment``);
this module assembles their output, with the documented production choices,
into the multi-industry overlay and serializes it.

The file is an OVERLAY, not a full calibration: it contains only the
parameters the multi-industry calibration changes relative to the
single-industry base ``ogphl_default_parameters.json``. Loading it alone
would leave every omitted parameter at OG-Core's (US-calibrated) defaults,
so it must always be applied ON TOP of the base:

    p = Specifications(...)
    p.update_specifications(<ogphl_default_parameters.json>)
    p.update_specifications(<ogphl_multisector_default_parameters.json>)

as ``examples/run_og_phl_multi_industry_calibrated.py`` (the canonical
loader) does. Everything economy-wide -- demographics, the earnings matrix,
tax functions, the fiscal and open-economy blocks, the solver seeds -- is
inherited from the base at load time, so a base recalibration flows into the
multi-industry model automatically, with nothing to regenerate.

The overlay contains:
  * ``M``, ``I``   - 8 production industries, 5 consumption goods
  * ``alpha_c``    - household consumption shares (SAM)
  * ``io_matrix``  - 5x8 domestic value-added content (SAM, Leontief)
  * ``c_min``      - 0.0 per consumption good (no subsistence floor)
  * ``gamma``      - per-industry private capital share: the SAM's total
                     capital shares rescaled to TOTAL_CAPITAL_SHARE, then
                     PUBLIC_CAPITAL_SHARE carved out (from capital, not labor)
  * ``epsilon``    - 1.0 per industry (Cobb-Douglas; OG-Core default)
  * ``gamma_g``    - PUBLIC_CAPITAL_SHARE for every industry
  * ``Z``          - per-industry TFP, the Solow residual (see get_Z)
  * ``chi_b``, ``chi_n`` - the base utility weights converted for the
                     multi-good composite-consumption units: scaled by
                     k**(sigma-1) with k = prod(alpha_c**-alpha_c), the units
                     constant OG-Core's unnormalized composite price index
                     picks up when I > 1 (see build_multisector_params).
                     These ARE multi-industry changes even though they look
                     like base preference parameters -- the conversion is
                     derived from alpha_c, so it belongs to the overlay.
  * ``nu``         - 0.2 dampening (0.4 is marginally unstable here)
  * ``TPI_outer_method`` - "anderson", the anchored Anderson accelerator
                     for the TPI outer loop (ogcore >= 0.16.4)

Deliberately NOT in the overlay: parameters the multi-industry calibration
leaves unchanged (e.g. ``cit_rate``, ``tau_c`` -- the CREATE Act 25% CIT and
the 12% VAT apply uniformly and equal the base values).
"""

import json
import os

import numpy as np

from ogphl import input_output as io
from ogphl.constants import PUBLIC_CAPITAL_SHARE, TOTAL_CAPITAL_SHARE

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
MULTISECTOR_PARAMS_PATH = os.path.join(
    CUR_DIR, "ogphl_multisector_default_parameters.json"
)

# The default 0.4 sits on the marginal-stability boundary for this
# calibration (the price update locks into a constant-amplitude period-2
# cycle); 0.2 puts the iteration comfortably inside the unit circle.
NU = 0.2

# Anderson acceleration for the TPI outer loop. It extrapolates the damped
# nu-step from the residual history, so it needs the calibrated NU above:
# with nu = 0.2 the baseline transition converges in 25 outer iterations;
# at nu = 0.4 the accelerator spends the run in trust-region resets (70
# iterations on the baseline) and the reform transition stalls outright.
TPI_OUTER_METHOD = "anderson"


def build_multisector_params():
    """Compute the multi-industry parameter overlay from the packaged data.

    Returns:
        params (dict): an OG-Core ``update_specifications``-format overlay.
    """
    alpha_c = [float(v) for v in io.get_alpha_c().values()]
    io_df = io.get_io_matrix_value_added()
    n_cons, n_ind = io_df.shape
    # Per-industry capital shares: rescale the SAM's total shares to the
    # economy-wide total, then subtract public capital's share to leave the
    # private capital share gamma_m used in the production function.
    gamma_total = io.get_gamma(target_avg=TOTAL_CAPITAL_SHARE)
    gamma = {k: v - PUBLIC_CAPITAL_SHARE for k, v in gamma_total.items()}
    Z = io.get_Z(gamma=gamma, gamma_g=PUBLIC_CAPITAL_SHARE)
    # OG-Core's composite-consumption price index is unnormalized
    # (p_tilde = prod(((1+tau_c) p_i / alpha_i)**alpha_i) in
    # aggregates.get_ptilde), so I=1 -> I=5 shrinks composite-consumption
    # units by
    # k = prod(alpha_i**-alpha_i) while chi_n and chi_b stay fixed numbers set
    # in the single-industry units. Every consumption term in the household
    # FOCs enters as MU(c)/p_tilde and scales by k**(sigma-1) under that units
    # change; the chi_b bequest term (assets, numeraire units) and the chi_n
    # disutility term do not. Scaling both weights by k**(sigma-1) restores
    # the FOCs at the same real allocation, keeping multi-industry households
    # behaviorally identical to the single-industry baseline.
    alpha_arr = np.array(alpha_c)
    k_units = float(np.prod(alpha_arr**-alpha_arr))
    with open(os.path.join(CUR_DIR, "ogphl_default_parameters.json")) as f:
        base = json.load(f)
    chi_scale = k_units ** (base["sigma"] - 1.0)
    chi_b = [float(v) * chi_scale for v in base["chi_b"]]
    chi_n = [float(v) * chi_scale for v in base["chi_n"]]
    return {
        "M": int(n_ind),
        "I": int(n_cons),
        "alpha_c": alpha_c,
        "io_matrix": io_df.values.tolist(),
        "c_min": [0.0] * n_cons,
        "gamma": [float(v) for v in gamma.values()],
        "epsilon": [1.0] * n_ind,
        "gamma_g": [PUBLIC_CAPITAL_SHARE] * n_ind,
        "Z": [[float(v) for v in Z.values()]],
        "chi_b": chi_b,
        "chi_n": chi_n,
        "nu": NU,
        "TPI_outer_method": TPI_OUTER_METHOD,
    }


def main():
    params = build_multisector_params()
    with open(MULTISECTOR_PARAMS_PATH, "w") as f:
        json.dump(params, f, indent=2)
        f.write("\n")
    print(
        f"Wrote {MULTISECTOR_PARAMS_PATH} "
        f"(multi-industry overlay, {len(params)} parameters)"
    )
    print(f"  M = {params['M']}, I = {params['I']}")
    print(f"  gamma = {np.round(params['gamma'], 4).tolist()}")
    print(f"  Z     = {np.round(params['Z'][0], 4).tolist()}")
    return params


if __name__ == "__main__":
    main()
