"""
Steady-state tuning script for OG-PHL calibration work.

Loads the packaged JSON plus an optional overrides file, solves the steady
state with the same worker pool as examples/run_og_phl.py, and prints the
calibration dashboard: each moment, model against the data target in
ogphl/targets.py.

It sets dials and nothing more. Fold settled values into the packaged JSON,
commit, re-install, and take every reported number from run_og_phl.py.

    python examples/tune_ss.py [overrides.json] [--label NAME]
                               [--warm SS_vars.pkl] [--tpi]

Without --warm the solve starts from the shipped seed, as the example does
(ogphl/warm_start.py). --warm starts it from any solved steady state for
nearby parameters instead; use it while moving parameters far from the
seed's. --tpi also solves the baseline transition path and prints the
first-period moments the discount factor and the foreign-capital share are
tuned to (ogphl/targets.py, TRANSITION_TARGETS).
"""

import argparse
import importlib.resources
import json
import multiprocessing
import os
import time

import pickle

import numpy as np
from distributed import Client
from ogcore.execute import runner
from ogcore.parameters import Specifications
from ogcore.utils import safe_read_pickle

from ogphl.targets import (
    TARGETS,
    TRANSITION_TARGETS,
    ss_moments,
    tpi_moments,
)
from ogphl.warm_start import enable, solve_ss_from


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("overrides", nargs="?", default=None)
    ap.add_argument("--label", default="tune")
    ap.add_argument("--warm", default=None)
    ap.add_argument("--tpi", action="store_true")
    args = ap.parse_args()

    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(
        n_workers=num_workers, processes=True, threads_per_worker=1
    )

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    out = os.path.join(cur_dir, "OG-PHL-Tune", args.label)
    p = Specifications(
        baseline=True,
        num_workers=num_workers,
        baseline_dir=out,
        output_base=out,
    )
    with importlib.resources.open_text(
        "ogphl", "ogphl_default_parameters.json"
    ) as file:
        p.update_specifications(json.load(file))
    overrides = {}
    if args.overrides:
        with open(args.overrides) as f:
            overrides = json.load(f)
        p.update_specifications(overrides)
    print(f"label {args.label}; overrides {json.dumps(overrides)}")

    t0 = time.time()
    if args.warm:
        ss = solve_ss_from(p, safe_read_pickle(args.warm), client=client)
        os.makedirs(os.path.join(out, "SS"), exist_ok=True)
        with open(os.path.join(out, "SS", "SS_vars.pkl"), "wb") as f:
            pickle.dump(ss, f)
    else:
        enable()
        runner(p, time_path=args.tpi, client=client)
        ss = safe_read_pickle(os.path.join(out, "SS", "SS_vars.pkl"))
    secs = time.time() - t0
    client.close()
    if args.tpi:
        tpi = safe_read_pickle(os.path.join(out, "TPI", "TPI_vars.pkl"))
        tm = tpi_moments(tpi)
        print(f"\n{'2025 moment':22s} {'model':>8s} {'data':>8s}")
        for k, (target, src) in TRANSITION_TARGETS.items():
            print(f"{k:22s} {tm[k]:8.4f} {target:8.4f}  {src}")
        for k in sorted(set(tm) - set(TRANSITION_TARGETS)):
            print(f"{k:22s} {tm[k]:8.4f}")

    model = ss_moments(ss)
    rc = float(np.max(np.abs(ss["resource_constraint_error"])))
    print(
        f"\nSS solved in {secs:.0f} s; max |RC error| {rc:.2e}; "
        f"r {float(np.squeeze(ss['r'])):.4f}; "
        f"r_gov {float(np.squeeze(ss['r_gov'])):.4f}; "
        f"factor {float(np.squeeze(ss['factor'])):.5g}"
    )
    print(f"{'moment':18s} {'model':>8s} {'data':>8s} {'gap':>8s}  source")
    for k, (target, src) in TARGETS.items():
        v = model.get(k, np.nan)
        print(f"{k:18s} {v:8.4f} {target:8.4f} {v - target:+8.4f}  {src}")
    for k in sorted(set(model) - set(TARGETS)):
        print(f"{k:18s} {model[k]:8.4f}")
    with open(os.path.join(out, "dashboard.json"), "w") as f:
        json.dump(
            {
                "model": model,
                "transition": tpi_moments(tpi) if args.tpi else None,
                "rc": rc,
                "seconds": secs,
                "overrides": overrides,
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    main()
