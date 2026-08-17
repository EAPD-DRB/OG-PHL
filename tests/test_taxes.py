"""
Tests of the tax calibration in the packaged single-industry JSON.

Every instrument is calibrated to actual collections as a share of GDP (OECD
Revenue Statistics in Asia and the Pacific 2025, Philippines, 2023), not to
statutory rates. These tests pin the shipped parameters to their sources and
check the internal consistency that the calibration rests on. No model solve.
"""

import json

from importlib.resources import files

import numpy as np
import pytest

# OECD Revenue Statistics in Asia and the Pacific 2025, Philippines, 2023,
# percent of GDP.
OECD_PIT = 0.0312
OECD_SSC = 0.0278
OECD_CIT = 0.0290
OECD_INDIRECT = 0.0739  # VAT 4.14 + specific goods and services 3.16

# TRAIN Law (RA 10963) schedule, effective 2023 onward: (lower bound, marginal
# rate, tax at lower bound), annual taxable income in pesos.
TRAIN = [
    (0, 0.00, 0),
    (250_000, 0.15, 0),
    (400_000, 0.20, 22_500),
    (800_000, 0.25, 102_500),
    (2_000_000, 0.30, 402_500),
    (8_000_000, 0.35, 2_202_500),
]


def statutory_etr(y):
    lo, rate, base = [row for row in TRAIN if row[0] <= y][-1]
    return (base + rate * (y - lo)) / y


def gs_etr(y, phi0, phi1, phi2):
    return (phi0 * (y - (y**-phi1 + phi2) ** (-1 / phi1))) / y


@pytest.fixture(scope="module")
def packaged():
    return json.loads(
        files("ogphl").joinpath("ogphl_default_parameters.json").read_text()
    )


@pytest.fixture(scope="module")
def gs_params(packaged):
    assert packaged["tax_func_type"] == "GS"
    return packaged["etr_params"][0][0]


def test_gs_top_rate_is_statutory(gs_params):
    """phi0 is anchored to the TRAIN top marginal rate, not fitted."""
    assert gs_params[0] == 0.35


def test_etr_mtr_params_are_identical(packaged):
    """GS marginal rates are the analytic derivative of the tax function, so
    all three parameter blocks carry the same triple."""
    assert packaged["etr_params"] == packaged["mtrx_params"]
    assert packaged["etr_params"] == packaged["mtry_params"]


def test_gs_effective_rate_is_progressive_and_below_statutory(gs_params):
    """The tuned schedule must (a) be monotone increasing in income, (b) never
    exceed the statutory schedule above the exempt threshold (phi2 is tuned
    DOWN from the statutory fit for informality), and (c) approach the top
    rate from below."""
    phi0, phi1, phi2 = gs_params
    grid = np.logspace(np.log10(300_000), 9, 200)
    etr = gs_etr(grid, phi0, phi1, phi2)
    assert np.all(np.diff(etr) > 0)
    statutory = np.array([statutory_etr(y) for y in grid])
    assert np.all(etr <= statutory + 1e-9)
    assert etr[-1] < phi0


def test_gs_near_zero_below_exempt_threshold(gs_params):
    """TRAIN exempts income below 250k. GS cannot hit exactly zero (that is
    the smoothing cost of the functional form, accepted in exchange for never
    going negative like HSV), but the effective rate there must be a rounding
    error next to the old flat 20%, not a real burden."""
    assert gs_etr(200_000, *gs_params) < 0.015
    assert gs_etr(100_000, *gs_params) < 0.006


def test_payroll_rate_matches_ssc_collections(packaged):
    """tau_payroll = SSC collections / labor share of income, so payroll
    revenue in the model equals actual SSC revenue as a share of GDP."""
    labor_share = 1.0 - packaged["gamma"][0] - packaged["gamma_g"][0]
    expected = OECD_SSC / labor_share
    assert packaged["tau_payroll"][0] == pytest.approx(expected, abs=5e-4)


def test_frac_tax_payroll_is_the_reporting_split(packaged):
    """frac_tax_payroll divides combined household tax revenue into PIT and
    payroll lines for reporting; it must equal SSC/(SSC+PIT)."""
    expected = OECD_SSC / (OECD_SSC + OECD_PIT)
    assert packaged["frac_tax_payroll"][0] == pytest.approx(expected, abs=1e-3)


def test_cit_is_statutory_rate_with_collections_adjustment(packaged):
    """The statutory CREATE rate stays visible in cit_rate; the effective rate
    comes from the adjustment factor tuned so the business-tax line collects
    CIT proper (2.90) + BTr income from government capital (GOCC/BSP
    dividends, PAGCOR share, ~1.00) + unallocable income taxes (0.30)."""
    assert packaged["cit_rate"][0][0] == 0.25
    assert 0.5 < packaged["adjustment_factor_for_cit_receipts"][0] < 0.7


def test_wealth_tax_captures_property_type_taxes(packaged):
    """The wealth tax is the instrument for OECD 'other taxes' less estate
    (property taxes, DST, LGU levies, 1.32% of GDP): near-flat effective rate
    p_wealth on wealth (m_wealth tiny), zero at zero wealth."""
    assert packaged["h_wealth"][0] == 1.0
    assert packaged["m_wealth"][0] == pytest.approx(0.001)
    assert 0.002 < packaged["p_wealth"][0] < 0.006


