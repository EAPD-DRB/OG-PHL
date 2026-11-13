"""
Tests of the steady-state dashboard targets. No model solve.
"""

import numpy as np

import pytest

from ogphl.targets import (
    CONS_TAX_SHARE,
    MODEL_PER_MARKET_GDP,
    TARGETS,
    TRANSITION_TARGETS,
    ss_moments,
    tpi_moments,
)

SS_KEYS = [
    "Y",
    "C",
    "I_total",
    "I_g",
    "G",
    "iit_revenue",
    "payroll_tax_revenue",
    "business_tax_revenue",
    "cons_tax_revenue",
    "wealth_tax_revenue",
    "bequest_tax_revenue",
    "total_tax_revenue",
    "r_gov",
    "D",
    "D_f",
    "TR",
    "agg_pension_outlays",
    "K_f",
    "K",
    "RM",
    "B",
    "BQ",
    "r",
    "factor",
]


def test_every_target_has_a_value_and_a_source():
    for name, (value, source) in TARGETS.items():
        assert np.isfinite(value), name
        assert isinstance(source, str) and source.strip(), name


def test_steady_state_targets_have_model_moments():
    """Every steady-state target has a matching model moment; the
    initial-wealth anchor is a transition-path target, read elsewhere."""
    ss = {k: np.array(1.0) for k in SS_KEYS}
    moments = ss_moments(ss)
    for name in TARGETS:
        if name.endswith("anchor"):
            continue
        assert name in moments, name


def test_moments_are_shares_of_market_price_gdp():
    """Model ratios are divided by Y plus consumption tax, GDP at market
    prices, the basis every data target is published on."""
    ss = {k: np.array(1.0) for k in SS_KEYS}
    ss["cons_tax_revenue"] = np.array(0.1)
    m = ss_moments(ss)
    assert m["PIT/Y"] == pytest.approx(1 / 1.1)
    assert m["GDP mkt / Y"] == pytest.approx(1.1)


def test_market_to_model_factor_matches_the_cons_tax_target():
    """A data share x of market GDP is x * MODEL_PER_MARKET_GDP of the
    model's Y when consumption tax is CONS_TAX_SHARE of market GDP."""
    tax = CONS_TAX_SHARE * MODEL_PER_MARKET_GDP  # as a share of Y
    assert 1 + tax == pytest.approx(MODEL_PER_MARKET_GDP)
    assert TARGETS["cons tax/Y"][0] == CONS_TAX_SHARE


def test_transition_targets_have_model_moments():
    """The discount factor and the foreign-capital share are tuned to the
    first transition period; each target has a moment there."""
    keys = SS_KEYS + ["total_primary_government_outlays"]
    tpi = {k: np.ones(5) for k in keys}
    moments = tpi_moments(tpi)
    for name in TRANSITION_TARGETS:
        assert name in moments, name
