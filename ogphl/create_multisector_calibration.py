"""
Build the OG-PHL multi-industry (M=8, I=5) calibration and write it to the
packaged ``ogphl_multisector_default_parameters.json``.

Calibration is a rare event. Run this ONLY to (re)generate the packaged,
self-sufficient multi-industry parameter file from the underlying data (the
2018 IFPRI SAM and the PSA Labor Force Survey):

    uv run python -m ogphl.create_multisector_calibration

The model itself loads the JSON; it does not call these functions at run time.
The construction tools live in ``ogphl.input_output`` (``get_alpha_c``,
``get_io_matrix_value_added``, ``get_gamma``, ``get_Z``, ``get_employment``);
this module assembles their output, with the documented production/fiscal
choices, into the multi-industry values, merges them onto the single-industry
base, and serializes the self-sufficient result.

Multi-industry values computed here and merged onto the single-industry base
``ogphl_default_parameters.json`` to form the self-sufficient file:
  * ``M``, ``I``   - 8 production industries, 5 consumption goods
  * ``alpha_c``    - household consumption shares (SAM)
  * ``io_matrix``  - 5x8 domestic value-added content (SAM, Leontief)
  * ``gamma``      - per-industry private capital share: the SAM's total
                     capital shares rescaled to TOTAL_CAPITAL_SHARE, then
                     PUBLIC_CAPITAL_SHARE carved out (from capital, not labor)
  * ``Z``          - per-industry TFP, the Solow residual (see get_Z)
  * ``epsilon``    - 1.0 (Cobb-Douglas; OG-Core default)
  * ``gamma_g``    - PUBLIC_CAPITAL_SHARE for every industry
  * ``c_min``      - 0.0 (no subsistence floor)
  * ``cit_rate``   - 0.25 (CREATE Act statutory corporate income tax)
  * ``tau_c``      - 0.12 (standard VAT)
  * ``chi_b``, ``chi_n`` - the base utility weights converted for the
                     multi-good composite-consumption units: scaled by
                     k**(sigma-1) with k = prod(alpha_c**-alpha_c), the units
                     constant OG-Core's unnormalized composite price index
                     picks up when I > 1 (see build_multisector_params)
  * ``nu``         - 0.2 TPI dampening (0.4 is marginally unstable here)

The economy-wide open-economy values (``zeta_K`` = 0.4,
``world_int_rate_annual`` = 0.05, ``debt_ratio_ss`` = 0.6) are not
multi-industry choices -- they are inherited unchanged from the
single-industry base ``ogphl_default_parameters.json`` (and documented in the
macro calibration chapter) because they describe the Philippine economy
regardless of the industry split. The merge below bakes them into the
self-sufficient file.
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

# TPI dampening. The default 0.4 sits on the marginal-stability boundary
# for this calibration (the price update locks into a constant-amplitude
# period-2 cycle); 0.2 puts the iteration comfortably inside the unit circle.
TPI_NU = 0.2


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
        "cit_rate": [[0.25]],
        "tau_c": [[0.12]],
        "chi_b": chi_b,
        "chi_n": chi_n,
        "nu": TPI_NU,
    }


def build_calibration():
    """Full, self-sufficient multi-industry parameter set.

    The single-industry base ``ogphl_default_parameters.json`` with the
    multi-industry values (``build_multisector_params``) applied on top. The
    model loads this one file and does not depend on the single-industry base
    at run time.
    """
    with open(os.path.join(CUR_DIR, "ogphl_default_parameters.json")) as f:
        params = json.load(f)
    params.update(build_multisector_params())
    return params


def main():
    params = build_calibration()
    with open(MULTISECTOR_PARAMS_PATH, "w") as f:
        json.dump(params, f, indent=2)
        f.write("\n")
    print(
        f"Wrote {MULTISECTOR_PARAMS_PATH} "
        f"(self-sufficient, {len(params)} parameters)"
    )
    print(f"  M = {params['M']}, I = {params['I']}")
    print(f"  gamma = {np.round(params['gamma'], 4).tolist()}")
    print(f"  Z     = {np.round(params['Z'][0], 4).tolist()}")
    return params


if __name__ == "__main__":
    main()
