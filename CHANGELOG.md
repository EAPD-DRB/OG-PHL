# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- SAM-derived per-industry capital share via `input_output.get_gamma()`, with an optional `target_avg` that rescales the (value-added-weighted) shares, correcting the upward bias from self-employed mixed income in the raw SAM. The multi-industry calibration rescales to the economy-wide *total* capital share (`constants.TOTAL_CAPITAL_SHARE`) and then subtracts public capital's share (`PUBLIC_CAPITAL_SHARE`) to leave the private share `gamma_m`, so public capital is carved out of capital rather than labor and the economy-wide labor share matches the national accounts. The calibration builder and the `Calibration` class (`M > 1`) import those shared constants and apply the same construction, so they cannot drift.
- Eight-industry production split: `constants.PROD_DICT` separates the former Utilities sector into Electricity and Water (Manufacturing stays last as the OG-Core numeraire / investment-good producer).
- `input_output.get_io_matrix_value_added()`: builds the `io_matrix` as the domestic value-added content of each consumption good by industry (input-output / Leontief inverse), with imported content netted out and rows renormalized. This traces the full domestic supply chain and is the construction the `Calibration` class and the example now use; the previous direct intermediate-use `get_io_matrix` is retained as a comparison baseline. It correctly attributes consumption to producing industries — e.g. household energy spending is ~74% electricity rather than ~54% manufacturing.
- `examples/run_og_phl_multi_industry_calibrated.py`: a SAM-calibrated multi-industry (M=8, I=5) example that solves the steady state by gamma continuation (homotopy) and prints a validation report.
- Packaged the multi-industry calibration as a static overlay artifact. `ogphl/ogphl_multisector_default_parameters.json` contains only the parameters the multi-industry calibration changes (`M`, `I`, `alpha_c`, `io_matrix`, `c_min`, `gamma`, `epsilon`, `gamma_g`, `Z`, the units-converted `chi_b`/`chi_n`, and the dampening `nu`); the example loads the single-industry base `ogphl_default_parameters.json` first and applies the overlay on top, so everything economy-wide (demographics, earnings, tax functions, the fiscal and open-economy blocks, solver seeds) is inherited from the base at load time and a base recalibration flows into the multi-industry model with nothing to regenerate. `ogphl/create_multisector_calibration.py` regenerates the overlay from the underlying data (`uv run python -m ogphl.create_multisector_calibration`) — run rarely, since calibration is a rare event. The example *loads* the JSONs and solves, rather than recomputing the calibration at run time; the `input_output` construction functions remain as the (tool-only) machinery. Tests assert the committed file carries exactly the whitelisted overlay keys (it can neither silently fatten into a full parameter set nor thin below what the example needs), stays in sync with the builder, and — applied on the base — yields a coherent M=8 parameter set with the base's economy-wide values intact.
- `input_output.get_Z()` and `input_output.get_employment()`: construct per-industry total factor productivity `Z_m` as the Solow residual of OG-Core's production technology `Y_m / (K_m**gamma_m * K_g**gamma_g * L_m**(1-gamma_m-gamma_g))`, normalized so Manufacturing (the numeraire) is 1. Public capital `K_g` is one aggregate stock shared by every industry, so its term cancels under the normalization and only `gamma_g`'s effect on the labor exponent enters (callers pass the model's `gamma_g`, 0.05). Employment comes from the packaged PSA Labor Force Survey series (`data/employment_by_psic_section.csv`, by PSIC section, 2012–2024); capital is allocated across industries by capital-income share with the national level anchored to the Penn World Table 10.01 capital-output ratio. The literal PIDS/Cororaton route (distributing investment by establishment-survey GAFA shares) was evaluated and rejected, because the surveys omit informal capital and invert the productivity ranking. The example now calibrates `Z` and morphs it alongside `gamma` along the continuation (the flat-`gamma` anchor only has `p_m = 1` when `Z` is homogeneous too), and documents that the high Manufacturing nominal-output share (numeraire absorbs all investment + net capital outflows) and foreign-capital share are structural open-economy features, not Z artifacts (confirmed by a Z=1 control).
- The multisector calibration converts the utility weights `chi_b` and `chi_n` for the multi-good composite-consumption units. OG-Core's composite price index is unnormalized (`p_tilde = prod(((1+tau_c) p_i / alpha_i)**alpha_i)`), so moving from one consumption good to five shrinks the units of composite consumption by `k = prod(alpha_i**-alpha_i)` — about 2.97 for the Philippine basket — while the fixed utility weights, set in single-industry units, do not follow. Households then behave as if they cared less about bequests and minded work less: saving falls (B/Y 2.4 vs the single-industry 3.7), foreign capital fills the gap (K_f/K 0.53 vs 0.26), and r rises (0.089 vs 0.071) — a units artifact, not economics. Scaling both weights by `k**(sigma-1)` (1.723 at sigma = 1.5) is the exact FOC-preserving conversion — derived, not fitted — and closes 44-80% of each gap (r 0.081, K_f/K 0.34, B/Y 3.3, K/Y 4.24 vs the single-industry 4.29); the residuals are genuine composition effects of the multi-good basket. The conversion is computed in the builder from `alpha_c`, so it regenerates with the consumption shares; the base JSON is untouched. A common Z-level rescale was tested and rejected: it moves r the wrong way, and the solved `factor` already matched the single-industry baseline to 0.02%, showing the income level was never misaligned.

- Enabled a debt-elastic sovereign premium in `ogphl_default_parameters.json`, the crowding-out-via-risk channel that OG-Core's defaults and the other country calibrations leave off (`r_gov_DY = r_gov_DY2 = 0`). It is a *centered* convex form, `r_gov_DY2 * (D/Y - 0.6)^2`, flat at the 0.60 debt target and steepening only as debt rises away — `r_gov_DY2 = 0.04`, `r_gov_DY = -0.048`, with `r_gov_shift` recentered from -0.0338 to -0.0482 so the premium is exactly zero at the target and the steady state is unchanged. This matches Philippine experience (stable spreads at 40–70% debt, blowouts only at 1980s-crisis levels) and, unlike a premium that bites at the target, leaves the multi-industry baseline transition well-behaved (debt peak ~1.3 and sovereign rate ~7.8% at the fiscal-adjustment hump, vs ~1.7 and ~16% for the uncentered form). See the macro calibration chapter for the lineage and sources.
- `ogphl/update_baseline.py`: regenerates the packaged single-industry JSON from the live calibration (UN demographics, World Bank `g_y_annual`), so the offline default reproduces the connected run (`uv run python -m ogphl.update_baseline`). The packaged values are refreshed with it.

### Changed

- Require `ogcore>=0.16.3` and Python 3.12+ (ogcore 0.16.3 supports Python 3.12-3.13). The floor keeps the packaged parameters and the installed ogcore from drifting apart: the demographic seed parameters below do not exist in older ogcore schemas.
- Regenerated the packaged baseline demographics under ogcore 0.16.3, whose demographics rework (PSLmodels/OG-Core#1073) realigns the transition arrays by one period and adds the period-0 seeds `g_n_preTP`, `imm_rates_preTP`, and `rho_preTP` that the aggregation code now uses. Macro and industry parameters are unchanged.
- Recalibrated the open-economy block to Philippine data, in `ogphl_default_parameters.json`. Capital openness `zeta_K` 0.9 → 0.4 (normalized Chinn-Ito index; the old value implied a ~96% foreign-owned capital stock vs. the ~20% in the BSP International Investment Position, and also kept domestic capital so thin that the transition path failed the resource constraint). World interest rate `world_int_rate_annual` 0.04 → 0.05, adding a ~100 bp Philippine sovereign country-risk premium to the global risk-free rate. Steady-state debt target `debt_ratio_ss` 1.10 → 0.60, matching the Philippine debt-to-GDP ratio (and the model's initial ratio) instead of the US-style placeholder. These are economy-wide values, so they live in the base JSON and the single- and multi-industry models both inherit them (the multi-industry overlay deliberately omits them); the macro calibration chapter documents the anchors.
- Macro parameters are no longer clobbered by wrong-source API pulls: `get_macro_params` now refreshes only `g_y_annual` (World Bank, its documented source). The IMF GFS pull for `alpha_T`/`alpha_G` is removed — the Philippine central-government social-benefit series it differenced are zero, which set `alpha_T = 0` and made the steady-state solve divide by zero — as are the World Bank external-debt pull for `initial_foreign_debt_ratio`/`zeta_D` and the ILOSTAT `gamma` and `r_gov_*` overrides; those parameters are held at their documented values in the packaged JSON.
- Retuned the packaged steady-state initial guesses to the recalibrated economy (`initial_guess_r_SS` 0.048 -> 0.0708, `initial_guess_TR_SS` 0.35 -> 0.1289, `initial_guess_factor_SS` 153064 -> 179355). The old values pointed at the pre-recalibration steady state; starting that far away, the solver either crawled through ogcore's initial-guess sweep or exhausted it without converging, which is what kept breaking the example run. From the retuned guesses the baseline steady state solves in seconds. The recalibrated steady state they encode: r = 0.0708, w = 2.760, debt-to-GDP exactly at the 0.60 target, and a 26% foreign-owned capital share — against ~20% in the BSP International Investment Position, where the old calibration implied ~96%.

### Fixed

- Removed a duplicate `acoff` activity from the Agriculture & Fishing group in `constants.PROD_DICT` (it was double-counted when aggregating SAM activities).
- `validate_ss` in the multi-industry example reported a misleading `C/Y` (~0.07): it divided composite consumption (in consumption-good units, price `p_tilde`≈5.5) by nominal output `Y`. It is now valued consistently (`p_tilde * C / Y` ≈ 0.37, in line with the single-industry baseline); consumption was never collapsed, only the printed ratio was wrong.

## [0.1.0] - 2026-06-02 12:00:00

### Changed

- Migrated the project from conda to uv. Install with `uv sync --extra dev`; `pyproject.toml` is the single source of truth for dependencies and `uv.lock` pins exact versions.
- CI uses `astral-sh/setup-uv`, and ruff replaces black for formatting and linting (`check_format.yml` -> `check_ruff.yml`).
- Updated the README, `AGENTS.md`, and the Makefile to the uv workflow.

### Removed

- `setup.py`, `environment.yml`, and `pytest.ini` (their settings moved into `pyproject.toml`).

## [0.0.15] - 2026-01-14 22:00:00

### Added

- the initial values `initial_guess_r_SS`, `initial_guess_TR_SS`, and `initial_guess_factor_SS` in `ogphl_default_parameters.json` in order to make the steady-state in the baseline solve faster.
- Adds 5-day training files to documentation

## [0.0.14] - 2026-01-05 12:00:00

### Added

- Updates the remittances default calibration values in `ogphl_default_parameters.json`
- Updates the initial values `initial_guess_r_SS`, `initial_guess_TR_SS`, and `initial_guess_factor_SS` in `ogphl_default_parameters.json` in order to make the steady-state in the baseline solve faster.
- Updates the `ogcore` package requirement in `environment.yml` and `setup.py` to `ogcore>=0.14.5`
- Updates the `RC_TPI=0.01` temporarily.

## [0.0.13] - 2025-08-15 21:00:00

### Added

- Updates for Python 3.13 compatibility
- Removes the deprecated `initial_guess_w_SS` parameter from the default parameters file

## [0.0.12] - 2025-06-18 12:00:00

### Added

- Updates the `.gitignore` file to ignore output from the `run_og_phl_multi_industry.py` example script in the `/OG-PHL-MultiExample/` directory
- Updates calibration in `ogphl_default_parameters.json` for `alpha_G`, `debt_ratio_ss`, `alpha_RM_1`, `alpha_RM_T`, `g_RM`, `gamma`, and `gamma_g`
- Updates the corresponding documentation in `households.md`, `firms.md`, and `government.md`
- Fixes a missing equation reference in `taxes.md` and changes it to a footnote, and adds footnote section heading in `demographics.md`
- Updates the Python range in `environment.yml`
- Updates the `python_requires` range in `setup.py` to between 3.11 and 3.12

## [0.0.11] - 2025-06-12 12:30:00

### Added

- Updates `environment.yml` to pin to `paramtools` version >= 0.20.0

## [0.0.10] - 2025-04-25 12:30:00

### Added

- Updates `environment.yml` to pin to `marshmallow` version < 4.0.0
- Removes unused imports in example scripts

## [0.0.9] - 2025-02-11 16:30:00

### Added

- Added `import setuptools` to `publish_to_pypi.yml`

## [0.0.8] - 2025-02-11 14:00:00

### Added

- Updated Python 3.12 in GH Actions
- Replaced miniforge and mambaforge with miniconda and "latest" in `deploy_docs.yml` and `docs_check.yml`
- Updated Python 3.11 and 3.12 in `README.md`
- Adds `PSL_Catalog.json`

## [0.0.7] - 2024-12-06 11:00:00

### Added

- Testing on Python 3.12
- Updated local currency units in `constants.py`

## [0.0.6] - 2024-10-24 11:00:00

### Added

- Updated `alpha_G` and `alpha_I`

## [0.0.5] - 2024-10-20 22:00:00

### Added

- Updated Frisch elasticity of labor supply parameter value to 0.25
- Added multi industry example run script

## [0.0.4] - 2024-10-20 22:00:00

### Added

- Added UN tutorial section to documentation
- Updated some Sphinx packages in `environment.yml`

## [0.0.3] - 2024-08-11 12:00:00

### Added

- Updates the calibration of `OG-PHL`
- Updates the documentation

## [0.0.0] - 2024-06-20 12:00:00

### Added

- This version is a pre-release alpha. The example run script `OG-PHL/examples/run_og_phl.py` runs, but the model is not currently calibrated to represent the Philippines economy and population.


[0.1.0]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.15...v0.1.0
[0.0.15]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.14...v0.0.15
[0.0.14]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.13...v0.0.14
[0.0.13]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.12...v0.0.13
[0.0.12]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.11...v0.0.12
[0.0.11]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.10...v0.0.11
[0.0.10]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.9...v0.0.10
[0.0.9]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.8...v0.0.9
[0.0.8]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.7...v0.0.8
[0.0.7]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.6...v0.0.7
[0.0.6]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.4...v0.0.6
[0.0.5]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.0.0...v0.0.3
