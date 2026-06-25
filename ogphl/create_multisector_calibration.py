"""
Build the OG-PHL multi-industry (M=8, I=5) calibration and write it to the
packaged ``ogphl_multisector_default_parameters.json``.

Calibration is a rare event. Run this ONLY to (re)generate the packaged
multi-industry parameter overlay from the underlying data (the 2018 IFPRI SAM
and the PSA Labor Force Survey):

    uv run python -m ogphl.create_multisector_calibration

The model itself loads the JSON; it does not call these functions at run time.
The construction tools live in ``ogphl.input_output`` (``get_alpha_c``,
``get_io_matrix_value_added``, ``get_gamma``, ``get_Z``, ``get_employment``);
this module just assembles their output, with the documented production/fiscal
choices, into an OG-Core parameter overlay and serializes it.

Values written (an overlay on top of ``ogphl_default_parameters.json``):
  * ``M``, ``I``   - 8 production industries, 5 consumption goods
  * ``alpha_c``    - household consumption shares (SAM)
  * ``io_matrix``  - 5x8 domestic value-added content (SAM, Leontief)
  * ``gamma``      - per-industry capital share (SAM), rescaled to the
                     value-added weighted mean ECONOMY_WIDE_GAMMA
  * ``Z``          - per-industry TFP, the Solow residual (see get_Z)
  * ``epsilon``    - 1.0 (Cobb-Douglas; OG-Core default)
  * ``gamma_g``    - PUBLIC_CAPITAL_SHARE for every industry
  * ``c_min``      - 0.0 (no subsistence floor)
  * ``cit_rate``   - 0.25 (CREATE Act statutory corporate income tax)
  * ``tau_c``      - 0.12 (standard VAT)
  * ``zeta_K``     - 0.4 capital openness (Chinn-Ito), down from the 0.9
                     placeholder; also what makes the transition path converge
  * ``debt_ratio_ss`` - 0.6 SS debt-to-GDP (PH ratio), not the 1.1 US default
  * ``nu``         - 0.2 TPI dampening (0.4 is marginally unstable here)
"""

import json
import os

import numpy as np

from ogphl import input_output as io

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
MULTISECTOR_PARAMS_PATH = os.path.join(
    CUR_DIR, "ogphl_multisector_default_parameters.json"
)

# Economy-wide capital share (the single-industry OG-PHL value, from the
# ILOSTAT labor share). The SAM's industry capital shares are rescaled to this
# value-added weighted mean; the raw average (~0.62) is biased upward by
# self-employed mixed income booked as capital.
ECONOMY_WIDE_GAMMA = 0.53785

# Public capital's output share, kept at the single-industry OG-PHL value.
PUBLIC_CAPITAL_SHARE = 0.05

# Open-economy capital openness. The single-industry default (0.9) implies ~96%
# foreign-owned capital -- far above the ~20% implied by the BSP International
# Investment Position. We anchor to the normalized Chinn-Ito openness index for
# the Philippines (~0.4), consistent with Feldstein-Horioka-implied mobility.
# This is also what lets the multi-industry steady state's transition path
# converge: at 0.9 domestic capital is a razor-thin ~4% of K and the K_d>=0
# constraint binds along the path; at 0.4 it has a comfortable buffer.
ZETA_K = 0.4

# Steady-state public-debt-to-GDP target. The Philippine ratio is ~60% (and is
# the model's initial_debt_ratio); 1.1 is the inherited US-style placeholder.
DEBT_RATIO_SS = 0.6

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
    gamma = io.get_gamma(target_avg=ECONOMY_WIDE_GAMMA)
    Z = io.get_Z(gamma=gamma, gamma_g=PUBLIC_CAPITAL_SHARE)
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
        "zeta_K": [ZETA_K],
        "debt_ratio_ss": DEBT_RATIO_SS,
        "nu": TPI_NU,
    }


def main():
    params = build_multisector_params()
    with open(MULTISECTOR_PARAMS_PATH, "w") as f:
        json.dump(params, f, indent=2)
        f.write("\n")
    print(f"Wrote {MULTISECTOR_PARAMS_PATH}")
    print(f"  M = {params['M']}, I = {params['I']}")
    print(f"  gamma = {np.round(params['gamma'], 4).tolist()}")
    print(f"  Z     = {np.round(params['Z'][0], 4).tolist()}")
    return params


if __name__ == "__main__":
    main()
