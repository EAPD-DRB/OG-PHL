"""Regenerate ONLY the demographic parameters in the packaged base
``ogphl_default_parameters.json`` under the installed ogcore.

Regeneration is a rare event: run this after bumping ogcore across a
demographics-convention change (e.g. ogcore 0.16.3 / PSLmodels/OG-Core#1073,
which shifts the transition-path arrays by one period and adds the period-0
seeds ``g_n_preTP``/``rho_preTP``/``imm_rates_preTP``). It calls the same
``get_pop_objs`` that ``ogphl.calibrate`` uses (UN data, with the cached
GitHub-mirror fallback, so no API token is required) and writes back
ONLY the demographic keys plus the demographics-derived earnings profile ``e``.

Everything else in the JSON -- the documented macro constants, the industry
capital shares, tax parameters -- is left byte-for-byte unchanged: a clobber
guard aborts the write if any non-demographic key would differ. Macro
parameters are documented constants (see ``ogphl.macro_params`` and the
calibration docs), NOT pulled from live APIs, so they are deliberately not
touched here.

    python -m ogphl.update_baseline_demographics
"""

import json

from importlib.resources import files

import numpy as np

from ogcore import demographics
from ogcore.parameters import Specifications

from ogphl import income
from ogphl.calibrate import UN_COUNTRY_CODE

# Demographic keys returned by get_pop_objs, plus the derived earnings profile
# and the remittance growth path (derived from g_n -- see flat_share_g_RM).
# Only these are rewritten; anything else is a clobber and blocks the write.
_DERIVED = "e"
_DERIVED_RM = "g_RM"
_DERIVED_ETA_RM = "eta_RM"

# Share of total remittance VALUE received by each per-capita income quintile.
# Average of FIES 2000/2003/2006, computed from Ang, Sugiyarto & Jha (ADB
# Economics WP 188), Table 4: quintile mean income x remittance share of
# income (quintiles hold equal family counts, so relative value follows
# directly). The gradient cross-validates against FIES 2018 (ADB WP 714,
# Fig. 1): remittance share of income among receiving households rises
# 16% -> 31% from bottom to top quintile.
RM_QUINTILE_VALUE_SHARES = [0.00523, 0.02020, 0.06313, 0.18667, 0.72483]


def remittance_eta(omega_SS, lambdas):
    """Allocation matrix eta_RM distributing aggregate remittances across
    households, shaped (S, J) as the parameter schema requires (ogcore tiles
    it over time; each group's total share is exact in every period).

    The lifetime-income-group split comes from mapping the FIES quintile
    value shares onto the model's J groups, assuming a uniform density of
    remittance value within each quintile (conservative at the top: the top
    quintile's share is spread evenly across its percentiles, which
    understates concentration within the top 1%). Within a group, remittances
    are spread per capita across ages -- the surveys say nothing about the
    age profile of receipt. ogcore's default is population-proportional
    everywhere (each group receives exactly its population share), which the
    Philippine data reject: the top quintile receives ~72% of remittance
    value, not 20%.
    """
    omega_SS = np.asarray(omega_SS, dtype=float)
    lambdas = np.asarray(lambdas, dtype=float).flatten()
    q = np.asarray(RM_QUINTILE_VALUE_SHARES, dtype=float)
    q = q / q.sum()
    # Cumulative remittance value at each population percentile (uniform
    # within quintile), evaluated at the lambdas group boundaries.
    cum_pop = np.concatenate([[0.0], np.cumsum(np.full(q.size, 1 / q.size))])
    cum_val = np.concatenate([[0.0], np.cumsum(q)])
    bounds = np.concatenate([[0.0], np.cumsum(lambdas)])
    group_share = np.diff(np.interp(bounds, cum_pop, cum_val))
    group_share = group_share / group_share.sum()
    # eta[s, j] = group share x age-population share within the group, so
    # every household in group j receives the same amount and the group total
    # is its data share (sum_s omega_SS[s, j] = lambdas[j]).
    within = omega_SS / omega_SS.sum(axis=0, keepdims=True)
    return within * group_share.reshape(1, -1)


