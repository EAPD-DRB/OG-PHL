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

from ogphl.targets import EXTERNAL_DEBT_SHARE
from ogphl.targets import MODEL_PER_MARKET_GDP as K_MKT

# OECD Revenue Statistics in Asia and the Pacific 2025, Philippines, 2023,
# percent of GDP. Data shares are of GDP at market prices; OG-Core's Y
# excludes the consumption tax, so a share of Y is the data share times
# K_MKT (ogphl/targets.py).
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
    revenue in the model equals actual SSC revenue as a share of GDP at
    market prices."""
    labor_share = 1.0 - packaged["gamma"][0] - packaged["gamma_g"][0]
    expected = OECD_SSC * K_MKT / labor_share
    assert packaged["tau_payroll"][0][0] == pytest.approx(expected, abs=5e-4)


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
    assert 0.6 < packaged["adjustment_factor_for_cit_receipts"][0] < 0.8


def test_wealth_tax_captures_property_type_taxes(packaged):
    """The wealth tax is the instrument for OECD 'other taxes' less estate
    (property taxes, DST, LGU levies, 1.32% of GDP): near-flat effective rate
    p_wealth on wealth (m_wealth tiny), zero at zero wealth."""
    assert packaged["h_wealth"][0] == 1.0
    assert packaged["m_wealth"][0] == pytest.approx(0.001)
    assert 0.002 < packaged["p_wealth"][0] < 0.006


def test_zeta_k_is_level_validated_against_iip(packaged):
    """zeta_K is a marginal fill share tuned so the foreign share of capital
    in the first transition year, 2025, matches the BSP IIP (~20%); the
    steady state's share (about 14%) is an outcome. It is the share of the
    gap between capital demanded at the world rate and domestically owned
    capital that foreigners fill; with the return on capital at ~8% against
    a 5% world rate that gap is moderate, so a share of about 0.15 delivers
    the IIP level. The Chinn-Ito index (~0.4) measures legal openness, not
    this share."""
    assert 0.12 <= packaged["zeta_K"][0] <= 0.22


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
    """alpha_G's last entry holds from 2027 until the budget rule takes over
    (tG1), so it is the near-term debt-stabilizing level: revenue minus the
    debt-stabilizing primary balance minus transfers, public investment and
    near-term pension outlays. It is not the steady state's G, which is far
    lower because the steady state carries a mature pension system in an
    aged population (pensions 6.3% of GDP; see test_pensions_are_sss_db).
    Uses the model's own SS growth rate and the two debt rates: market
    (domestic) debt, 40.64% of GDP, at r_gov 2.33% (BTr 2024-2025 domestic
    interest over average domestic debt, 5.33% nominal, less ~3% expected
    inflation), and debt contracted abroad, 19.36% of GDP, at 2.44% (4.44%
    nominal less 2% foreign inflation). Revenue includes the captured non-
    tax lines: BTr income + unallocable income taxes on the CIT side (4.20
    total), fees on the indirect side (7.94), and property-type taxes via
    the wealth tax (1.32). Near-term pensions: 2.28% of GDP today (SSS +
    GSIS + MUP), rising with covered retirees per worker to 3.4% by 2044
    (2.87% average over 2027-2044); public investment averages 5.15% of
    GDP. Every term is a share of GDP at market prices; alpha_G is a share
    of the model's Y, so the identity is scaled by K_MKT. The packaged
    value is derived from the solved transition instead (the level that
    returns debt to 60% of GDP by 2044, when the budget rule takes over),
    which sits below this static value by the transition's revenue
    shortfall: revenue dips to about 18.2% of GDP mid-window against 19.4%
    at the data and the steady state."""
    r_gov_ss = 0.0233
    r_ext = packaged["r_D_ext_annual"][0]
    d_ext = EXTERNAL_DEBT_SHARE
    g = np.exp(packaged["g_y_annual"]) * (1 + packaged["g_n_ss"]) - 1
    pb_star = ((r_gov_ss - g) * (0.60 - d_ext) + (r_ext - g) * d_ext) / (1 + g)
    revenue = OECD_PIT + OECD_SSC + 0.0420 + 0.0794 + 0.0132 + 0.0007
    near_term_pensions = 0.0287
    static = revenue - pb_star - 0.0448 - 0.0515 - near_term_pensions
    shortfall = static - packaged["alpha_G"][-1] / K_MKT
    assert 0.0 < shortfall < 0.025


def test_alpha_g_glides_from_program_stance_to_identity(packaged):
    """alpha_G is a declining path: the 2025-2028 values reproduce the
    programmed primary balance (DBM BESF FY2026 Table A.2, deficit less
    interest: -2.51, -2.26, -1.59 and -1.03% of GDP; ogphl/data/
    fiscal_program_PHL.csv) given the model's realized
    transition revenue and phased-in pension outlays, and from 2029 the path
    holds the level that returns debt to 60% of GDP by 2044, when the budget
    rule (tG1) takes over. A flat alpha_G makes the
    model consolidate years ahead of the government's own plan."""
    path = packaged["alpha_G"]
    assert len(path) == 5
    assert all(a > b for a, b in zip(path, path[1:]))
    assert path == pytest.approx(
        [0.10292, 0.1002, 0.0909, 0.08183, 0.0708], abs=1e-6
    )


