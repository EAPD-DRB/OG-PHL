"""
Import smoke tests for installed package usage.
"""

import json
import importlib.resources


def test_import_smoke():
    import ogphl
    from ogphl import macro_params
    from ogphl.calibrate import Calibration

    assert ogphl is not None
    assert macro_params is not None
    assert Calibration is not None


def test_packaged_data_available():
    """Packaged data files load from the installed wheel."""
    from ogphl import input_output

    sam = input_output.read_SAM()
    assert sam is not None

    with importlib.resources.open_text(
        "ogphl", "ogphl_default_parameters.json"
    ) as f:
        defaults = json.load(f)
    assert isinstance(defaults, dict)
