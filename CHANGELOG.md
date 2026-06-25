# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- SAM-derived per-industry capital share via `input_output.get_gamma()`, with an optional `target_avg` that rescales the shares (value-added weighted) to an economy-wide level, correcting the upward bias from self-employed mixed income in the raw SAM. The `Calibration` class now overlays `gamma` for multi-industry (`M > 1`) runs.
- Eight-industry production split: `constants.PROD_DICT` separates the former Utilities sector into Electricity and Water (Manufacturing stays last as the OG-Core numeraire / investment-good producer).
- `input_output.get_io_matrix_value_added()`: builds the `io_matrix` as the domestic value-added content of each consumption good by industry (input-output / Leontief inverse), with imported content netted out and rows renormalized. This traces the full domestic supply chain and is the construction the `Calibration` class and the example now use; the previous direct intermediate-use `get_io_matrix` is retained as a comparison baseline. It correctly attributes consumption to producing industries — e.g. household energy spending is ~74% electricity rather than ~54% manufacturing.
- `examples/run_og_phl_multi_industry_calibrated.py`: a SAM-calibrated multi-industry (M=8, I=5) example that solves the steady state by gamma continuation (homotopy) and prints a validation report.
- Packaged the multi-industry calibration as a static artifact. `ogphl/ogphl_multisector_default_parameters.json` holds the computed M=8 overlay (`M`, `I`, `alpha_c`, `io_matrix`, `gamma`, `epsilon`, `gamma_g`, `Z`, `c_min`, `cit_rate`, `tau_c`), and `ogphl/create_multisector_calibration.py` is the tool that regenerates it from the underlying data (`uv run python -m ogphl.create_multisector_calibration`) — run rarely, since calibration is a rare event. The example now *loads* this JSON and solves, rather than recomputing the calibration at run time; the `input_output` construction functions remain as the (tool-only) machinery. A test asserts the committed JSON stays in sync with the builder.
- `input_output.get_Z()` and `input_output.get_employment()`: construct per-industry total factor productivity `Z_m` as the Solow residual of OG-Core's production technology `Y_m / (K_m**gamma_m * K_g**gamma_g * L_m**(1-gamma_m-gamma_g))`, normalized so Manufacturing (the numeraire) is 1. Public capital `K_g` is one aggregate stock shared by every industry, so its term cancels under the normalization and only `gamma_g`'s effect on the labor exponent enters (callers pass the model's `gamma_g`, 0.05). Employment comes from the packaged PSA Labor Force Survey series (`data/employment_by_psic_section.csv`, by PSIC section, 2012–2024); capital is allocated across industries by capital-income share with the national level anchored to the Penn World Table 10.01 capital-output ratio. The literal PIDS/Cororaton route (distributing investment by establishment-survey GAFA shares) was evaluated and rejected, because the surveys omit informal capital and invert the productivity ranking. The example now calibrates `Z` and morphs it alongside `gamma` along the continuation (the flat-`gamma` anchor only has `p_m = 1` when `Z` is homogeneous too), and documents that the high Manufacturing nominal-output share (numeraire absorbs all investment + net capital outflows) and foreign-capital share are structural open-economy features, not Z artifacts (confirmed by a Z=1 control).

### Changed

- Recalibrated the open-economy block to Philippine data, in `ogphl_default_parameters.json`. Capital openness `zeta_K` 0.9 → 0.4 (normalized Chinn-Ito index; the old value implied a ~96% foreign-owned capital stock vs. the ~20% in the BSP International Investment Position, and also kept domestic capital so thin that the transition path failed the resource constraint). World interest rate `world_int_rate_annual` 0.04 → 0.05, adding a ~100 bp Philippine sovereign country-risk premium to the global risk-free rate. Steady-state debt target `debt_ratio_ss` 1.10 → 0.60, matching the Philippine debt-to-GDP ratio (and the model's initial ratio) instead of the US-style placeholder. These are economy-wide values, so they live in the base JSON and the single- and multi-industry models both inherit them; the macro calibration chapter documents the anchors. The multi-industry overlay now only carries the TPI dampening `nu` = 0.2 it needs on top of the base.

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
