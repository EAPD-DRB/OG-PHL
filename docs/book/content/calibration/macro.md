(Chap_MacroCalib)=
# Calibration of Macroeconomic Parameters

## Economic Assumptions

As the default rate of labor augmenting technological change, $g_y$, we use a value of 3.6%. The average annual growth rate in GDP per capita in the Philippines between 2000 and 2019 is 3.6% per year. The pre-pandemic window is used deliberately to avoid COVID-era volatility distorting the steady-state productivity target.

## Open Economy Parameters

### Foreign holding of government debt in the initial period

The path of foreign holding of domestic debt is endogenous, but the initial period stock of debt held by foreign investors is exogenous. We set this parameter, `initial_foreign_debt_ratio`, to 0.2, based on the Bureau of the Treasury (BTr) Debt Indicator report for Q4 2025 ([source](https://www.treasury.gov.ph/wp-content/uploads/2026/02/Debt-Indicator-December-2025.pdf)).

### Foreign purchases of newly issued debt

We set $\zeta_D = 0.2$. This is calibrated to equal `initial_foreign_debt_ratio` above, on the assumption that the foreign share of newly issued debt matches the foreign share of the existing stock.

### Foreign holdings of excess capital

We set $\zeta_K = 0.47$. This parameter governs the share of the gap between domestically-supplied capital and the capital demanded at the world interest rate that foreign investors fill, so it is effectively the degree of openness of the capital account. It is a *marginal* fill share, not a directly measured quantity, so we calibrate it by the level it produces: $\zeta_K = 0.47$ puts the solved steady-state foreign-owned share of the capital stock at 20%, matching the Bangko Sentral ng Pilipinas International Investment Position. The normalized Chinn-Ito capital-account openness index for the Philippines (roughly 0.4, [Chinn-Ito index](https://web.pdx.edu/~ito/Chinn-Ito_website.htm)) serves as the prior that locates the plausible range — and far from the earlier placeholder of 0.9, which implied a ~96% foreign-owned capital stock. The value is also consistent with the imperfect international capital mobility implied by Feldstein-Horioka-style saving-investment correlations. Note that $\zeta_K$ interacts with the rest of the calibration through household saving: the recalibrated tax system (lower income taxes, a wealth tax) changes domestic saving, so the $\zeta_K$ that hits the IIP anchor moves with it; re-validate the solved foreign share after any tax-side change.

It also restores a domestic-capital buffer the transition needs: at $\zeta_K = 0.9$ domestic capital ($K_d = B - D_d$) is only ~4% of the stock, so the $K_d \geq 0$ constraint binds along the path and the resource constraint fails to close; at 0.4 it clears.

### World interest rate

The small-open-economy block prices foreign capital and foreign debt at an exogenous world interest rate, `world_int_rate_annual`. We set it to 5% — a global risk-free rate of about 4% plus a Philippine country-risk premium of roughly 100 basis points, the Philippines being an investment-grade (BBB) sovereign. The previous 4% placeholder omits this premium, understating the supply price of foreign capital and so overstating foreign ownership of the capital stock.

### Remittances as a share of GDP

Personal remittance inflows to the Philippines are a substantial component of household income. The ratio of aggregate remittances to GDP is governed by two parameters: $\alpha_{RM,1}$ for the model's start period and $\alpha_{RM,T}$ for the long run / steady state. Both are set to 0.0812 (8.12%), and the long-run value is calibrated to equal the current-period value so the calibration implies no remittance transition.

The level is *personal* remittances, the BPM6 measure of household income from abroad, which is the concept the model's $RM$ represents. Bangko Sentral ng Pilipinas (BSP) reports full-year 2025 personal remittances of US\$39.62 billion and cash remittances of US\$35.63 billion, the latter equal to 7.3% of GDP. Applying BSP's own published ratio to the personal measure gives $0.073 \times 39.62/35.63 = 8.12\%$ of GDP, using one consistent GDP denominator throughout. This sits inside the 8.0–9.0% band BSP research reports for personal remittances since 2017 {cite}`BayangosLubangco:2025`; the narrower cash series runs 7.0–8.0%, and calibrating to it understates household income from abroad by roughly a percentage point of GDP. See {doc}`households` for the measurement distinction, the growth path $g_{RM}$, and the household allocation `eta_RM`.

## Government Debt, Spending and Transfers

### Government Debt

The path of government debt is endogenous.  But the initial value is exogenous.  To avoid converting between model units and dollars, we calibrate the initial debt to GDP ratio, rather than the dollar value of the debt.  This is the model parameter $\alpha_D$.  We compute this from the ratio of publicly held debt outstanding to GDP.  Based on [a 2024Q1 report from Treasury](https://www.treasury.gov.ph/?p=64737) the value is 0.60.

We also set the long-run (steady-state) debt-to-GDP target, `debt_ratio_ss`, to 0.60, matching the initial ratio rather than the 1.10 US-style placeholder inherited from OG-Core. This keeps the fiscal closure consistent with the Philippine debt position at both ends of the transition.

```{figure} ./images/debt_ratio_ss_anchor.png
---
height: 400px
name: FigDebtRatioSSPHL
---
Philippine national-government debt-to-GDP, 2000–2025 (Bureau of the Treasury). `debt_ratio_ss` is calibrated to 0.60 — at the MTFF 60% soft ceiling and equal to the current stance, within the ~45–60% band implied by the IMF general-government measure (~57%), the MTFF target, and the World Bank's prudence range. It replaces the inherited 1.10 US-style placeholder, which sat above the entire historical range (2004 peak 71.6%; 2019 trough 39.6%). The lower anchor also shrinks the share of household saving absorbed by government debt, easing the crowding-out that had inflated the foreign-owned capital share.
```

### Aggregate transfers

Aggregate (non-Social Security) transfers to households are set as a share of GDP with the parameter $\alpha_T$. We exclude Social Security from transfers since it is modeled specifically. We set $\alpha_T = [0.0448]$ (4.48%) using World Bank World Development Indicators data for 2023. The value is computed as the product of total government expense as a share of GDP (WDI series `GC.XPN.TOTL.GD.ZS`) and the share of that expense classified as subsidies and other transfers.

### Government expenditures

Government spending on goods and services is set as a share of GDP with the parameter $\alpha_G$. It is **not** set to the observed spending share; it is set to the level consistent with the government budget at the debt target — the single most consequential discipline in the fiscal calibration.

For debt to hold at `debt_ratio_ss` $= \bar{d}$, the government must run a primary balance $pb^* = \frac{r_{gov} - g}{1 + g}\,\bar{d}$, where $g$ is the model's steady-state growth rate. With the re-anchored $r_{gov} = 2.0\%$ and $g = 3.2\%$, $pb^* \approx -0.7\%$ of GDP. Primary spending must therefore equal revenue minus $pb^*$: with modeled revenue of 19.4% of GDP (taxes plus captured non-tax revenue — see {ref}`Chap_Tax`), total primary spending is 20.1%, and after transfers ($\alpha_T = 0.0448$) and public investment ($\alpha_I = 0.052$), $\alpha_G = 0.1045$.

For comparison, the DBM Budget of Expenditures and Sources of Financing implies a goods-and-services share of about 16% (FY 2026 disbursements of 21.5% of GDP less transfers, which includes interest of ~2.9%, so ~13% on a primary basis). The remaining distance between 10.5% and ~13% is the consolidation gap: the actual FY 2024 primary deficit was 2.8% of GDP against the model's debt-stabilizing $-0.7\%$, and the model's steady state represents the debt-stabilizing stance, not today's. Two structural points matter for anyone recalibrating this block: OG-Core's steady-state closure makes $G$ the residual of the budget identity regardless of the input $\alpha_G$, so an inconsistent value is not honored in the steady state — it only destabilizes the *transition*, where $\alpha_G$ binds for the first $t_{G1}$ periods and excess spending compounds into the debt-elastic premium. And revenue errors mask spending errors: an earlier calibration paired $\alpha_G \approx 0.17$ with a flat 20% income tax that over-collected by a factor of six; the two errors cancelled in the steady state while distorting every household decision in the model.

**The transition follows the government's own consolidation schedule.** A single flat $\alpha_G$ at the identity value would make the model consolidate *immediately* — a primary balance of $-0.7\%$ from the first period, four years ahead of the government's plan. Instead, $\alpha_G$ is a declining path pinned to the Medium-Term Fiscal Framework: $[0.1196, 0.1160, 0.1045]$ for 2026, 2027, and 2028 onward. Each early value is the spending share that reproduces the MTFF's programmed primary balance for that year (the DBCC deficit path less BESF FY 2026 interest payments: $-2.2$ and $-1.6$ percent of GDP for 2026–27), given the model's *realized* transition revenue under the data-anchored initial wealth below; the path reaches the debt-stabilizing level in 2028, just before the program's own primary balance crosses the model's $pb^*$. The MTFF program converging to the model's debt-stabilizing stance by the end of the decade is itself a useful validation of the fiscal block: the steady state is where the government's plan is headed. On the solved path the model's primary balance matches the program exactly in 2026 and 2027 ($-2.22$, $-1.60$) and to 0.15pp in 2028.

### Initial household wealth

OG-Core's transition path historically imposed the initial distribution of household wealth as the steady-state profile rescaled so that *aggregate* initial wealth equals its steady-state level. For the Philippines that rescale factor is 1.625 — the 2026 population is young relative to the model's stationary distribution — so every initial household received a 63% wealth windfall, which short-horizon retirees rationally consumed: a 41% one-year jump in aggregate consumption, domestic investment collapsing to ~2% of its long-run level, and a spurious debt paydown to 50% of GDP. See [OG-Core issue #1188](https://github.com/PSLmodels/OG-Core/issues/1188).

This calibration instead anchors initial wealth to data with `initial_wealth_ratio` ([OG-Core PR #1189](https://github.com/PSLmodels/OG-Core/pull/1189), **which this calibration requires**): observed household wealth relative to the model's steady-state level is $(K_d/Y + D_d/Y)_{data} / (B/Y)_{ss} = (0.8 \times 3.5 + 0.8 \times 0.6)/3.98 = 0.823$, using the PWT capital-output ratio, the BSP IIP foreign-owned capital share, and the BTr domestic share of debt. Under the data-anchored value the artifact is gone: the 2026→2027 consumption jump is 4% rather than 41%, investment never collapses, and the transition's fiscal paths are driven by fiscal parameters rather than a phantom windfall.

### Fiscal paths against actuals and the program

```{figure} ./images/fiscal_paths_vs_program.png
---
height: 500px
name: FigFiscalPathsPHL
---
Baseline model transition paths against Bureau of the Treasury actuals (2022–2024) and the DBCC Medium-Term Fiscal Framework 2022–2030 Midterm Update (October 2025) program. Public investment sits on the MTFF infrastructure program; revenue runs near the program's general-government equivalent (MTFF national-government revenue plus a +3.78pp bridge for social security contributions and local taxes, from the 2023 OECD-vs-BTr gap), drifting below it later because the program embeds tax-administration gains the calibration holds constant; the primary balance reproduces the programmed consolidation exactly in 2026–27 and to 0.15pp in 2028. The debt ratio stays within about ±4pp of the 0.60 anchor along the whole path (a shallow dip to 55.6% in 2033 as the model briefly runs tighter than $pb^*$, then a rise to 63.8% in 2046 as transition revenue sits below its steady-state share, before the closure settles it at target). Earlier versions of this figure showed a violent 2027 revenue spike and a debt paydown to 50% of GDP — both artifacts of OG-Core's imposed initial wealth distribution, removed by the data-anchored `initial_wealth_ratio` (see the initial household wealth section above).
```

### Government interest rate wedge

The interest rate the government pays on its debt, $r_{gov,t}$, generally differs from the household interest rate $r_t$ — sovereigns often borrow at lower rates than the private market because they are seen as safer borrowers, but the spread also widens with the debt burden. OG-Core captures both through:

$$r_{gov,t} = \max\Big(r_{gov,scale} \cdot r_t - r_{gov,shift} + r_{gov,DY} \cdot \tfrac{D_t}{Y_t} + r_{gov,DY2} \cdot \big(\tfrac{D_t}{Y_t}\big)^2,\; 0\Big)$$

**Level wedge.** The slope $r_{gov,scale} = 0.245$ — the pass-through of the private rate into the sovereign rate — comes from Philippine sovereign-vs-corporate yield data sourced from the IMF, following Li, Magud, Werner, and Witte (2021), [The Long-Run Impact of Sovereign Yields on Corporate Yields in Emerging Markets](https://www.imf.org/en/Publications/WP/Issues/2021/06/04/The-Long-Run-Impact-of-Sovereign-Yields-on-Corporate-Yields-in-Emerging-Markets-50224) (IMF WP/21/155). The intercept, however, is **re-anchored to the real effective rate the Philippine government actually pays on its debt stock** rather than taken from the LMWW cross-country estimate. In the model, $r_{gov}$ multiplies the entire debt stock in the debt-service line, so it is an *average* rate, and the matching data moment is interest payments over gross debt: the Bureau of the Treasury's Cash Operations Report puts FY 2024 interest payments at ₱763.3 billion ([source](https://www.treasury.gov.ph/wp-content/uploads/2025/02/COR-Press-Release-FY-2024.pdf)) on an average national-government debt stock of about ₱15.3 trillion — a 5.0% nominal effective rate — less expected inflation of about 3% (the BSP target midpoint) gives a **real effective rate of about 2.0%** (FY 2025, with interest of ₱854 billion on a larger stock, gives essentially the same rate). `r_gov_shift` is set to $-0.0190$ so the steady-state $r_{gov}$ equals that value (the stored shift includes the debt-elastic recentering described below). The raw LMWW intercept instead put the steady-state $r_{gov}$ at 5.1% real — 3 percentage points above what the Treasury pays — which overstated debt service by about 1.9% of GDP and, through the budget identity, forced model government spending that much lower. The same correction was applied in OG-ZAF for the same reason.

A consequence worth stating plainly: at $r_{gov} = 2.0\%$ real and steady-state growth $g \approx 3.2\%$, the model has $r_{gov} < g$, so the debt-stabilizing primary balance is a small *deficit* (about $-0.7\%$ of GDP) — consistent with the actual Philippine experience of stabilizing debt ratios while running primary deficits, because nominal growth exceeds the nominal effective interest rate. The actual FY 2024 primary deficit was 2.8% of GDP (BTr), so the model's steady state still embeds roughly two points of consolidation relative to the current stance.

**Debt-elastic premium.** The $r_{gov,DY}$ and $r_{gov,DY2}$ terms let the sovereign rate rise with the debt ratio — the crowding-out-via-risk channel that OG-Core and the sister country models leave off (otherwise a debt-financed reform raises debt with no feedback to borrowing cost). It is the [Schmitt-Grohé and Uribe (2003)](https://www.nber.org/system/files/working_papers/w9270/w9270.pdf) premium in convex (quadratic) form, following the fiscal-limits literature ([Bi 2012](https://www.sciencedirect.com/science/article/abs/pii/S0014292111001085); [Ghosh et al. 2013](https://www.nber.org/system/files/working_papers/w16782/w16782.pdf)). OG-PHL uses a *centered* form, $r_{gov,DY2}\,(D_t/Y_t - 0.6)^2$ — flat at the 0.60 target and steepening only as debt rises away — matching the country's stable spreads at 40–70% debt and stress only at 1980s-crisis levels. We set $r_{gov,DY2} = 0.04$ (so $r_{gov,DY} = -0.048$, with `r_gov_shift` recentered to $-0.0482$), which holds the steady state fixed and adds ~36 bp at $D/Y = 0.9$ and ~144 bp at 1.2 — within the emerging-market spread-to-debt range ([Jaramillo and Weber 2012](https://www.imf.org/external/pubs/ft/wp/2012/wp12198.pdf)). A conservative $r_{gov,DY2} = 0.02$ is a reasonable alternative.

Centering is what makes the premium usable along the transition. The multi-industry baseline debt path overshoots to about 1.3 times GDP early in the fiscal-adjustment window (period $t_{G1}$) before returning to 0.60, and the centered premium prices that overshoot at a plausible peak sovereign rate near 7.8%. A premium that bit at the target (vertex at zero debt) would instead compound the overshoot into a runaway debt-service feedback — toward ~1.7 and a ~16% rate. It is enabled by default.