def test_pensions_are_sss_db(packaged):
    """Public pensions follow the SSS defined-benefit rules (RA 11199; OECD
    Pensions at a Glance Asia/Pacific 2024): pension age 60, benefit 20% of
    average monthly earnings plus 2% per credited year beyond ten, about 2%
    per year over a 40-year career, paid 13 times a year, on the greater of
    the last five years' or the career average (nominal and unindexed, so
    the last five years in practice). Coverage is the formal groups (about
    36% of the employed contribute to SSS or GSIS) times one scale that also
    carries generosity: GSIS and military pensions (54% of spending) pay more
    than the SSS formula, and the formula's flat add-ons are not modeled, so
    the scale may exceed one. It is set so outlays are 2.28% of GDP today
    (SSS 1.06% 2023, GSIS 0.68% 2024, MUP pension and gratuity fund 0.54%
    2024 GAA) times the rise in covered
    retirees per worker to the steady state (factor 3.056, which weights by
    coverage because the covered groups live longer): 6.97% of GDP in the
    steady state. Replaces the US system, which the repo had switched
    off with zero benefit rates while collecting contributions. The mature
    scale applies from 2050; from 2025 it rises linearly from 80% of it, so
    outlays start at today's 2.28% of GDP (the maturing of the scheme: a
    mature system from the start pays about 2.8%)."""
    assert packaged["pension_system"] == "Defined Benefits"
    assert packaged["retirement_age"] == [60]
    assert packaged["yr_contrib"] == 40
    assert packaged["avg_earn_num_years"] == 5
    assert packaged["alpha_db"][0][0] == pytest.approx(
        0.02 * 13 / 12, abs=1e-4
    )
    shape = [0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0]
    rows = packaged["replacement_rate_adjust"]
    coverage = rows[-1]
    scale = coverage[-1]
    assert coverage == pytest.approx([c * scale for c in shape], abs=1e-4)
    assert 0.8 < scale <= 1.2
    phase = [row[-1] / scale for row in rows]
    assert len(rows) == 26
    assert phase[0] == pytest.approx(0.8007, abs=1e-4)
    assert all(a < b for a, b in zip(phase, phase[1:]))


def test_alpha_i_is_the_mtff_infrastructure_program(packaged):
    """alpha_I maps the MTFF infrastructure program onto the 2025 start:
    5.3% of GDP (2025), 5.1/5.1 (2026-27), 5.2 (2028+), as shares of Y."""
    program = np.array([0.053, 0.051, 0.051, 0.052])
    assert packaged["alpha_I"] == pytest.approx(program * K_MKT, abs=1e-6)


def test_initial_public_capital_matches_icsd(packaged):
    """initial_Kg_ratio 0.38 is the ICSD/PIMA-informed public capital stock
    (~0.35-0.40 of GDP), the same figure subtracted in the initial-wealth
    construction -- the two must stay consistent."""
    assert packaged["initial_Kg_ratio"] == pytest.approx(
        0.38 * K_MKT, abs=1e-6
    )


def test_initial_wealth_is_data_anchored(packaged):
    """Since ogcore 0.22, initial_wealth_ratio is the target ratio of initial
    household wealth to initial-period GDP, so it is set to the data value
    itself: 3.35 = (PWT 2023 total K/Y 3.97 - ICSD public capital ~0.38)
    x 0.80 domestic share (BSP IIP) + 0.48 domestically-held debt (BTr).
    Without the anchor every initial household starts with ~63% more wealth
    than its steady-state counterpart and retirees consume the windfall."""
    data_target = (3.97 - 0.38) * 0.8 + 0.8 * 0.6
    assert data_target == pytest.approx(3.35, abs=0.005)
    assert packaged["initial_wealth_ratio"] == pytest.approx(
        3.35 * K_MKT, abs=1e-6
    )


def test_delta_is_measured_depreciation(packaged):
    """delta = consumption of fixed capital / capital stock: World Bank CFC
    10.12% of GNI (2021) x GNI/GDP 1.036 = 10.48% of GDP, over PWT 11 capital
    at constant national prices, 4.04 x GDP in 2021, gives 0.026 (2020: 0.025).
    Public capital is assumed to depreciate at the same rate (no published
    split). Replaces the US default 0.05."""
    cfc_gdp = 0.10123 * (20101002089900 / 19410614486200)
    k_y = 4124357.75 / 1020730.875
    assert cfc_gdp / k_y == pytest.approx(0.026, abs=0.0005)
    assert packaged["delta_annual"] == 0.026


def test_beta_is_tuned_to_first_year_investment(packaged):
    """beta_annual is tuned (not sourced) so fixed investment in the first
    transition year, 2025, is the national accounts' 23.6% of GDP (World
    Bank, 2024), with household wealth at its data anchor and the initial
    distribution of wealth by age from the NTA. It is not tuned to the
    steady state's capital stock: the data describe today's young
    population, and the steady state's capital-output ratio (about 3.7) is an
    outcome of aging. Uniform across lifetime-income groups. Replaces the US
    default 0.96."""
    beta = packaged["beta_annual"]
    assert len(set(beta)) == 1
    assert 0.88 < beta[0] < 0.93


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


def test_g_y_is_growth_per_person_employed(packaged):
    """g_y is labor-augmenting productivity growth, so it is World Bank growth
    of GDP per person employed (SL.GDP.PCAP.EM.KD), mean 2001-2019, not per
    capita: the rise in the share of the population at work is produced by
    the model's own demographics. Per capita gave 0.0371."""
    assert packaged["g_y_annual"] == pytest.approx(0.031332, abs=1e-5)
