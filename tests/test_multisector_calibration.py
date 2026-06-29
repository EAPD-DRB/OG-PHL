"""
Tests of the multi-industry calibration builder and its packaged JSON overlay.
"""

import importlib.resources
import json

import numpy as np
import pytest

from ogphl.create_multisector_calibration import build_multisector_params


def test_build_multisector_params():
    """The builder produces a well-formed 8-industry, 5-good overlay."""
    p = build_multisector_params()
    assert p["M"] == 8
    assert p["I"] == 5
    for key in (
        "alpha_c",
        "io_matrix",
        "c_min",
        "gamma",
        "epsilon",
        "gamma_g",
        "Z",
        "cit_rate",
        "tau_c",
    ):
        assert key in p
    assert len(p["gamma"]) == 8
    assert len(p["Z"]) == 1 and len(p["Z"][0]) == 8
    assert np.shape(p["io_matrix"]) == (5, 8)
    assert p["Z"][0][-1] == pytest.approx(
        1.0
    )  # Manufacturing is the numeraire
    assert all(z > 0 for z in p["Z"][0])
    assert all(0.0 < g < 1.0 for g in p["gamma"])


def test_packaged_multisector_json_in_sync():
    """
    The committed multisector JSON matches what the builder produces, so the
    static artifact cannot silently drift from the tool that generates it.
    """
    with (
        importlib.resources.files("ogphl")
        .joinpath("ogphl_multisector_default_parameters.json")
        .open() as f
    ):
        shipped = json.load(f)
    built = build_multisector_params()
    assert shipped["M"] == built["M"]
    assert shipped["I"] == built["I"]
    np.testing.assert_allclose(shipped["gamma"], built["gamma"], rtol=1e-9)
    np.testing.assert_allclose(shipped["Z"][0], built["Z"][0], rtol=1e-9)
    np.testing.assert_allclose(
        np.array(shipped["io_matrix"]),
        np.array(built["io_matrix"]),
        rtol=1e-9,
    )
    np.testing.assert_allclose(shipped["alpha_c"], built["alpha_c"], rtol=1e-9)
