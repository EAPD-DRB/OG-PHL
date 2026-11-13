"""
Tests of the labor supply target and the chi_n calibration step. No model
solve.
"""

import json
import os

import numpy as np
import pytest
from ogcore.parameters import Specifications

from ogphl import income, labor

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
JSON_PATH = os.path.join(
    CUR_PATH, "..", "ogphl", "ogphl_default_parameters.json"
)


def test_hours_per_person_are_ilostat_lfs_values():
    """Hours per person are the employment-to-population ratio times the mean
    hours of the employed: 76.5% x 42.94 hours at ages 35-39 in 2024."""
    h = income.hours_per_person("PHL", 2024, [37])
    assert h[0] == pytest.approx(0.75435 * 42.94, rel=1e-6)
    with pytest.raises(ValueError):
        income.hours_per_person("PHL", 1990, [37])


def test_labor_supply_target_shape():
    """The target is hours per person over a 112-hour week: about 0.29 at
    prime ages, 0.11 at 67, tapering with NTA labor income beyond the
    survey's open 65+ band and never below 2% of the time endowment."""
    t = labor.labor_supply_target(20, 80)
    assert t.shape == (80,)
    assert t[17] == pytest.approx(0.75435 * 42.94 / 112, rel=1e-6)
    assert t[47] == pytest.approx(0.34959 * 34.51 / 112, rel=1e-6)
    assert np.all(t[48:] <= t[47])
    assert t.min() >= labor.MIN_LABOR_SUPPLY


def test_chi_n_step_is_exact_at_the_target():
    """At the target the step leaves chi_n unchanged; where the model works
    more than the target the weight rises, and it never exceeds the cap."""
    p = Specifications()
    chi = np.full(p.S, 20.0)
    n = np.full(p.S, 0.3)
    assert np.allclose(labor.chi_n_step(chi, n, n, p), chi)
    up = labor.chi_n_step(chi, n * 1.5, n, p)
    assert np.all(up > chi)
    capped = labor.chi_n_step(np.full(p.S, 9999.0), n * 3, n * 0.1, p)
    assert np.all(capped <= labor.MAX_CHI_N)


def test_packaged_chi_n_is_calibrated():
    """The packaged chi_n is the Philippine calibration, not OG-USA's
    profile: weights rise steeply after 60, where Filipinos work little
    per hour of productivity."""
    with open(JSON_PATH) as f:
        chi_n = np.array(json.load(f)["chi_n"])
    assert chi_n.shape == (80,)
    assert chi_n[45] > 2 * chi_n[20]
