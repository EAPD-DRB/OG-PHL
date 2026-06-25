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

We set $\zeta_K = 0.4$. This parameter governs the share of the gap between domestically-supplied capital and the capital demanded at the world interest rate that foreign investors fill, so it is effectively the degree of openness of the capital account. It is harder to pin down from the data than the debt parameters, because purchases of "excess" capital demand are not directly measured. We anchor the value to the normalized Chinn-Ito capital-account openness index for the Philippines, which sits at roughly 0.4 ([Chinn-Ito index](https://web.pdx.edu/~ito/Chinn-Ito_website.htm)). This is also consistent with the imperfect international capital mobility implied by Feldstein-Horioka-style saving-investment correlations, and with the Bangko Sentral ng Pilipinas International Investment Position, which shows foreign-owned capital at roughly 20% of the stock — far below the ~96% that the earlier placeholder of 0.9 implied.

The choice also matters for solving the model. At $\zeta_K = 0.9$ domestically-held capital, $K_d = B - D_d$, is a razor-thin ~4% of the total stock; along the transition path the $K_d \geq 0$ constraint binds, the solver clamps it, and the aggregate resource constraint fails to close. At $\zeta_K = 0.4$ domestic capital keeps a comfortable buffer and the (multi-industry) transition path converges to a true equilibrium.

### World interest rate

The small-open-economy block prices foreign capital and foreign debt at an exogenous world interest rate, `world_int_rate_annual`. We set this to 5% (annual). We read it as a global risk-free rate of about 4% plus a Philippine country-risk premium of roughly 100 basis points — the Philippines is an investment-grade (BBB) sovereign, so foreign investors require modest compensation over the risk-free rate to hold Philippine claims. The 4% placeholder used previously omits this premium and so understates the supply price of foreign capital. Raising the world rate from 4% to 5% lowers the equilibrium foreign capital share (foreigners supply less when their required return is higher), pulls the domestic return toward an emerging-market-realistic level near 9%, and raises the household consumption share of output. A larger premium (e.g. an equity-style 200 basis points, a 6% world rate) moves these margins further in the same direction; 5% is the conservative sovereign-spread anchor.

### Remittances as a share of GDP

Personal remittance inflows to the Philippines are a substantial component of household income. The ratio of aggregate remittances to GDP is governed by two parameters: $\alpha_{RM,1}$ for the model's start period and $\alpha_{RM,T}$ for the long run / steady state. Both are set to 0.072 (7.2%), based on Bangko Sentral ng Pilipinas (BSP) data for 2025 ([source](https://www.bsp.gov.ph/SitePages/MediaAndResearch/MediaDisp.aspx?ItemId=7821&MType=MediaReleases)). The long-run value is calibrated to equal the current-period value.

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

Government spending on goods and services is set as a share of GDP with the parameter $\alpha_G$. We define government spending as:
    <center>Government Spending = Total Outlays - Transfers - Net Interest on Debt - Social Security</center>
We set $\alpha_G = [0.1702, 0.1632, 0.1612]$ for years 2026, 2027, and 2028, derived from the Department of Budget and Management (DBM), Budget of Expenditures and Sources of Financing (BESF) for FY 2026, Table A2 ([source](https://www.dbm.gov.ph/wp-content/uploads/BESF/BESF2026/A2.pdf)). Specifically, total disbursements as a percent of GDP are 21.5%, 20.8%, and 20.6% for those years; subtracting $\alpha_T = 0.0448$ from each gives the values above.

### Government interest rate wedge

The interest rate the government pays on its debt, $r_{gov,t}$, generally differs from the household interest rate $r_t$ — sovereigns often borrow at lower rates than the private market because they are seen as safer borrowers, but the spread also widens with the debt burden. OG-Core captures both through:

$$r_{gov,t} = \max\Big(r_{gov,scale} \cdot r_t - r_{gov,shift} + r_{gov,DY} \cdot \tfrac{D_t}{Y_t} + r_{gov,DY2} \cdot \big(\tfrac{D_t}{Y_t}\big)^2,\; 0\Big)$$

**Level wedge.** The first two parameters set the level of the sovereign rate relative to the private rate. For the Philippines, $r_{gov,scale} = 0.245$ and $r_{gov,shift} = -0.034$, calibrated from Philippine sovereign-vs-corporate yield data sourced from the IMF, following the methodology in Li, Magud, Werner, and Witte (2021), [The Long-Run Impact of Sovereign Yields on Corporate Yields in Emerging Markets](https://www.imf.org/en/Publications/WP/Issues/2021/06/04/The-Long-Run-Impact-of-Sovereign-Yields-on-Corporate-Yields-in-Emerging-Markets-50224) (IMF Working Paper No. WP/21/155).

**Debt-elastic premium.** The remaining parameters, $r_{gov,DY}$ and $r_{gov,DY2}$, let the sovereign rate rise with the debt-to-GDP ratio. They are zero in OG-Core's defaults and in the other country calibrations, which leaves sovereign borrowing free at the margin — a debt-financed reform raises debt with no feedback to the government's cost of funds. That omission matters most for an emerging market: it is exactly the crowding-out-via-risk channel that makes deficit-financed policy costly. The term originates as the [Schmitt-Grohé and Uribe (2003)](https://www.nber.org/system/files/working_papers/w9270/w9270.pdf) debt-elastic interest-rate premium; the *quadratic* form follows the sovereign-risk / fiscal-limits literature ([Bi 2012](https://www.sciencedirect.com/science/article/abs/pii/S0014292111001085); [Ghosh et al. 2013](https://www.nber.org/system/files/working_papers/w16782/w16782.pdf)), in which the default-probability schedule is convex, so spreads are flat at low debt and accelerate toward the country's fiscal limit. [Ardagna, Caselli and Lane (2007)](https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp411.pdf) find precisely this — the linear debt effect is roughly zero and the response is carried by the quadratic term.

For debt-moving experiments we therefore recommend a pure-quadratic calibration: $r_{gov,DY} = 0$ and $r_{gov,DY2} = 0.04$ (sensitivity band 0.025–0.06). In OG-Core's units $D/Y$ is a ratio and $r_{gov}$ a decimal, so the coefficients are not basis points; the marginal sensitivity is $2\,r_{gov,DY2}(D/Y)$, about 4.8 basis points per percentage point of debt at the 60% target and ~8 bp at 100% — within the range estimated for emerging markets ([Jaramillo and Weber 2012](https://www.imf.org/external/pubs/ft/wp/2012/wp12198.pdf); [Akitoby and Stratmann 2008](https://www.imf.org/external/pubs/ft/wp/2006/wp0616.pdf); compared with ~3 bp for advanced economies, [Laubach 2009](https://www.federalreserve.gov/pubs/feds/2003/200312/200312pap.pdf)). To avoid double-counting the level that the wedge already calibrates, the premium is *recentered* on the steady-state debt target by adjusting the shift, $r_{gov,shift}^{new} = r_{gov,shift} + r_{gov,DY2}\,(D/Y)_{ss}^2 = -0.034 + 0.04 \cdot 0.6^2 = -0.019$, so the premium is exactly zero at $D/Y = 0.6$ and the steady state is unchanged; it bites only as debt deviates from target along a transition.

Because the steady state is unaffected, these terms are left at zero in the default calibration and enabled per experiment. There is an important caveat for the multi-industry transition. The baseline debt path overshoots its long-run target before settling — it humps to about 1.2 times GDP at the start of the fiscal-adjustment window (period $t_{G1}$) and only returns to 0.6 by around period 80. A convex premium evaluated at that peak is far outside its calibration range, and it sets off a destabilizing debt-service feedback (higher debt raises $r_{gov}$, which raises interest payments, which raises debt). Enabling the central calibration on the multi-industry baseline pushes the debt peak from ~1.2 to ~1.7 and the transitional sovereign rate to ~16%, an implausible path even though the solver still converges and the steady state is unchanged. The premium is therefore well-behaved only where debt stays in a moderate range (it adds ~180 bp at $D/Y = 0.9$); applying it to the multi-industry model requires either taming the baseline overshoot first or capping the premium. We keep it off by default for this reason.
