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

We set $\zeta_K = 0.9$. Note, this parameter is harder to pin down from the data as foreign purchases on "excess" capital demand is not typically directly measured or reported. A value of 0.9 implies a high degree of openness to international capital flows.

### Remittances as a share of GDP

Personal remittance inflows to the Philippines are a substantial component of household income. The ratio of aggregate remittances to GDP is governed by two parameters: $\alpha_{RM,1}$ for the model's start period and $\alpha_{RM,T}$ for the long run / steady state. Both are set to 0.072 (7.2%), based on Bangko Sentral ng Pilipinas (BSP) data for 2025 ([source](https://www.bsp.gov.ph/SitePages/MediaAndResearch/MediaDisp.aspx?ItemId=7821&MType=MediaReleases)). The long-run value is calibrated to equal the current-period value.

## Government Debt, Spending and Transfers

### Government Debt

The path of government debt is endogenous.  But the initial value is exogenous.  To avoid converting between model units and dollars, we calibrate the initial debt to GDP ratio, rather than the dollar value of the debt.  This is the model parameter $\alpha_D$.  We compute this from the ratio of publicly held debt outstanding to GDP.  Based on [a 2024Q1 report from Treasury](https://www.treasury.gov.ph/?p=64737) the value is 0.60.

### Aggregate transfers

Aggregate (non-Social Security) transfers to households are set as a share of GDP with the parameter $\alpha_T$. We exclude Social Security from transfers since it is modeled specifically. We set $\alpha_T = [0.0448]$ (4.48%) using World Bank World Development Indicators data for 2023. The value is computed as the product of total government expense as a share of GDP (WDI series `GC.XPN.TOTL.GD.ZS`) and the share of that expense classified as subsidies and other transfers.

### Government expenditures

Government spending on goods and services is set as a share of GDP with the parameter $\alpha_G$. We define government spending as:
    <center>Government Spending = Total Outlays - Transfers - Net Interest on Debt - Social Security</center>
We set $\alpha_G = [0.1702, 0.1632, 0.1612]$ for years 2026, 2027, and 2028, derived from the Department of Budget and Management (DBM), Budget of Expenditures and Sources of Financing (BESF) for FY 2026, Table A2 ([source](https://www.dbm.gov.ph/wp-content/uploads/BESF/BESF2026/A2.pdf)). Specifically, total disbursements as a percent of GDP are 21.5%, 20.8%, and 20.6% for those years; subtracting $\alpha_T = 0.0448$ from each gives the values above.

### Government interest rate wedge

The interest rate the government pays on its debt, $r_{gov,t}$, generally differs from the household interest rate $r_t$ — sovereigns often borrow at lower rates than the private market because they are seen as safer borrowers. OG-Core models this gap as:

$$r_{gov,t} = \max(r_{gov,scale} \cdot r_t - r_{gov,shift},\; 0)$$

For the Philippines, the two parameters are $r_{gov,scale} = 0.245$ and $r_{gov,shift} = -0.034$. They are calibrated from Philippine sovereign-vs-corporate yield data sourced from the IMF, following the methodology in Li, Magud, Werner, and Witte (2021), [The Long-Run Impact of Sovereign Yields on Corporate Yields in Emerging Markets](https://www.imf.org/en/Publications/WP/Issues/2021/06/04/The-Long-Run-Impact-of-Sovereign-Yields-on-Corporate-Yields-in-Emerging-Markets-50224) (IMF Working Paper No. WP/21/155).
