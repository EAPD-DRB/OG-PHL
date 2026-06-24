"""
Tests of input_output.py module
"""

import pandas as pd
import pytest
from unittest.mock import patch
from ogphl import input_output as io

sam_dict = {
    # "index": ["Beer", "Chocolate", "Car", "House"],
    "Ag": [30, 160, 0, 5],
    "Mining": [10, 0, 100, 100],
    "Manufacturing": [60, 40, 200, 295],
    "hhd-r1": [100, 200, 300, 400],
    "hhd-r2": [0, 0, 0, 0],
    "hhd-r3": [0, 0, 0, 0],
    "hhd-r4": [0, 0, 0, 0],
    "hhd-r5": [0, 0, 0, 0],
    "hhd-u1": [0, 0, 0, 0],
    "hhd-u2": [0, 0, 0, 0],
    "hhd-u3": [0, 0, 0, 0],
    "hhd-u4": [0, 0, 0, 0],
    "hhd-u5": [0, 0, 0, 0],
    "row": [10, 20, 30, 40],
}
sam_df = pd.DataFrame(sam_dict, index=["Beer", "Chocolate", "Car", "House"])

cons_dict = {"Food": ["Beer", "Chocolate"], "Non-food": ["Car", "House"]}

prod_dict = {
    "Primary": ["Ag", "Mining"],
    "Secondary": ["Manufacturing"],
}


@pytest.mark.parametrize(
    "sam_df, cons_dict",
    [
        (sam_df, cons_dict),
    ],
    ids=["Test 1"],
)
def test_get_alpha_c(sam_df, cons_dict):
    """
    Test of get_alpha_c() function
    """
    test_dict = io.get_alpha_c(sam=sam_df, cons_dict=cons_dict)

    assert isinstance(test_dict, dict)
    assert list(test_dict.keys()).sort() == ["Food", "Non-food"].sort()
    assert test_dict["Food"] == 270 / 900
    assert test_dict["Non-food"] == 630 / 900


@pytest.mark.parametrize(
    "sam_df, cons_dict, prod_dict",
    [
        (sam_df, cons_dict, prod_dict),
    ],
    ids=["Test 1"],
)
def test_get_io_matrix(sam_df, cons_dict, prod_dict):
    """
    Test of get_io_matrix()
    """
    test_df = io.get_io_matrix(
        sam=sam_df, cons_dict=cons_dict, prod_dict=prod_dict
    )

    assert isinstance(test_df, pd.DataFrame)
    assert list(test_df.columns).sort() == ["Primary", "Secondary"].sort()
    assert list(test_df.index).sort() == ["Food", "Non-food"].sort()
    assert test_df.loc["Food", "Primary"] == 2 / 3
    assert test_df.loc["Food", "Secondary"] == 1 / 3


@patch("ogphl.input_output.read_SAM", return_value=None)
def test_get_alpha_c_raises_on_none_sam(mock_read_sam):
    """
    get_alpha_c() raises RuntimeError when SAM data is unavailable.
    """
    with pytest.raises(RuntimeError, match="Cannot compute alpha_c"):
        io.get_alpha_c()


@patch("ogphl.input_output.read_SAM", return_value=None)
def test_get_io_matrix_raises_on_none_sam(mock_read_sam):
    """
    get_io_matrix() raises RuntimeError when SAM data is unavailable.
    """
    with pytest.raises(RuntimeError, match="Cannot compute io_matrix"):
        io.get_io_matrix()


# Mock SAM with factor-payment rows for the gamma calibration.
# Primary (Ag):   labor = 10 + 10 + 0 = 20, capital + land = 20 + 10 = 30
#                 -> gamma = 30 / 50 = 0.6
# Secondary (Mfg): labor = 40, capital + land = 10 + 0 = 10
#                 -> gamma = 10 / 50 = 0.2
gamma_sam_df = pd.DataFrame(
    {
        "Ag": {
            "flab-n": 10,
            "flab-p": 10,
            "flab-s": 0,
            "fcap": 20,
            "flnd": 10,
        },
        "Mfg": {"flab-n": 40, "flab-p": 0, "flab-s": 0, "fcap": 10, "flnd": 0},
        # a non-factor row that must be ignored by get_gamma
        "other": {"flab-n": 5, "flab-p": 5, "flab-s": 5, "fcap": 5, "flnd": 5},
    }
)
gamma_prod_dict = {"Primary": ["Ag"], "Secondary": ["Mfg"]}


def test_get_gamma():
    """
    Test of get_gamma() function
    """
    test_dict = io.get_gamma(sam=gamma_sam_df, prod_dict=gamma_prod_dict)

    assert isinstance(test_dict, dict)
    assert list(test_dict.keys()) == ["Primary", "Secondary"]
    assert test_dict["Primary"] == 30 / 50
    assert test_dict["Secondary"] == 10 / 50


def test_get_gamma_rescaled():
    """
    get_gamma() with target_avg rescales so the value-added weighted mean
    capital share equals the target while preserving the ratio across
    industries.

    Raw: Primary VA = 50, gamma = 0.6; Secondary VA = 50, gamma = 0.2.
    Weighted mean = 0.4. Scaling to 0.5 multiplies both by 1.25.
    """
    test_dict = io.get_gamma(
        sam=gamma_sam_df, prod_dict=gamma_prod_dict, target_avg=0.5
    )
    assert test_dict["Primary"] == pytest.approx(0.75)
    assert test_dict["Secondary"] == pytest.approx(0.25)
    # ratio between industries is preserved by the rescaling
    raw = io.get_gamma(sam=gamma_sam_df, prod_dict=gamma_prod_dict)
    assert test_dict["Primary"] / test_dict["Secondary"] == pytest.approx(
        raw["Primary"] / raw["Secondary"]
    )


def test_get_gamma_zero_value_added():
    """
    get_gamma() returns 0.0 for an industry with no factor payments
    rather than dividing by zero.
    """
    empty_sam = pd.DataFrame(
        {"Ag": {"flab-n": 0, "flab-p": 0, "flab-s": 0, "fcap": 0, "flnd": 0}}
    )
    test_dict = io.get_gamma(sam=empty_sam, prod_dict={"Primary": ["Ag"]})
    assert test_dict["Primary"] == 0.0


@patch("ogphl.input_output.read_SAM", return_value=None)
def test_get_gamma_raises_on_none_sam(mock_read_sam):
    """
    get_gamma() raises RuntimeError when SAM data is unavailable.
    """
    with pytest.raises(RuntimeError, match="Cannot compute gamma"):
        io.get_gamma()


def test_get_gamma_packaged_sam():
    """
    Integration test: the packaged SAM and the 8-industry PROD_DICT yield a
    capital share in (0, 1) for every industry, keyed consistently.
    """
    from ogphl.constants import PROD_DICT

    gamma = io.get_gamma()
    assert list(gamma.keys()) == list(PROD_DICT.keys())
    assert len(gamma) == 8
    assert all(0.0 < g < 1.0 for g in gamma.values())
