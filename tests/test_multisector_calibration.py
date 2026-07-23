"""
Tests of the multi-industry calibration builder and its packaged JSON overlay.
"""

import importlib.resources
import json

import numpy as np
import pytest

from ogphl.create_multisector_calibration import build_multisector_params

# The complete key set of the packaged overlay: only the parameters the
# multi-industry calibration changes relative to the single-industry base.
# A key appearing here must be a deliberate multi-industry choice; anything
# else (demographics, tax functions, the fiscal/macro block, solver seeds)
# is inherited from ogphl_default_parameters.json at load time.
OVERLAY_KEYS = {
    "M",
    "I",
    "alpha_c",
    "io_matrix",
    "c_min",
    "gamma",
    "epsilon",
    "gamma_g",
    "Z",
    "chi_b",
    "chi_n",
    "nu",
    "TPI_outer_method",
}


def _load_packaged(name):
    with importlib.resources.files("ogphl").joinpath(name).open() as f:
        return json.load(f)


def test_build_multisector_params():
    """The builder produces a well-formed 8-industry, 5-good overlay."""
    p = build_multisector_params()
    assert set(p.keys()) == OVERLAY_KEYS
    assert p["M"] == 8
    assert p["I"] == 5
    assert len(p["gamma"]) == 8
    assert len(p["Z"]) == 1 and len(p["Z"][0]) == 8
    assert np.shape(p["io_matrix"]) == (5, 8)
    assert p["Z"][0][-1] == pytest.approx(
        1.0
    )  # Manufacturing is the numeraire
    assert all(z > 0 for z in p["Z"][0])
    assert all(0.0 < g < 1.0 for g in p["gamma"])


def test_packaged_overlay_is_lean_and_in_sync():
    """
    The committed multisector JSON is a lean overlay -- exactly the
    whitelisted multi-industry keys, nothing else (so it can never silently
    fatten back into a full parameter set or thin below what the example
    needs) -- and every value matches what the builder produces, so the
    static artifact cannot drift from its generating tool.
    """
    shipped = _load_packaged("ogphl_multisector_default_parameters.json")
    assert set(shipped.keys()) == OVERLAY_KEYS
    built = build_multisector_params()
    assert shipped["M"] == built["M"]
    assert shipped["I"] == built["I"]
    assert shipped["nu"] == built["nu"]
    assert shipped["TPI_outer_method"] == built["TPI_outer_method"]
    np.testing.assert_allclose(shipped["gamma"], built["gamma"], rtol=1e-9)
    np.testing.assert_allclose(shipped["Z"][0], built["Z"][0], rtol=1e-9)
    np.testing.assert_allclose(
        np.array(shipped["io_matrix"]),
        np.array(built["io_matrix"]),
        rtol=1e-9,
    )
    np.testing.assert_allclose(shipped["alpha_c"], built["alpha_c"], rtol=1e-9)
    np.testing.assert_allclose(shipped["c_min"], built["c_min"], rtol=1e-9)
    np.testing.assert_allclose(shipped["epsilon"], built["epsilon"], rtol=1e-9)
    np.testing.assert_allclose(shipped["gamma_g"], built["gamma_g"], rtol=1e-9)
    np.testing.assert_allclose(shipped["chi_b"], built["chi_b"], rtol=1e-9)
    np.testing.assert_allclose(shipped["chi_n"], built["chi_n"], rtol=1e-9)


def test_overlay_applies_on_base():
    """
    The canonical two-step load -- the single-industry base, then the
    multi-industry overlay -- produces a coherent M=8, I=5 parameter set
    that keeps the base's economy-wide values (the overlay must be applied
    on top of the base, never loaded alone).
    """
    from ogcore.parameters import Specifications

    base = _load_packaged("ogphl_default_parameters.json")
    overlay = _load_packaged("ogphl_multisector_default_parameters.json")
    p = Specifications()
    p.update_specifications(base)
    p.update_specifications(overlay)
    assert p.M == 8
    assert p.I == 5
    np.testing.assert_allclose(p.gamma, overlay["gamma"], rtol=1e-12)
    np.testing.assert_allclose(p.Z[-1, :], overlay["Z"][0], rtol=1e-12)
    np.testing.assert_allclose(p.alpha_c, overlay["alpha_c"], rtol=1e-12)
    np.testing.assert_allclose(
        p.io_matrix, np.array(overlay["io_matrix"]), rtol=1e-12
    )
    # Economy-wide values come from the base, untouched by the overlay.
    assert p.debt_ratio_ss == pytest.approx(base["debt_ratio_ss"])
    assert p.zeta_K[0] == pytest.approx(base["zeta_K"][0])
    np.testing.assert_allclose(p.lambdas.flatten(), base["lambdas"])


def test_chi_units_conversion():
    """
    chi_b and chi_n in the overlay are the base weights scaled by
    k**(sigma-1), the exact FOC-preserving conversion for the multi-good
    composite-consumption units (k is the constant OG-Core's unnormalized
    price index picks up).
    """
    base = _load_packaged("ogphl_default_parameters.json")
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