def test_zeta_k_is_level_validated_against_iip(packaged):
    """zeta_K is a marginal fill share tuned so the solved foreign share of
    capital matches the BSP IIP (~20%); the Chinn-Ito index (~0.4) is the
    prior, not the target."""
    assert 0.4 <= packaged["zeta_K"][0] <= 0.55


def test_bequest_tax_is_effective_not_statutory(packaged):
    """Statutory estate tax is 6%; effective collections are ~0.07% of GDP.
    Guards against reverting to the statutory rate (which over-collected
    17x)."""
    assert packaged["tau_bq"][0] < 0.01


def test_tau_c_covers_all_indirect_taxes(packaged):
    """tau_c is tuned so collections match VAT + excises + customs (7.39% of
    GDP), which lands near but not at the 12% statutory VAT rate."""
    assert 0.10 < packaged["tau_c"][0][0] < 0.15


def test_fiscal_identity_alpha_g(packaged):
    """alpha_G is set to the level consistent with the debt target: revenue
    minus the debt-stabilizing primary balance minus transfers and public
    investment. Uses the model's own SS growth rate and the calibrated
    steady-state r_gov of ~2.0% (BTr FY2024: interest P763.3bn on ~P15.3tn
    average debt, less ~3% expected inflation). Revenue includes the captured
    non-tax lines: BTr income + unallocable income taxes on the CIT side
    (4.20 total), fees on the indirect side (7.94), and property-type taxes
    via the wealth tax (1.32)."""
    r_gov_ss = 0.020
    g = np.exp(0.0371282577980211) * (1 + packaged["g_n_ss"]) - 1
    pb_star = (r_gov_ss - g) / (1 + g) * packaged["debt_ratio_ss"]
    revenue = OECD_PIT + OECD_SSC + 0.0420 + 0.0794 + 0.0132 + 0.0007
    consistent = revenue - pb_star - packaged["alpha_T"][0] - 0.052
    assert packaged["alpha_G"][-1] == pytest.approx(consistent, abs=0.004)


def test_alpha_g_glides_from_program_stance_to_identity(packaged):
    """alpha_G is a declining path: each early value reproduces the MTFF's
    programmed primary balance (deficit less BESF interest) given the model's
    realized transition revenue under the data-anchored initial wealth, and
    the path reaches the debt-stabilizing level by 2028. A flat
    identity-value alpha_G makes the model consolidate years ahead of the
    government's own plan. Values re-derived on the solved transition:
    revenue 19.32/19.58 in 2026/27, program pb -2.22/-1.60, alpha_T 4.48,
    alpha_I 5.1."""
    path = packaged["alpha_G"]
    assert len(path) > 1
    assert all(a > b for a, b in zip(path, path[1:]))
    assert path == pytest.approx([0.1122, 0.1092, 0.1045], abs=1e-6)


def test_alpha_i_is_the_mtff_infrastructure_program(packaged):
    """alpha_I maps the MTFF infrastructure program onto the 2025 start:
    5.3% (2025), 5.1/5.1 (2026-27), 5.2 (2028+)."""
    assert packaged["alpha_I"] == pytest.approx(
        [0.053, 0.051, 0.051, 0.052], abs=1e-6
    )


def test_initial_public_capital_matches_icsd(packaged):
    """initial_Kg_ratio 0.38 is the ICSD/PIMA-informed public capital stock
    (~0.35-0.40 of GDP), the same figure subtracted in the initial-wealth
    construction -- the two must stay consistent."""
    assert packaged["initial_Kg_ratio"] == pytest.approx(0.38, abs=1e-6)


def test_initial_wealth_is_data_anchored(packaged):
    """initial_wealth_ratio (requires PSLmodels/OG-Core#1189) anchors
    aggregate initial wealth relative to steady-state GDP; the value 2.677
    is chosen so the SOLVED initial wealth-to-GDP ratio equals the data
    target of 3.35 = (PWT 2023 total K/Y 3.97 - ICSD public capital ~0.38)
    x 0.80 domestic share (BSP IIP) + 0.48 domestically-held debt (BTr).
    Delivered ratio is verified in the transition run (goodness-of-fit).
    Without the anchor every initial household starts with ~63% more wealth
    than its steady-state counterpart and retirees consume the windfall."""
    data_target = (3.97 - 0.38) * 0.8 + 0.8 * 0.6
    assert data_target == pytest.approx(3.35, abs=0.005)
    assert packaged["initial_wealth_ratio"] == pytest.approx(2.783, abs=1e-6)
    # parameter < data target because Y(0) < Y_ss for a converging economy
    assert packaged["initial_wealth_ratio"] < data_target


def test_start_year_is_last_observed_year(packaged):
    """The start year is a calibration decision: the most recent year the
    calibration observes (2025), not a projection year. initial_debt_ratio
    0.60 matches beginning-of-2025 debt (end-2024: 60.7%, BTr) and alpha_RM
    is the observed 2025 personal-remittance ratio."""
    assert packaged["start_year"] == 2025


def test_tpi_uses_anderson_acceleration(packaged):
    """Anderson cuts the transition solve ~10x on this model (11-12
    iterations / ~2 min vs ~30-70 / ~20 min damped), validated on both the
    baseline and the initial-wealth comparison runs."""
    assert packaged["TPI_outer_method"] == "anderson"
