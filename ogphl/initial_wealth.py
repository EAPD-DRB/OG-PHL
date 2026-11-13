"""
The initial distribution of household wealth across ages and lifetime-income
groups, OG-Core's ``initial_hhwealth_dist``.

Without it OG-Core starts the transition from the steady-state profile of
wealth by age, scaled to the aggregate anchor ``initial_wealth_ratio``. The
Philippine population is young, so hitting the aggregate scales every age up:
each household started 1.6 times richer than its steady-state counterpart
and the older ones consumed the windfall.

The age shape here is the Philippines' National Transfer Accounts private
asset income per person by age, latest year (2015; fetched by
``scripts/fetch_nta_age_profiles.py``), which traces wealth by age when the
return on assets does not vary much with age. Within each age, wealth across
lifetime-income groups keeps the model's own steady-state pattern (from the
shipped warm-start seed), since no Philippine survey reports wealth by
lifetime income. The level stays with ``initial_wealth_ratio``.

    python -m ogphl.initial_wealth

writes the matrix into the packaged parameters.
"""

import csv
import json
import os
import pickle

import numpy as np

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
JSON_PATH = os.path.join(CUR_PATH, "ogphl_default_parameters.json")
NTA_PATH = os.path.join(CUR_PATH, "data", "nta_private_asset_income_PHL.csv")
SEED_PATH = os.path.join(CUR_PATH, "data", "ss_warm_start.pkl")


def asset_income_by_age(ages, path=NTA_PATH):
    """
    NTA private asset income per person (smooth mean) at single ages, in the
    latest year. Ages beyond the last reported age take its value; negative
    values (net debtors among the young) are set to zero.

    Args:
        ages (array_like): ages in years
        path (str): CSV written by scripts/fetch_nta_age_profiles.py

    Returns:
        income (Numpy array): asset income per person at each age
        year (int): the NTA year used
    """
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    row = max(rows, key=lambda r: int(r["Year"]))
    values = []
    for age in range(0, 111):
        v = row.get(f"Age{age}", "")
        values.append(float(v) if v not in ("", None) else np.nan)
    values = np.array(values)
    last = int(np.max(np.where(~np.isnan(values))[0]))
    ages = np.minimum(np.asarray(ages), last)
    return np.maximum(values[ages], 0.0), int(row["Year"])


def initial_hhwealth_dist(omega0, b_ss, E):
    """
    Shares of initial aggregate household wealth by age and lifetime-income
    group.

    Row s holds the savings that households of age s carry into the first
    model period, so it takes the asset income of age s + 1.

    Args:
        omega0 (Numpy array): population distribution in the first period,
            size (S, J)
        b_ss (Numpy array): steady-state savings by age and group,
            ``b_sp1``, size (S, J)
        E (int): age at which households become economically active

    Returns:
        dist (Numpy array): size (S, J), summing to one
    """
    S, _ = b_ss.shape
    ages = np.arange(E + 1, E + S + 1)
    age_shape, _ = asset_income_by_age(ages)
    w = omega0 / omega0.sum(axis=1, keepdims=True)
    mean_b = (b_ss * w).sum(axis=1, keepdims=True)
    within = np.where(mean_b > 0, b_ss / np.maximum(mean_b, 1e-300), 1.0)
    wealth = omega0 * age_shape[:, None] * within
    return wealth / wealth.sum()


def main():
    with open(JSON_PATH, encoding="utf-8") as f:
        params = json.load(f)
    with open(SEED_PATH, "rb") as f:
        seed = pickle.load(f)
    omega0 = np.array(params["omega"])[0]
    # one model period per year of age, so E is the starting age
    E = int(params.get("starting_age", 20))
    dist = initial_hhwealth_dist(omega0, seed["b"], E)
    params["initial_hhwealth_dist"] = [
        [round(float(x), 10) for x in row] for row in dist
    ]
    # rounding can leave the sum a hair off one; put the residual on the
    # largest cell so OG-Core's sum-to-one check passes
    arr = np.array(params["initial_hhwealth_dist"])
    i, j = np.unravel_index(arr.argmax(), arr.shape)
    params["initial_hhwealth_dist"][i][j] = round(
        float(arr[i, j] + 1.0 - arr.sum()), 10
    )
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=4)
        f.write("\n")
    _, year = asset_income_by_age([40])
    print(f"wrote initial_hhwealth_dist (NTA {year} age shape) to {JSON_PATH}")


if __name__ == "__main__":
    main()
