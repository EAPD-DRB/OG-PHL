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


def _io_va_mock_sam(import_cA=0.0):
    """A 2-sector mock SAM (Ag, Mfg) for the value-added io_matrix test.

    Ag (activity aA -> commodity cA): output 100, value added 100, no inputs.
    Mfg (activity aM -> commodity cM): output 100, value added 50, uses 50 of
    cA as an intermediate input. So a peso of the manufactured good cM embodies
    half Ag value added and half Mfg value added.
    """
    accounts = ["cA", "cM", "aA", "aM", "flab-n", "fcap", "row"] + io.HH_COLS
    sam = pd.DataFrame(0.0, index=accounts, columns=accounts)
    sam.loc["aA", "cA"] = 100.0  # make matrix (diagonal)
    sam.loc["aM", "cM"] = 100.0
    sam.loc["cA", "aM"] = 50.0  # Mfg uses 50 of the Ag commodity
    sam.loc["flab-n", "aA"] = 60.0  # Ag value added = 100
    sam.loc["fcap", "aA"] = 40.0
    sam.loc["flab-n", "aM"] = 30.0  # Mfg value added = 50
    sam.loc["fcap", "aM"] = 20.0
    sam.loc["cA", "hhd-r1"] = 100.0  # household final consumption
    sam.loc["cM", "hhd-r1"] = 100.0
    sam.loc["row", "cA"] = import_cA  # imports of the Ag commodity
    return sam


io_va_cons_dict = {"Food": ["cA"], "Goods": ["cM"]}
io_va_prod_dict = {"Ag": ["aA"], "Mfg": ["aM"]}


def test_get_io_matrix_value_added_indirect():
    """
    A manufactured good embodies the value added of its upstream inputs.

    With no imports, half of a peso of the 'Goods' consumption good (cM) is Ag
    value added (the cA input) and half is Mfg value added.
    """
    df = io.get_io_matrix_value_added(
        sam=_io_va_mock_sam(),
        cons_dict=io_va_cons_dict,
        prod_dict=io_va_prod_dict,
    )
    assert df.loc["Food", "Ag"] == pytest.approx(1.0)
    assert df.loc["Food", "Mfg"] == pytest.approx(0.0)
    assert df.loc["Goods", "Ag"] == pytest.approx(0.5)
    assert df.loc["Goods", "Mfg"] == pytest.approx(0.5)
    assert df.sum(axis=1).tolist() == pytest.approx([1.0, 1.0])


def test_get_io_matrix_value_added_imports():
    """
    Imported intermediates are netted out before the row is renormalized.

    With half of cA's supply imported, the Ag value added embodied in 'Goods'
    falls from 1/2 to 1/3 (the imported half carries no domestic value added).
    """
    df = io.get_io_matrix_value_added(
        sam=_io_va_mock_sam(import_cA=100.0),
        cons_dict=io_va_cons_dict,
        prod_dict=io_va_prod_dict,
    )
    assert df.loc["Goods", "Ag"] == pytest.approx(1.0 / 3.0)
    assert df.loc["Goods", "Mfg"] == pytest.approx(2.0 / 3.0)
    assert df.sum(axis=1).tolist() == pytest.approx([1.0, 1.0])


def test_get_io_matrix_value_added_packaged_sam():
    """
    Integration test: the packaged SAM yields a valid 5x8 io_matrix whose rows
    sum to one, with electricity dominating the energy & water good.
    """
    from ogphl.constants import CONS_DICT, PROD_DICT

    df = io.get_io_matrix_value_added()
    assert df.shape == (len(CONS_DICT), len(PROD_DICT))
    assert df.values.min() >= -1e-12
    assert df.sum(axis=1).tolist() == pytest.approx([1.0] * len(CONS_DICT))
    assert df.loc["Energy and water", "Electricity"] > 0.5


@patch("ogphl.input_output.read_SAM", return_value=None)
def test_get_io_matrix_value_added_raises_on_none_sam(mock_read_sam):
    """
    get_io_matrix_value_added() raises RuntimeError when the SAM is missing.
    """
    with pytest.raises(RuntimeError, match="Cannot compute io_matrix"):
        io.get_io_matrix_value_added()
