"""
Tests of the multi-industry calibration builder and its packaged JSON overlay.
"""

import importlib.resources
import json

import numpy as np
import pytest

from ogphl.create_multisector_calibration import (
    build_calibration,
    build_multisector_params,
)


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
        "chi_b",
        "chi_n",
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


def test_packaged_multisector_json_is_self_sufficient_and_in_sync():
    """
    The committed multisector JSON is a full, self-sufficient parameter set
    (the single-industry base with the multi-industry values applied), and it
    matches what the builder produces -- so the model can load it on its own,
    and the static artifact cannot silently drift from its generating tool.
    """
    with (
        importlib.resources.files("ogphl")
        .joinpath("ogphl_multisector_default_parameters.json")
        .open() as f
    ):
        shipped = json.load(f)
    # Self-sufficient: the complete key set of the base-merged calibration --
    # far more than the ~14 multi-industry values, so it carries the whole
    # single-industry base (a base-only parameter like sigma is present).
    assert set(shipped.keys()) == set(build_calibration().keys())
    assert "sigma" in shipped
    assert len(shipped) > 5 * len(build_multisector_params())
    # In sync: the computed multi-industry values match the builder.
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
    np.testing.assert_allclose(shipped["chi_b"], built["chi_b"], rtol=1e-9)
    np.testing.assert_allclose(shipped["chi_n"], built["chi_n"], rtol=1e-9)


def test_chi_units_conversion():
    """
    chi_b and chi_n in the overlay are the base weights scaled by
    k**(sigma-1), the exact FOC-preserving conversion for the multi-good
    composite-consumption units (k is the constant OG-Core's unnormalized
    price index picks up).
    """
    with (
        importlib.resources.files("ogphl")
        .joinpath("ogphl_default_parameters.json")
        .open() as f
    ):
        base = json.load(f)
    built = build_multisector_params()
    alpha = np.array(built["alpha_c"])
    k = float(np.prod(alpha**-alpha))
    scale = k ** (base["sigma"] - 1.0)
    assert scale > 1.0  # I>1 shrinks composite units, so weights scale up
    np.testing.assert_allclose(
        built["chi_b"], np.array(base["chi_b"]) * scale, rtol=1e-12
    )
    np.testing.assert_allclose(
        built["chi_n"], np.array(base["chi_n"]) * scale, rtol=1e-12
    )
