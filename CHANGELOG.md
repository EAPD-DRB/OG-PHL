# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Require `ogcore>=0.18.0` and migrate the calibration to its income-group-varying demographics (PSLmodels/OG-Core#1165): the packaged demographic arrays (`omega`, `omega_SS`, `rho`, `imm_rates` and their preTP seeds) are regenerated in the new age-by-income shape with `update_baseline_demographics` (macro and industry parameters untouched, enforced by the tool's clobber guard), and both `get_pop_objs` call sites pass `income_percentiles=p.lambdas` as 0.18 requires (from PR #78). OG-PHL's demographics do not vary by income group, so the new arrays are the old ones spread across groups by `lambdas`: the age distribution and the regenerated earnings matrix reproduce the previous values to machine precision, and model results are unchanged. `income.get_e_interp` now reads the OG-USA snapshot's raw JSON values instead of loading them through a `Specifications` object, which decouples it from the installed ogcore's array schema (the 0.18 schema rejects OG-USA's not-yet-migrated shapes) and accepts age weights in either the 1-D or the new age-by-income shape.

### Added

- Enabled a debt-elastic sovereign premium in `ogphl_default_parameters.json`, the crowding-out-via-risk channel that OG-Core's defaults and the other country calibrations leave off (`r_gov_DY = r_gov_DY2 = 0`). It is a *centered* convex form, `r_gov_DY2 * (D/Y - 0.6)^2`, flat at the 0.60 debt target and steepening only as debt rises away — `r_gov_DY2 = 0.04`, `r_gov_DY = -0.048`, with `r_gov_shift` recentered from -0.0338 to -0.0482 so the premium is exactly zero at the target and the steady state is unchanged. This matches Philippine experience (stable spreads at 40-70% debt, blowouts only at 1980s-crisis levels). See the macro calibration chapter for the lineage and sources.
- `ogphl/update_baseline.py`: regenerates the packaged single-industry JSON from the live calibration (UN demographics, World Bank `g_y_annual`), so the offline default reproduces the connected run (`uv run python -m ogphl.update_baseline`). The packaged values are refreshed with it.

### Changed

- Require `ogcore>=0.16.3` and Python 3.12+ (ogcore 0.16.3 supports Python 3.12-3.13). The floor keeps the packaged parameters and the installed ogcore from drifting apart: the demographic seed parameters below do not exist in older ogcore schemas.
- Regenerated the packaged baseline demographics under ogcore 0.16.3, whose demographics rework (PSLmodels/OG-Core#1073) realigns the transition arrays by one period and adds the period-0 seeds `g_n_preTP`, `imm_rates_preTP`, and `rho_preTP` that the aggregation code now uses. Macro and industry parameters are unchanged.
- Recalibrated the open-economy block to Philippine data, in `ogphl_default_parameters.json`. Capital openness `zeta_K` 0.9 -> 0.4 (normalized Chinn-Ito index; the old value implied a ~96% foreign-owned capital stock vs. the ~20% in the BSP International Investment Position, and also kept domestic capital so thin that the transition path failed the resource constraint). World interest rate `world_int_rate_annual` 0.04 -> 0.05, adding a ~100 bp Philippine sovereign country-risk premium to the global risk-free rate. Steady-state debt target `debt_ratio_ss` 1.10 -> 0.60, matching the Philippine debt-to-GDP ratio (and the model's initial ratio) instead of the US-style placeholder. These are economy-wide values, so they live in the base JSON and the single- and multi-industry models both inherit them; the macro calibration chapter documents the anchors.
- Macro parameters are no longer clobbered by wrong-source API pulls: `get_macro_params` now refreshes only `g_y_annual` (World Bank, its documented source). The IMF GFS pull for `alpha_T`/`alpha_G` is removed — the Philippine central-government social-benefit series it differenced are zero, which set `alpha_T = 0` and made the steady-state solve divide by zero — as are the World Bank external-debt pull for `initial_foreign_debt_ratio`/`zeta_D` and the ILOSTAT `gamma` and `r_gov_*` overrides; those parameters are held at their documented values in the packaged JSON.
- Retuned the packaged steady-state initial guesses to the recalibrated economy (`initial_guess_r_SS` 0.048 -> 0.0708, `initial_guess_TR_SS` 0.35 -> 0.1289, `initial_guess_factor_SS` 153064 -> 179355). The old values pointed at the pre-recalibration steady state; starting that far away, the solver either crawled through ogcore's initial-guess sweep or exhausted it without converging, which is what kept breaking the example run. From the retuned guesses the baseline steady state solves in seconds. The recalibrated steady state they encode: r = 0.0708, w = 2.760, debt-to-GDP exactly at the 0.60 target, and a 26% foreign-owned capital share — against ~20% in the BSP International Investment Position, where the old calibration implied ~96%.

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
