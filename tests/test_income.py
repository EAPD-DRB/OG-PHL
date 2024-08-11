"""
Tests of income.py module
"""

import pytest
import numpy as np
from ogphl import income


# @pytest.mark.parametrize(
#     "abil_wgts,expected_vals",
#     [
#         (abil_wgts1, expected_vals1),
#         (abil_wgts2, expected_vals2),
#         (abil_wgts3, expected_vals3),
#         (abil_wgts4, expected_vals4),
#     ],
#     ids=[
#         "J=7, default weights",
#         "non-default weights",
#         "J=10 weights",
#         "J=9 weights",
#     ],
# )
# Commenting out for now - need to update values above for PHL and
# there's probably a better way to do this
# def test_get_e_interp(abil_wgts, expected_vals):
#     """
#     Test of get_e_interp
#     """
#     age_wgts = np.ones(80) * 1 / 80
#     test_vals = income.get_e_interp(
#         80, age_wgts, age_wgts, abil_wgts, plot=True
#     )
#     print("test vals = ", test_vals)
#     assert np.allclose(test_vals, expected_vals)


def test_get_e_interp_exception():
    """
    Test that RuntimeError is abil_wgts not suitable for interpolation
    """
    age_wgts = np.ones(80) * 1 / 80
    abil_wgts = np.array([0.25, 0.25, 0.2, 0.1, 0.1, 0.09, 0.009999, 0.000001])
    with pytest.raises(RuntimeError):
        income.get_e_interp(20, 80, 8, abil_wgts, age_wgts)
