# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [Unreleased]

### Changed

- Government debt contracted abroad is modelled as such, with OG-Core's `alpha_D_ext` and `r_D_ext_annual` (PSLmodels/OG-Core#1279): the Treasury's external debt, 19.36% of GDP at end-2024 (0.2103 of the model's output), at 2.44% real (its effective rate, 4.44% in 2024-2025, less 2% foreign inflation). It used to sit in market debt, where OG-Core pays foreign holders the household portfolio return (about 8% real): in 2025 the model paid 1.0% of GDP to foreigners on public debt against the 0.8% the Treasury actually paid on its external debt; now 0.62% in real terms. Market debt is the domestic debt: `initial_debt_ratio` 0.6517 -> 0.4490 (41.3% of GDP, end-2024; all debt starts at the actual 60.7%), `debt_ratio_ss` 0.6517 -> 0.4414 (the 60% anchor on all debt less the external part). `initial_foreign_debt_ratio` 0.2 -> 0.042 and `zeta_D` 0.2 -> 0.048, non-residents' share of peso government securities (BTr investor profile, end-2024 and end-2025); 0.2 was the external debt as a share of GDP, not of debt. `r_gov` is anchored to the domestic effective rate, 2.33% real (5.33% nominal in 2024-2025 less 3%), instead of 2.0% on all debt; the debt premium is evaluated at all debt and stays centred on 60%. The dashboard, the fiscal-path figure and the example's reform (65% of GDP, all debt) count market plus external debt (`targets.EXTERNAL_DEBT_SHARE`). Re-tuned on the official run: `beta_annual` 0.9027 -> 0.8981, `zeta_K` 0.1453 -> 0.1571, `r_gov_shift` -0.0149 -> -0.0185, `tau_c` 0.11287 -> 0.11174, CIT adjustment 0.7369 -> 0.7387, `p_wealth` 0.003776 -> 0.003864, `alpha_G` 0.1021/0.0996/0.0905/0.0817/0.0733 -> 0.1029/0.1002/0.0909/0.0818/0.0708. Investment and the foreign share of capital in 2025 are on target, household consumption is 76.1% (data 76.1%), the program-year primary balances are exact, and all debt is 60.0% of GDP in 2044.
- uv installs OG-Core from the integration branch of master with PSLmodels/OG-Core#1279, #1280, #1276 and #1277 (`[tool.uv.sources]`, the commit OG-ETH pins); the PyPI requirement stays `ogcore>=0.24.4`. A full run takes about 9 minutes instead of 25.

- Requires ogcore 0.24.4, the latest release. Its changes since 0.24.1 are to the notional-account and hybrid pension systems; the defined-benefit system used here is unchanged, and the steady state matches the 0.24.1 run to 1e-11.
- Initial household wealth is spread across ages from data, through OG-Core's `initial_hhwealth_dist` (`ogphl/initial_wealth.py`): the Philippines' NTA private asset income per person by age (2015, `ogphl/data/nta_private_asset_income_PHL.csv`), and within each age the model's own spread across lifetime-income groups. OG-Core otherwise stretches the steady-state age profile to the aggregate anchor, which in a young population started every household 1.6 times richer than its steady-state counterpart; consumption in the first year ran 80.8% of GDP against 76.1% in the data, concentrated among the old.
- The discount factor and the foreign-capital fill share are tuned to the first transition year instead of the steady state: `beta_annual` 0.9027 so fixed investment in 2025 is 23.6% of GDP (World Bank, 2024), and `zeta_K` 0.1453 so the foreign share of capital in 2025 is the IIP's 20%. The data describe today's young population; the steady state's capital stock (about 3.7 times GDP) and foreign share are outcomes of aging. `targets.TRANSITION_TARGETS` and `targets.tpi_moments` score these moments, and `examples/tune_ss.py --tpi` prints them. The tax dials, pension phase-in (from 80% of the mature scale) and the spending path are re-tuned to match.
- The calibration is scored against GDP at market prices. OG-Core's output excludes the consumption tax (households pay it on top of the producer price), while every Philippine target is a share of market-price GDP, so every fiscal ratio, the capital stock and the debt anchor ran 7-8% below the data on a consistent basis. `ogphl/targets.py` now divides model moments by output plus the consumption tax, and the parameters OG-Core multiplies by its own output are the data share times 1.086 (`targets.MODEL_PER_MARKET_GDP`): `alpha_T`, `alpha_G`, `alpha_I`, `alpha_RM_1`/`alpha_RM_T`, `debt_ratio_ss`, `initial_debt_ratio`, `initial_wealth_ratio` and `initial_Kg_ratio`. The debt premium on `r_gov` is re-centered on the converted target (`r_gov_DY` -0.0442, `r_gov_DY2` 0.0339). The example's reform states its 65% long-run debt target at market prices and converts it the same way.
- Capital share from the ILO's 2023 labor income share on the same basis: total capital share 0.588 -> 0.515 (`gamma` 0.538 -> 0.465, `constants.TOTAL_CAPITAL_SHARE`). The old value matched the 2015 ILO share with product taxes counted as capital income.
- Labor supply by age (`chi_n`) is calibrated to Philippine hours per person from the Labor Force Survey (ILOSTAT, 2024; `ogphl/labor.py`, ported from OG-ETH, `scripts/fetch_ilo_hours_by_age.py`) in place of OG-USA's profile, which had households working 45% of their time at every age to 55 and a third at 75. The NTA age shape of earnings is now per hour worked, so hours are not counted twice.
- Income gradients use the Demographic-Gradients library's updated conversion, `tilt / (100 x (1 - p))` with p OG-Core's own rate, and fertility differs by age (the library's pooled age offsets added to the DHS TFR tilt).
- Dials re-tuned on the corrected basis (`beta_annual`, `zeta_K`, the spending path and the pension phase-in were then re-tuned to 2025 moments, above): `beta_annual` 0.8895, `zeta_K` 0.172, `tau_c` 0.1138, `tau_payroll` 0.0623, CIT adjustment 0.7246, `p_wealth` 0.00418, `tau_bq` 0.00391, GS `phi2` 2.0265e-8, `r_gov_shift` -0.0140, mature pension scale 0.856. Every steady-state target is within 0.8%; untargeted, fixed investment is 23.9% of GDP (data 23.6%) and household consumption 77.8% (data 76.1%). The return on capital is 8.3%.
- Pensions phase in: the scale starts at 80% of the mature value in 2025 and reaches it in 2050, so outlays start at today's 2.28% of GDP (a mature system from the first year pays about 2.8%).
- `alpha_G` follows the budget's programmed primary balance for 2025-2028 (DBM BESF FY2026 Table A.2: -2.51, -2.26, -1.59, -1.03% of GDP; `ogphl/data/fiscal_program_PHL.csv`) and from 2029 the level that returns debt to 60% of GDP by 2044, when the budget rule starts. Debt stays between 57% and 62% of GDP along the path.
- The steady state starts from a shipped solved state (`ogphl/warm_start.py`, `ogphl/data/ss_warm_start.pkl`, ported from OG-ZAF; regenerate with `examples/save_warm_start.py`). OG-Core's flat starting guesses no longer solve this calibration: solved household savings are about 130 times the flat seed. `examples/tune_ss.py` takes `--warm` to start from any solved state.
- The example no longer makes live data calls. It used to re-download UN demographics, re-derive the earnings profile and refresh World Bank `g_y_annual` whenever the machine was online, so online and offline runs of the same commit could give different results. The packaged JSON is now the whole calibration; `python -m ogphl.update_baseline` is the one deliberate way to refresh the API-sourced values, as a reviewable change to the JSON. The README describes both, and drops the UN token note that no longer applies.
- Requires ogcore 0.24.1 (a released version; the lock previously pointed at a local patched build). `tau_payroll` and `alpha_db` use the nested T x J forms ogcore now requires (values unchanged). The single-industry base sets `nu = 0.2` to go with its Anderson transition solver.
- Public pensions switched on, with the SSS defined-benefit rules. The repo had switched them off (the US benefit formula's rates set to zero, undocumented) while the payroll tax collected 2.8% of GDP of contributions, so households saved as if no pension would come. `pension_system` -> Defined Benefits; `retirement_age` 65 -> 60; `alpha_db` 0 -> 0.0217 (20% of average earnings plus 2% per credited year beyond ten, paid 13 times a year); `avg_earn_num_years` 35 -> 5; `replacement_rate_adjust` = [0, 0, 0.5, 1, 1, 1, 1] x 1.073, the formal groups' coverage, scaled with generosity so outlays are today's 2.28% of GDP (SSS 1.06%, GSIS 0.68%, military and uniformed pensions 0.54%) times the 3.06-fold rise in covered retirees per worker to the steady state: 6.97% of GDP. With tax rates at today's collections, that mature system squeezes steady-state government consumption to about 3% of GDP (documented as the long-run cost of aging under current policy, not tuned away).
- Settled the remaining sourced inputs before the final retune. `g_y_annual` 0.0371 -> 0.0313: World Bank growth of GDP per person employed (2001-2019), not per capita, since the model's demographics already produce the demographic dividend. Earnings Gini target 40.7 -> 39.3, the World Bank PIP 2023 income Gini (40.7 was the 2021 value). Income gradients in fertility and mortality from the EAPD-DRB Demographic-Gradients library (`ogphl/demographic_gradients.py`): DHS 2022 tilts for fertility (-0.99) and infant mortality (-1.60), and the library's income rule for adult mortality (-0.76 at 2024 GNI per head; no Philippine census measurement). And the NTA age shape of earnings, the half of the e-matrix method the repo lacked (ported from OG-JPN, `scripts/fetch_nta_age_profiles.py`): the US curves are reshaped by the ratio of the Philippine (2015) to the US (2011) NTA labor-income profile before the Gini tilt, moving the model's average earnings peak from age 58 to 46. Also fixes a NumPy 2.5 break in `get_e_interp`.
- All dials re-tuned on the settled inputs: `beta_annual` 0.846, `zeta_K` 0.0705, `tau_c` 0.1042, CIT adjustment 0.5383, `p_wealth` 0.0042, `tau_bq` 0.0030, GS `phi2` 1.7724e-8, `r_gov_shift` -0.00655. Every steady-state target within 0.02pp. Untargeted, consumption is 77.8% of market-price GDP (data 76.1%) and fixed investment 22.1% (data 23.6%).
- `ogphl/targets.py` holds the steady-state dashboard targets, each with its source, and computes the matching model moments from a solved `SS_vars.pkl` (the pattern from OG-ZAF). `examples/tune_ss.py` solves the steady state with optional overrides and prints the dashboard; it sets dials only, and every reported number comes from `run_og_phl.py`.
- Recalibrated capital and saving to Philippine data. Depreciation and patience were still the OG-Core US defaults, which left the steady state with 4.4 times GDP of capital, investment at 38% of market-price GDP and consumption at 58%. `delta_annual` 0.05 -> 0.026 (World Bank consumption of fixed capital, 10.48% of GDP in 2021, over the PWT 11 capital stock, 4.04 times GDP). `beta_annual` 0.96 -> 0.8667, tuned so private K/Y is 3.59 (PWT 2023 total 3.97 less public capital of about 0.38). With the IIP foreign share and domestically held debt, that also puts household wealth at the 3.35 initial-wealth anchor. `zeta_K` 0.47 -> 0.0699, re-tuned so the foreign share of capital stays at the IIP's 20% now that the return on capital is 11.4%. The tax dials were re-tuned to the same collections targets on the new bases (`tau_c` 0.1451 -> 0.1189, CIT adjustment 0.583 -> 0.5403, `p_wealth` 0.00348 -> 0.004217, `tau_bq` 0.0035 -> 0.0032, GS `phi2` 1.9e-8 -> 1.5516e-8). `r_gov_shift` -0.019 -> -0.00666 keeps the effective real rate on debt at 2.0%. `initial_wealth_ratio` 2.783 -> 3.35: since ogcore 0.22 the parameter is the target ratio to initial GDP, so it is the data value itself. Untargeted check: fixed investment is 24.1% of market-price GDP against 23.6% in the national accounts, and consumption 69.4% against 76.1%.

## [Unreleased]

### Added

- Audit pass over the full calibration: `alpha_I` re-mapped to the MTFF infrastructure program under the 2025 start ([0.053, 0.051, 0.051, 0.052] — the 2025 program is 5.3%, which the previous mapping missed); `initial_Kg_ratio` 0.2 -> 0.38, the ICSD/PIMA-informed public capital stock and the same figure subtracted in the initial-wealth construction (the two must stay consistent); the alpha_G glide re-tuned on the resulting revenue path ([0.1122, 0.1092, 0.1045] — the solved 2025 primary balance lands exactly on the programmed -2.51); a regression test pinning the UN country code (the family's #1 copy-paste error); and documentation fixes (the households chapter stated two different Frisch elasticities — the packaged value is 0.25, McNelis et al.; the macro chapter said g_y = 3.6% while the packaged value is 3.71%). Documented the initial-period foreign-capital-share tension: with household wealth at its measured 3.35, the model's t=0 foreign share is ~35% vs the IIP's ~20%, because the model's K/Y exceeds the PWT's — the two observables cannot both hold, and the calibration keeps the household-wealth anchor and records the miss with its mechanical cause.

- Calibrated `eta_RM`, the allocation of aggregate remittances across households, to Philippine data — it was silently at OG-Core's population-proportional default, under which the bottom quarter of households received 25% of remittance value. FIES-based evidence (Ang, Sugiyarto & Jha 2009, Table 4; averaged over the 2000/2003/2006 rounds) puts the top income quintile's share at ~72% and the bottom quintile's at ~0.5%, a gradient that is stable across rounds and consistent with FIES 2018 (ADB WP 714). The quintile value shares are mapped onto the model's seven lifetime-income groups by interpolating the cumulative distribution (uniform within quintile — conservative at the top) and spread per capita across ages within each group. Construction lives in `update_baseline_demographics.remittance_eta` (it is omega-derived, so it regenerates with the demographics); documented caveats: FIES ranks by *current* income (which overstates concentration vs the lifetime concept) while uniform-within-quintile understates top-1% concentration.
- Captured previously unmodeled government revenue (~4.1% of GDP) on the nearest-equivalent model instruments, so the model government's resources now total 19.5% of GDP against ~19.4% actual: (i) the OECD "other taxes" residual net of estate taxes (property taxes, DST, LGU levies; 1.32%) via the **wealth tax** — `h_wealth=1`, `m_wealth=0.001` make the effective rate flat at `p_wealth=0.00348` (0.35%/yr on wealth, an honest stand-in for recurrent property taxation, priced on the saving margin); (ii) BTr income (GOCC/BSP dividends, PAGCOR share, guarantee fees; ~1.0%) plus the OECD unallocable income taxes (0.30%) via the CIT adjustment factor (0.406 -> 0.583); (iii) recurring fees and charges (~0.55%) via `tau_c` (0.1263 -> 0.1451). One-off 2024 items (PHIC/PDIC fund transfers, PPP concession fee) are excluded, per the BTr Cash Operations Report. With honest revenue near 19.4%, `alpha_G` rises to 0.1045 (from the tax-only 0.0694), leaving only the genuine consolidation gap (~2 points of primary balance) between model and observed spending.

### Changed

- **Moved the start year to 2025** — a calibration decision: the start year should be the most recent year the calibration observes, not a projection year. The anchors line up with it directly: alpha_RM is the observed 2025 personal-remittance ratio, the r_gov anchor uses FY2024-2025 interest actuals, and initial_debt_ratio 0.60 matches beginning-of-2025 debt (end-2024: 60.7%, BTr) where a 2026 start would require ~0.62. Demographics (and the demographics-derived g_RM and eta_RM) regenerated for the 2025 start with `update_baseline_demographics`.
- **Anchored initial household wealth to data (requires OG-Core with PSLmodels/OG-Core#1189, unreleased).** OG-Core's transition imposed the steady-state wealth profile rescaled so aggregate initial wealth equals its steady-state level — a ~1.6x uniform windfall for the young Philippine population, which retirees rationally consumed: a 41% one-year aggregate consumption spike, domestic investment collapsing to ~2% of its long-run level, and a spurious debt paydown to 50% of GDP (diagnosed in OG-Core issue #1188). Because initial wealth is a predetermined state, the anchor is static: `initial_wealth_ratio = 2.677` (relative to steady-state GDP) is set so the SOLVED initial wealth-to-GDP ratio equals the data target of 3.35 = (PWT 2023 K/Y 3.97 - ICSD public capital ~0.38) x 0.80 domestic share (BSP IIP) + 0.48 domestically-held debt (BTr); the delivered ratio is 3.35. Reform runs clone the baseline's initial wealth (the initial state is history). Under the anchor the consumption jump is ~2%, investment never collapses, and the fiscal transition is driven by fiscal parameters instead of the phantom windfall. The alpha_G glide re-derived on the realized revenue path: [0.1139, 0.1087, 0.1045] for 2025/2026/2027+, reproducing the MTFF primary balance closely where the program is data (2025: -2.63 model vs -2.51 program; 2026: -2.34 vs -2.22) and running 0.6-1.3pp looser in 2027-28 (transition revenue dips ~1.7pp below its steady-state share mid-window; matching the program exactly there would require a V-shaped spending path). Tests that build a Specifications object strip the parameter when the installed ogcore predates #1189.
- **`TPI_outer_method = "anderson"` in the packaged parameters** — the transition solves in 11-12 iterations (~2 minutes) instead of ~30-70 (~20 minutes), a ~10x wall-clock reduction validated on the baseline, the reform, and the initial-wealth comparison runs; distances decline monotonically with no oscillation.
- `alpha_G` is now a declining path pinned to the government's own consolidation schedule — first derived as [0.1210, 0.1148, 0.1084, 0.1045] for 2026/2027/2028/2029+, then re-derived to [0.1196, 0.1160, 0.1045] under the data-anchored initial wealth (see above) — instead of a flat scalar at the debt-stabilizing level. The first three values reproduce the MTFF's programmed primary balance (DBCC deficit path less BESF FY2026 interest: -2.2, -1.6, -1.1% of GDP) given the model's revenue; the path reaches the identity-consistent level in 2029, the year the program's primary balance crosses the model's pb*. With the flat scalar the model consolidated four years ahead of the plan and paid debt down to ~48% of GDP before returning to target; on the path, the transition's fiscal stance follows the MTFF through the consolidation window (2026 primary balance -1.9 vs -2.2 programmed), and the remaining mid-2030s debt undershoot (trough ~50%) is attributable to the documented 2027 initial-condition transient rather than the fiscal stance. The macro chapter adds a validation figure comparing the model's transition paths of the primary balance, debt ratio, revenue, and public investment against BTr actuals and the MTFF program. The steady state is unchanged (the SS closure is independent of `alpha_G`).

### Fixed

- Corrected the FY2024 interest-payment figure used to anchor `r_gov`: BTr's Cash Operations Report puts it at P763.3bn, not the P854.1bn previously cited (that is FY2025). Real effective rate on debt re-derived at ~2.0% (5.0% nominal less ~3% expected inflation; FY2025 gives the same), `r_gov_shift` -0.02364 -> -0.0190. The debt-stabilizing primary balance is now -0.7% of GDP against the actual -2.8% (BTr), so the steady state embeds ~2 points of consolidation.
- Retuned `zeta_K` 0.4 -> 0.47 to hold the solved foreign-owned capital share at the BSP IIP anchor (~20%) under the recalibrated tax system — the tax changes raise domestic saving, which had pushed the foreign share down to 14%. `zeta_K` is a marginal fill share, so it is validated by the level it produces; the Chinn-Ito index (~0.4) remains the prior locating the plausible range.

- Recalibrated the entire revenue side of `ogphl_default_parameters.json` to actual Philippine collections by instrument (OECD Revenue Statistics in Asia and the Pacific 2025, data for 2023), replacing statutory rates applied to the model's full base. The old calibration collected 28.4% of GDP in tax — the country collects 17.9% — with the personal income tax alone taking 19.5% of GDP, more than the entire actual Philippine tax take. Instrument by instrument (model steady state vs. actual, % of GDP):

  - **PIT**: flat 20% ETR replaced with a progressive Gouveia-Strauss schedule (`tax_func_type = "GS"`) fit to the TRAIN Law: the top rate 0.35 is anchored to the statutory top bracket, the curvature 1.196 is least-squares fit to the statutory schedule's shape, and the scale is tuned in-model so collections match actual PIT revenue. Lands 3.15 vs 3.12. The same triple serves `etr_params`, `mtrx_params`, and `mtry_params` (analytically consistent marginal rates; replaces the flat 6% capital-income MTR).
  - **Social security contributions**: `tau_payroll` 0.14 -> 0.0675, the effective rate that collects actual SSC revenue (2.78% of GDP) from the model's wage bill; the statutory 14-15% applies only to covered formal employment. The old value silently collected ~5.8% of GDP in payroll tax on top of the flat PIT (`frac_tax_payroll` now 0.4712 so the reported PIT/payroll split matches the data split). Lands 2.81 vs 2.78.
  - **CIT**: `adjustment_factor_for_cit_receipts` 0.3 -> 0.406, tuning effective collections to actual corporate tax revenue. Lands 2.90 vs 2.90 (statutory `cit_rate` stays 0.25, CREATE Act).
  - **Indirect**: `tau_c` 0.12 -> 0.1263, now explicitly covering ALL taxes on goods and services (VAT + excises + customs, 7.39% of GDP) rather than nominally being "the VAT rate". Lands 7.37 vs 7.39.
  - **Bequest**: `tau_bq` 0.06 -> 0.0035. The statutory 6% estate rate applied to all model bequest flows collected 1.19% of GDP; actual BIR estate + donor collections are ~0.07%. Same statutory-for-effective error OG-ZAF hit with its bequest tax.

- Re-anchored the sovereign borrowing rate to what the Treasury actually pays: `r_gov_shift` -0.0482 -> -0.02364, putting the steady-state real effective rate on government debt at 2.5% (BTr FY2024 interest of P854bn on ~P15.3tn average debt = 5.6% nominal, less ~3% expected inflation) instead of the 5.1% implied by the raw Li-Magud-Werner-Witte cross-country intercept. The LMWW slope (0.245) is kept; only the level is re-anchored, the same correction OG-ZAF made. Debt service falls ~1.6% of GDP to match the budget data, and with r_gov < g the debt-stabilizing primary balance is a small deficit (-0.4% of GDP) — matching how the Philippines actually stabilizes its debt ratio while running primary deficits.

- Set `alpha_G` to the budget-identity-consistent level (0.0694, from [0.1702, 0.1632, 0.1612]). The old spending share was only sustainable because the flat PIT over-collected by a factor of six; with honest revenue it exceeds what the tax system raises by ~10% of GDP, which the steady-state closure silently overrides but the transition path does not — spending above the consistent level for the first tG1 periods compounds into the debt-elastic premium and destabilizes the path (the OG-ZAF fiscal-runaway lesson). The macro chapter documents the honest decomposition of the gap vs. the DBM BESF spending share: ~4% of GDP of revenue OG-Core has no instrument for (non-tax revenue, property/DST/LGU taxes), plus the remaining consolidation distance to the debt-stabilizing stance.

- Retuned the packaged steady-state initial guesses to the recalibrated steady state (`initial_guess_r_SS` 0.0708 -> 0.064, `initial_guess_TR_SS` 0.1289 -> 0.1324, `initial_guess_factor_SS` 179355 -> 172241). Steady state under the new calibration: r = 0.064, K/Y = 4.49, tax/GDP = 16.3% (vs 16.5% actual excluding unmodeled instruments), K_f/K = 0.14, and the revenue dashboard within 0.04% of GDP on every modeled instrument.

- Recalibrated remittances in `ogphl_default_parameters.json` to the right measure and put them on a growth path that holds their calibrated share. Two separate errors: the level was *cash* remittances and the growth rate was in the wrong units.

  `alpha_RM_1` and `alpha_RM_T` 0.072 -> 0.0812. BSP publishes a GDP ratio only for cash remittances — money through banks and formal couriers — and that headline number is what the 7.2% came from. The model's `RM` is a household income inflow, which is the broader personal (BPM6) measure: BSP reports 2025 personal remittances of US$39.62bn against US$35.63bn in cash remittances, the latter being the 7.3% of GDP they publish, so personal remittances are 0.073 * 39.62/35.63 = 8.12% of GDP on that same denominator. This lands inside the 8.0-9.0% band BSP's own researchers report for personal remittances since 2017, where the cash series runs 7.0-8.0%.

  `g_RM` 0.03 -> a path tracking `g_n`. The 3.0% was the year-over-year growth of remittances in US dollars, but OG-Core advances detrended remittances by `(1 + g_RM) / (exp(g_y) * (1 + g_n))`, so a dollar growth rate is not the input the model wants. Against a denominator running about 5.7% early in the transition, remittances shrank ~2.7% a year in model units: the remittance share of GDP fell from 7.2% to a trough of 4.68% around period 24 — 35% below its calibrated level — and did not recover until roughly period 100. Nothing in the calibration intended that. `g_RM` is now set so the ratio is exactly one in every period, holding remittances at their calibrated share throughout. Because `g_n` falls over the transition this has to be a path, not a scalar; no constant holds the share flat. Note that `alpha_RM_1 = alpha_RM_T` alone does not achieve this — those pin the endpoints, `g_RM` governs everything between them. Steady-state results are unaffected: `get_RM` uses `alpha_RM_T * Y` directly in the steady state and never consults `g_RM`.

  `update_baseline_demographics` now regenerates `g_RM` alongside the demographic arrays, since it is derived from `g_n` and would otherwise go stale after a regeneration, and `tests/test_remittances.py` asserts the share stays flat and that the packaged `g_RM` matches the packaged `g_n`.

### Changed

- Documented the remittance calibration in the households and macro chapters: which BSP measure the model needs and why the published ratio is the wrong one, how `g_RM` is defined in the model's growth units, and — newly stated — that `eta_RM`, the allocation of remittances across households, is left at OG-Core's population-proportional default and is **not** calibrated to the Philippines. Philippine evidence indicates remittances skew toward higher-income households, so the model currently spreads them more evenly than the data suggest; closing that gap needs PSA Family Income and Expenditure Survey microdata. The two chapters previously disagreed with each other and with the shipped values (households said 8.3% with a 3.0% growth story, macro said 7.2%).

## [0.1.1] - 2026-07-27 12:00:00

### Added

- Enabled a debt-elastic sovereign premium in `ogphl_default_parameters.json`, the crowding-out-via-risk channel that OG-Core's defaults and the other country calibrations leave off (`r_gov_DY = r_gov_DY2 = 0`). It is a *centered* convex form, `r_gov_DY2 * (D/Y - 0.6)^2`, flat at the 0.60 debt target and steepening only as debt rises away — `r_gov_DY2 = 0.04`, `r_gov_DY = -0.048`, with `r_gov_shift` recentered from -0.0338 to -0.0482 so the premium is exactly zero at the target and the steady state is unchanged. This matches Philippine experience (stable spreads at 40-70% debt, blowouts only at 1980s-crisis levels). See the macro calibration chapter for the lineage and sources.
- `ogphl/update_baseline.py`: regenerates the packaged single-industry JSON from the live calibration (UN demographics, World Bank `g_y_annual`), so the offline default reproduces the connected run (`uv run python -m ogphl.update_baseline`). The packaged values are refreshed with it.
- `ogphl/update_baseline_demographics.py`: regenerates only the packaged demographic arrays and the demographics-derived earnings profile `e` under the installed ogcore (`uv run python -m ogphl.update_baseline_demographics`), for use after an ogcore bump that changes the demographics convention. Everything else in the JSON is left byte-for-byte unchanged, enforced by a clobber guard that aborts the write if any non-demographic key would differ.

### Changed

- Require `ogcore>=0.18.0` and Python 3.12+, and migrate the calibration to ogcore's income-group-varying demographics (PSLmodels/OG-Core#1165). The floor keeps the packaged parameters and the installed ogcore from drifting apart: the demographic seed parameters do not exist in older ogcore schemas. The packaged demographic arrays (`omega`, `omega_SS`, `rho`, `imm_rates` and their period-0 seeds `g_n_preTP`, `imm_rates_preTP`, and `rho_preTP`) are regenerated in the new age-by-income shape with `update_baseline_demographics` (macro and industry parameters untouched, enforced by the tool's clobber guard), and both `get_pop_objs` call sites pass `income_percentiles=p.lambdas` as 0.18 requires (from PR #78). The regenerated arrays also carry ogcore 0.16.3's earlier demographics rework (PSLmodels/OG-Core#1073), which realigns the transition arrays by one period and adds those period-0 seeds that the aggregation code now uses. OG-PHL's demographics do not vary by income group, so the new arrays are the old ones spread across groups by `lambdas`: the age distribution and the regenerated earnings matrix reproduce the previous values to machine precision, and model results are unchanged. `income.get_e_interp` now reads the OG-USA snapshot's raw JSON values instead of loading them through a `Specifications` object, which decouples it from the installed ogcore's array schema (the 0.18 schema rejects OG-USA's not-yet-migrated shapes) and accepts age weights in either the 1-D or the new age-by-income shape.
- Recalibrated the open-economy block to Philippine data, in `ogphl_default_parameters.json`. Capital openness `zeta_K` 0.9 -> 0.4 (normalized Chinn-Ito index; the old value implied a ~96% foreign-owned capital stock vs. the ~20% in the BSP International Investment Position, and also kept domestic capital so thin that the transition path failed the resource constraint). World interest rate `world_int_rate_annual` 0.04 -> 0.05, adding a ~100 bp Philippine sovereign country-risk premium to the global risk-free rate. Steady-state debt target `debt_ratio_ss` 1.10 -> 0.60, matching the Philippine debt-to-GDP ratio (and the model's initial ratio) instead of the US-style placeholder. These are economy-wide values, so they live in the base JSON and the single- and multi-industry models both inherit them; the macro calibration chapter documents the anchors.
- Macro parameters are no longer clobbered by wrong-source API pulls: `get_macro_params` now refreshes only `g_y_annual` (World Bank, its documented source). The IMF GFS pull for `alpha_T`/`alpha_G` is removed — the Philippine central-government social-benefit series it differenced are zero, which set `alpha_T = 0` and made the steady-state solve divide by zero — as are the World Bank external-debt pull for `initial_foreign_debt_ratio`/`zeta_D` and the ILOSTAT `gamma` and `r_gov_*` overrides; those parameters are held at their documented values in the packaged JSON.
- Retuned the packaged steady-state initial guesses to the recalibrated economy (`initial_guess_r_SS` 0.048 -> 0.0708, `initial_guess_TR_SS` 0.35 -> 0.1289, `initial_guess_factor_SS` 153064 -> 179355). The old values pointed at the pre-recalibration steady state; starting that far away, the solver either crawled through ogcore's initial-guess sweep or exhausted it without converging, which is what kept breaking the example run. From the retuned guesses the baseline steady state solves in seconds. The recalibrated steady state they encode: r = 0.0708, w = 2.760, debt-to-GDP exactly at the 0.60 target, and a 26% foreign-owned capital share — against ~20% in the BSP International Investment Position, where the old calibration implied ~96%.

### Fixed

- Brought all installation instructions in line with the uv workflow the project migrated to in 0.1.0, matching the same fix in OG-ZAF. The README now documents two supported paths, each as per-platform copy-paste blocks verified end to end: the OG family's universal installer (`install.sh --repo og-phl`, from PSLmodels/OG-Core) and a manual install (install uv, clone, `uv run python examples/run_og_phl.py`). The PyPI install section is dropped: `pip install ogphl` on a Python older than 3.12, including the one that ships with macOS, silently installs an outdated release with an old OG-Core, and even on a supported Python the PyPI route does not pin the tested `ogcore` version. The contributor guide and the UN tutorial no longer instruct readers to build the deleted `ogphl-dev` conda environment (those steps failed outright: `environment.yml` was removed in 0.1.0); both now use `uv sync --extra dev` and `uv run`, the contributor guide's test command matches CI (`pytest -m "not local"`), and stale `master`-branch references now say `main`.

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


[0.1.1]: https://github.com/EAPD-DRB/OG-PHL/compare/v0.1.0...v0.1.1
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
