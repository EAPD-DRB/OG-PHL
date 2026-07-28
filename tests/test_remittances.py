"""
Tests of the remittance calibration in the packaged single-industry JSON.

Remittances are calibrated as a constant share of GDP. Holding that share
takes two things: ``alpha_RM_1 == alpha_RM_T`` for the level, and a ``g_RM``
path that tracks ``g_n`` so ``aggregates.get_RM`` neither inflates nor
deflates remittances along the transition. These tests pin the level against
its source and assert the share actually stays flat -- the second is the one
that catches a stale ``g_RM`` after a demographics regeneration.

No model solve is involved.
"""

import json

from importlib.resources import files

import numpy as np
import pytest

from ogcore import aggregates as aggr
from ogcore.parameters import Specifications

from ogphl.update_baseline_demographics import flat_share_g_RM

# BSP full-year 2025: cash remittances US$35.63bn, which BSP reports as 7.3%
# of GDP, and personal remittances US$39.62bn. The model's RM is a household
# income inflow, so it takes the personal (BPM6) measure, not the narrower
# cash one BSP publishes the GDP ratio for.
BSP_CASH_SHARE_OF_GDP = 0.073
BSP_CASH_USD_BN = 35.63
BSP_PERSONAL_USD_BN = 39.62
EXPECTED_ALPHA_RM = 0.0812


@pytest.fixture(scope="module")
def packaged():
    return json.loads(
        files("ogphl").joinpath("ogphl_default_parameters.json").read_text()
    )


@pytest.fixture(scope="module")
def params(packaged):
    p = Specifications()
    p.update_specifications(packaged)
    return p


def test_alpha_rm_matches_bsp_personal_remittances(packaged):
    """The level is personal remittances / GDP, derived off BSP's own ratio."""
    derived = BSP_CASH_SHARE_OF_GDP * (BSP_PERSONAL_USD_BN / BSP_CASH_USD_BN)
    assert derived == pytest.approx(EXPECTED_ALPHA_RM, abs=5e-5)
    assert packaged["alpha_RM_1"] == EXPECTED_ALPHA_RM
    assert packaged["alpha_RM_T"] == EXPECTED_ALPHA_RM


def test_alpha_rm_is_in_bsp_personal_remittance_band(packaged):
    """BSP research puts personal remittances at 8-9% of GDP since 2017 and
    cash at 7-8%. Guards against silently reverting to the cash measure."""
    assert 0.080 <= packaged["alpha_RM_1"] <= 0.090


def test_no_remittance_transition_path(packaged):
    """A level shift between the first period and the steady state would be a
    modeling choice; the calibration deliberately makes none."""
    assert packaged["alpha_RM_1"] == packaged["alpha_RM_T"]


def test_g_rm_holds_remittances_at_a_constant_share_of_gdp(params):
    """The property the whole calibration rests on.

    ``get_RM`` compounds ``(1 + g_RM[t]) / (exp(g_y) * (1 + g_n[t-1]))``, so a
    ``g_RM`` that does not track ``g_n`` makes RM/Y drift for the first tG2
    periods. With the shipped 3% scalar the ratio fell 35% below target
    before recovering.
    """
    Y = np.ones(params.T + params.S)
    ratio = aggr.get_RM(Y, params, "TPI")[: params.T] / Y[: params.T]
    assert np.allclose(ratio, params.alpha_RM_T, atol=1e-12)


def test_packaged_g_rm_is_consistent_with_packaged_g_n(params, packaged):
    """g_RM is derived from g_n, so a demographics regeneration that forgets
    to rewrite it leaves the two inconsistent."""
    expected = flat_share_g_RM(params.g_y, params.g_n)
    assert np.allclose(np.array(packaged["g_RM"]), expected, atol=1e-12)


def test_flat_share_g_rm_is_not_representable_as_a_scalar(params):
    """Documents why g_RM is a path: g_n moves enough over the transition that
    no single constant holds the share flat."""
    g_RM = flat_share_g_RM(params.g_y, params.g_n)
    assert g_RM.max() - g_RM.min() > 0.02


def test_steady_state_remittances_equal_alpha_rm_times_output(params):
    """SS mode ignores g_RM entirely -- the share there is alpha_RM_T alone."""
    assert aggr.get_RM(np.ones(1), params, "SS") == pytest.approx(
        params.alpha_RM_T
    )


def test_eta_rm_is_a_distribution(packaged):
    """eta_RM allocates all of aggregate remittances: (S, J), sums to 1."""
    eta = np.array(packaged["eta_RM"])
    assert eta.shape == (80, 7)
    assert eta.min() >= 0
    assert eta.sum() == pytest.approx(1.0)


def test_eta_rm_reproduces_fies_concentration(packaged):
    """The group split must reproduce the FIES quintile mapping: the top
    ~20% of households (j5+j6+j7, lambdas 0.10+0.09+0.01) receive the top
    quintile's ~72% of remittance value; the bottom quarter receives ~1%.
    Guards against reverting to ogcore's population-proportional default
    (which would give them 20% and 25%)."""
    eta = np.array(packaged["eta_RM"])
    by_group = eta.sum(axis=0)
    assert by_group[4:].sum() == pytest.approx(0.7248, abs=0.01)
    assert by_group[0] == pytest.approx(0.0103, abs=0.005)


def test_eta_rm_is_per_capita_within_groups(packaged):
    """Within a lifetime-income group every household of every age receives
    the same amount: eta proportional to the group's age distribution."""
    eta = np.array(packaged["eta_RM"])
    omega = np.array(packaged["omega_SS"])
    per_hh = eta / np.maximum(omega, 1e-30)
    for j in range(7):
        assert np.allclose(per_hh[:, j], per_hh[0, j], rtol=1e-8)


def test_eta_rm_regenerates_from_packaged_demographics(packaged):
    """The packaged matrix must match the constructor applied to the packaged
    omega_SS -- a demographics regeneration that forgets eta_RM leaves the
    two inconsistent."""
    from ogphl.update_baseline_demographics import remittance_eta

    expected = remittance_eta(
        np.array(packaged["omega_SS"]), np.array(packaged["lambdas"])
    )
    assert np.allclose(np.array(packaged["eta_RM"]), expected, atol=1e-12)
