"""
Tests of the initial distribution of household wealth. No model solve.
"""

import json
import os
import pickle

import numpy as np
import pytest

from ogphl import initial_wealth

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
JSON_PATH = os.path.join(
    CUR_PATH, "..", "ogphl", "ogphl_default_parameters.json"
)


@pytest.fixture(scope="module")
def packaged():
    with open(JSON_PATH) as f:
        return json.load(f)


def test_asset_income_is_the_latest_nta_profile():
    """The age shape is NTA private asset income per person, 2015, rising
    through working life and held at its last reported age (80)."""
    income, year = initial_wealth.asset_income_by_age([20, 40, 60, 80, 95])
    assert year == 2015
    assert income[0] < income[1] < income[2]
    assert income[4] == income[3]
    assert np.all(income >= 0)


def test_distribution_shape_and_sum():
    """An S x J matrix of shares of aggregate wealth, as OG-Core requires."""
    omega0 = np.full((80, 7), 1 / 560)
    b_ss = np.tile(np.linspace(0.1, 5, 80)[:, None], (1, 7))
    dist = initial_wealth.initial_hhwealth_dist(omega0, b_ss, 20)
    assert dist.shape == (80, 7)
    assert dist.sum() == pytest.approx(1.0)
    assert np.all(dist >= 0)
    # with no difference across groups in b_ss, each age is split by
    # population, equally here
    assert np.allclose(dist / dist.sum(axis=1, keepdims=True), 1 / 7)


def test_packaged_distribution_matches_the_builder(packaged):
    """The packaged matrix is what the builder produces from the shipped
    seed and the packaged population, so it cannot drift from either."""
    with open(initial_wealth.SEED_PATH, "rb") as f:
        seed = pickle.load(f)
    omega0 = np.array(packaged["omega"])[0]
    built = initial_wealth.initial_hhwealth_dist(omega0, seed["b"], 20)
    shipped = np.array(packaged["initial_hhwealth_dist"])
    assert shipped.sum() == pytest.approx(1.0, abs=1e-9)
    np.testing.assert_allclose(shipped, built, atol=1e-8)
