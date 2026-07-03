"""
Regenerate the packaged single-industry default-parameter JSON.

Runs the OG-PHL ``Calibration`` with ``update_from_api=True`` and writes the
overlay back into ``ogphl_default_parameters.json`` so an offline run
(``update_from_api=False``) reproduces the connected calibration. The overlay
is the live data OG-PHL sources from APIs:

  * demographics from the UN (with the ogcore 0.16.3 preTP seeds),
  * the earnings profile ``e`` (derived from those demographics),
  * ``g_y_annual`` from the World Bank (pre-pandemic per-capita growth).

Documented, non-API macro parameters (``alpha_T``, ``alpha_G``, the
open-economy block, ``gamma``, ``r_gov_*`` ...) are held in the JSON and left
unchanged; see ``ogphl.macro_params`` and the calibration docs.

Usage::

    uv run python -m ogphl.update_baseline
"""

import json
import os

import numpy as np

from ogcore.parameters import Specifications
from ogphl.calibrate import Calibration

JSON_PATH = os.path.join(
    os.path.dirname(__file__), "ogphl_default_parameters.json"
)


def _jsonable(value):
    """Convert numpy scalars/arrays to plain JSON-serializable types."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def main():
    with open(JSON_PATH) as f:
        params = json.load(f)

    p = Specifications(baseline=True)
    p.update_specifications(params)
    overlay = Calibration(p, update_from_api=True).get_dict()

    for key, value in overlay.items():
        params[key] = _jsonable(value)

    with open(JSON_PATH, "w") as f:
        json.dump(params, f, indent=4)
        f.write("\n")

    print(
        f"Wrote {os.path.basename(JSON_PATH)} "
        f"({len(params)} params); overlaid from live calibration: "
        f"{sorted(overlay.keys())}"
    )


if __name__ == "__main__":
    main()