def flat_share_g_RM(g_y, g_n):
    """Remittance growth path holding aggregate remittances at a fixed share
    of GDP.

    ``aggregates.get_RM`` advances detrended remittances by the factor
    ``(1 + g_RM[t]) / (exp(g_y) * (1 + g_n[t-1]))``, so ``RM/Y`` holds at
    ``alpha_RM`` only when that factor is 1. Setting ``alpha_RM_1 ==
    alpha_RM_T`` is NOT sufficient on its own: with any other ``g_RM`` the
    ratio drifts away from the calibrated share over the first ``tG2``
    periods and only returns afterwards. ``g_n`` varies over the transition,
    so no single scalar can hold the share flat -- the path has to track it.
    """
    g_n = np.asarray(g_n, dtype=float)
    g_RM = np.exp(g_y) * (1.0 + np.roll(g_n, 1)) - 1.0
    g_RM[0] = np.exp(g_y) * (1.0 + g_n[0]) - 1.0  # unused by get_RM; kept sane
    return g_RM


def regenerate():
    """Return the demographic overlay {key: jsonable} regenerated under the
    installed ogcore, matching ogphl.calibrate's get_pop_objs calls."""
    json_path = files("ogphl").joinpath("ogphl_default_parameters.json")
    before = json.loads(json_path.read_text())

    # Bootstrap: across an ogcore demographics-convention change the packaged
    # arrays still have the PREVIOUS ogcore's shapes, which the installed
    # schema rejects -- and they are exactly the keys being regenerated.
    # Load the base without them; the tool only needs the non-demographic
    # scalars (E, S, T, J, lambdas, start_year) to drive the regeneration.
    demog_keys = {
        "omega",
        "omega_SS",
        "omega_S_preTP",
        "rho",
        "rho_preTP",
        "imm_rates",
        "imm_rates_preTP",
        "g_n",
        "g_n_ss",
        "g_n_preTP",
        _DERIVED,
        _DERIVED_RM,
        _DERIVED_ETA_RM,
    }
    p = Specifications()
    p.update_specifications(
        {k: v for k, v in before.items() if k not in demog_keys}
    )  # single-sector base (M=1, I=1)

    pop = demographics.get_pop_objs(
        p.E,
        p.S,
        p.T,
        0,
        99,
        country_id=UN_COUNTRY_CODE,
        initial_data_year=p.start_year - 1,
        final_data_year=p.start_year + 1,
        income_percentiles=p.lambdas.flatten(),
        GraphDiag=False,
    )
    demog80 = demographics.get_pop_objs(
        20,
        80,
        p.T,
        0,
        99,
        country_id=UN_COUNTRY_CODE,
        initial_data_year=p.start_year - 1,
        final_data_year=p.start_year + 1,
        income_percentiles=p.lambdas.flatten(),
        GraphDiag=False,
    )
    e = income.get_e_interp(p.E, p.S, p.J, p.lambdas, demog80["omega_SS"])

    def _jsonable(v):
        return v.tolist() if hasattr(v, "tolist") else v

    overlay = {k: _jsonable(v) for k, v in pop.items()}
    overlay[_DERIVED] = _jsonable(e)
    # Remittances are calibrated as a constant share of GDP, and that share is
    # only held if g_RM tracks the regenerated g_n -- so it is rewritten here
    # rather than left to go stale against new demographics.
    overlay[_DERIVED_RM] = _jsonable(flat_share_g_RM(p.g_y, pop["g_n"]))
    # The remittance allocation matrix is omega-derived (per-capita within
    # lifetime-income groups), so it too is rebuilt with the demographics.
    overlay[_DERIVED_ETA_RM] = _jsonable(
        remittance_eta(pop["omega_SS"], p.lambdas)
    )
    return json_path, before, overlay


def main():
    json_path, before, overlay = regenerate()
    after = dict(before)
    after.update(overlay)

    overlay_keys = set(overlay)
    clobbered = [
        k
        for k in before
        if k not in overlay_keys and after.get(k) != before.get(k)
    ]
    added = sorted(set(after) - set(before))
    print(f"demographic keys written: {sorted(overlay_keys)}")
    print(f"new keys added: {added}")
    print(f"non-demographic keys clobbered (must be []): {clobbered}")
    assert not clobbered, "clobber guard tripped -- refusing to write"

    json_path.write_text(json.dumps(after, indent=4) + "\n")
    print(f"wrote {json_path}")


if __name__ == "__main__":
    main()
