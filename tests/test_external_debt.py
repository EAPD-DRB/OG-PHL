"""
Tests of the government debt block in the packaged JSON: debt contracted
abroad (OG-Core's alpha_D_ext and r_D_ext_annual) and market (domestic)
debt. No model solve.

Sources: BTr Debt Indicators, December 2025 (stocks at end-2024, interest
in 2024 and 2025) and the BTr investor profile of peso government
securities in ADB, Asia Bond Monitor, March 2026.
"""

import json
from importlib.resources import files

import pytest

from ogphl.targets import EXTERNAL_DEBT_SHARE, TARGETS
from ogphl.targets import MODEL_PER_MARKET_GDP as K_MKT

# End-2024 National Government debt, P million, and 2024 GDP
DOMESTIC_2024 = 10_930_415
EXTERNAL_2024 = 5_120_887
GDP_2024 = 26_446_369
# Effective nominal rate on external debt, 2024 and 2025: interest over the
# average stock (P223.5bn and P229.3bn)
EXTERNAL_RATE_NOMINAL = (0.04599 + 0.04281) / 2
FOREIGN_INFLATION = 0.02


@pytest.fixture(scope="module")
def packaged():
    return json.loads(
        files("ogphl").joinpath("ogphl_default_parameters.json").read_text()
    )


def test_external_debt_is_the_btr_external_stock(packaged):
    """Debt contracted abroad is the BTr's external debt, 19.36% of GDP at
    market prices, held at that level, converted to the model's Y."""
    assert EXTERNAL_DEBT_SHARE == pytest.approx(
        EXTERNAL_2024 / GDP_2024, abs=5e-5
    )
    assert packaged["alpha_D_ext"] == pytest.approx(
        [EXTERNAL_DEBT_SHARE * K_MKT], abs=1e-6
    )


def test_external_rate_is_real_in_output_units(packaged):
    """The foreign-currency effective rate less foreign inflation (the real
    exchange rate held constant)."""
    assert packaged["r_D_ext_annual"] == pytest.approx(
        [EXTERNAL_RATE_NOMINAL - FOREIGN_INFLATION], abs=1e-4
    )


def test_initial_market_debt_is_domestic_debt(packaged):
    """initial_debt_ratio is the domestic part of end-2024 debt; with the
    external part, all debt starts at the 60.7% of GDP the BTr reports."""
    domestic = DOMESTIC_2024 / GDP_2024
    assert packaged["initial_debt_ratio"] == pytest.approx(
        domestic * K_MKT, abs=1e-5
    )
    total = (
        packaged["initial_debt_ratio"] + packaged["alpha_D_ext"][0]
    ) / K_MKT
    assert total == pytest.approx(0.607, abs=1e-3)


def test_long_run_anchor_is_all_debt(packaged):
    """debt_ratio_ss is market debt: the 60% anchor on all debt less the
    external debt. The debt premium is centred on the same 60%, where
    OG-Core evaluates it (all government debt)."""
    anchor = TARGETS["D/Y"][0]
    total = packaged["debt_ratio_ss"] + packaged["alpha_D_ext"][-1]
    assert total == pytest.approx(anchor * K_MKT, abs=1e-5)
    vertex = -packaged["r_gov_DY"] / (2 * packaged["r_gov_DY2"])
    assert vertex == pytest.approx(anchor * K_MKT, abs=2e-3)


def test_foreign_share_of_market_debt_is_non_residents_peso_holdings(
    packaged,
):
    """Non-residents' share of peso government securities, 4.2% at
    end-2024 and 4.8% at end-2025; not the external debt's 20% of GDP,
    which an earlier version used."""
    assert packaged["initial_foreign_debt_ratio"] == pytest.approx(0.042)
    assert packaged["zeta_D"] == pytest.approx([0.048])
