"""
Tests of calibrate.py module offline and partial-failure behavior.
"""

import warnings
from unittest.mock import MagicMock, patch

import numpy as np

from ogphl.calibrate import Calibration


def _make_mock_p(I=1, M=1):  # noqa: E741
    """Create a minimal mock Specifications object."""
    p = MagicMock()
    p.I = I
    p.M = M
    p.E = 20
    p.S = 80
    p.T = 160
    p.J = 7
    p.start_year = 2025
    p.lambdas = np.array([0.25, 0.25, 0.0625, 0.0625, 0.0625, 0.0625, 0.25])
    return p


class TestOfflineMode:
    """Tests for update_from_api=False."""

    def test_single_sector_returns_identity_values(self):
        p = _make_mock_p(I=1, M=1)
        c = Calibration(p, update_from_api=False)

        d = c.get_dict()
        np.testing.assert_array_equal(d["alpha_c"], np.array([1.0]))
        np.testing.assert_array_equal(d["io_matrix"], np.array([[1.0]]))

    def test_single_sector_no_demographics_or_macro(self):
        p = _make_mock_p(I=1, M=1)
        c = Calibration(p, update_from_api=False)

        d = c.get_dict()
        assert "e" not in d
        assert "omega" not in d
        assert "omega_SS" not in d
        assert "g_y_annual" not in d
        assert "initial_debt_ratio" not in d

    def test_multi_sector_omits_alpha_c_and_io_matrix(self):
        p = _make_mock_p(I=5, M=4)
        c = Calibration(p, update_from_api=False)

        assert c.get_dict() == {}
        assert c.alpha_c is None
        assert c.io_matrix is None

    @patch("ogphl.calibrate.macro_params")
    @patch("ogphl.calibrate.io")
    def test_no_external_calls(self, mock_io, mock_macro):
        p = _make_mock_p(I=5, M=4)
        Calibration(p, update_from_api=False)

        mock_macro.get_macro_params.assert_not_called()
        mock_io.get_alpha_c.assert_not_called()
        mock_io.get_io_matrix.assert_not_called()


class TestOnlinePartialFailure:
    """Tests for update_from_api=True with mocked partial failures."""

    @patch("ogphl.calibrate.macro_params")
    def test_macro_failure_warns_and_omits(self, mock_macro):
        mock_macro.get_macro_params.side_effect = RuntimeError("API down")

        p = _make_mock_p(I=1, M=1)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with patch("ogcore.demographics.get_pop_objs") as mock_demog:
                mock_demog.side_effect = RuntimeError("skip")
                c = Calibration(p, update_from_api=True)

        macro_warnings = [x for x in w if "Macro params" in str(x.message)]
        assert len(macro_warnings) == 1

        d = c.get_dict()
        assert "g_y_annual" not in d
        assert "initial_debt_ratio" not in d

    @patch("ogphl.calibrate.io")
    @patch("ogphl.calibrate.macro_params")
    def test_sam_failure_warns_and_omits(self, mock_macro, mock_io):
        mock_macro.get_macro_params.return_value = {"g_y_annual": 0.01}
        mock_io.get_alpha_c.side_effect = RuntimeError("SAM unavailable")
        mock_io.get_io_matrix.side_effect = RuntimeError("SAM unavailable")

        p = _make_mock_p(I=5, M=4)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with patch("ogcore.demographics.get_pop_objs") as mock_demog:
                mock_demog.side_effect = RuntimeError("skip")
                c = Calibration(p, update_from_api=True)

        assert len([x for x in w if "alpha_c" in str(x.message)]) == 1
        assert len([x for x in w if "io_matrix" in str(x.message)]) == 1

        d = c.get_dict()
        assert "alpha_c" not in d
        assert "io_matrix" not in d
        assert d["g_y_annual"] == 0.01

    @patch("ogphl.calibrate.macro_params")
    def test_demographics_failure_warns_and_omits(self, mock_macro):
        mock_macro.get_macro_params.return_value = {"g_y_annual": 0.01}

        p = _make_mock_p(I=1, M=1)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with patch("ogcore.demographics.get_pop_objs") as mock_demog:
                mock_demog.side_effect = RuntimeError("UN API down")
                c = Calibration(p, update_from_api=True)

        assert len([x for x in w if "Demographics" in str(x.message)]) == 1

        d = c.get_dict()
        assert "e" not in d
        assert "omega" not in d
        assert "omega_SS" not in d
        assert d["g_y_annual"] == 0.01
        assert "alpha_c" in d
        assert "io_matrix" in d
