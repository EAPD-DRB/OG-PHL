"""
Tests of update_baseline.py module.

The regeneration tool overlays the live calibration onto the packaged JSON.
These tests stub the calibration so no network or model solve is involved.
"""

import json

import numpy as np

from ogphl import update_baseline


def test_jsonable_converts_numpy_types():
    assert update_baseline._jsonable(np.float64(1.5)) == 1.5
    assert update_baseline._jsonable(np.int64(3)) == 3
    assert update_baseline._jsonable(np.array([1.0, 2.0])) == [1.0, 2.0]
    assert update_baseline._jsonable([np.float64(0.5), 2]) == [0.5, 2]
    assert update_baseline._jsonable((np.int64(1),)) == [1]
    assert update_baseline._jsonable("text") == "text"


def test_main_bakes_live_overlay_into_json(monkeypatch, tmp_path):
    packaged = {"g_y_annual": 0.01, "alpha_T": [0.0448], "S": 80}
    path = tmp_path / "params.json"
    path.write_text(json.dumps(packaged))

    class FakeSpecs:
        def update_specifications(self, params):
            self.params = params

    class FakeCalibration:
        def __init__(self, p, update_from_api=False):
            assert update_from_api is True

        def get_dict(self):
            return {
                "g_y_annual": np.float64(0.037),
                "omega": np.array([[0.5, 0.5]]),
            }

    monkeypatch.setattr(update_baseline, "JSON_PATH", str(path))
    monkeypatch.setattr(
        update_baseline, "Specifications", lambda baseline=True: FakeSpecs()
    )
    monkeypatch.setattr(update_baseline, "Calibration", FakeCalibration)

    update_baseline.main()

    out = json.loads(path.read_text())
    # live overlay values are baked in, as plain JSON types
    assert out["g_y_annual"] == 0.037
    assert out["omega"] == [[0.5, 0.5]]
    # documented values not in the overlay are untouched
    assert out["alpha_T"] == [0.0448]
    assert out["S"] == 80
