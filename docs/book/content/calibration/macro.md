(Chap_MacroCalib)=
# Calibration of Macroeconomic Parameters

## Economic Assumptions

As the default rate of labor augmenting technological change, $g_y$, we use a value of 3.6%.  The average annual growth rate in GDP per capita in the Philippines between 2000 and 2019 is 3.6% per year.

## Open Economy Parameters

### Foreign holding of government debt in the initial period

The path of foreign holding of domestic debt is endogenous, but the initial period stock of debt held by foreign investors is exogenous.  We set this parameter, `initial_foreign_debt_ratio` to 0.142, as determined from data from the World Bank's World Development Indicators.

### Foreign purchases of newly issued debt

We set $\zeta_D = 0.142$.  This was not directly observed in the data, so the value was set to the current share of foreign holdings of government debt.

### Foreign holdings of excess capital

We set $\zeta_K = 0.9$. Note, this parameter is harder to pin down from the data as foreign purchases on "excess" capital demand is not typically directly measured or reported.  A value of 0.9 implies a high degree of openness to international capital flows.

## Government Debt, Spending and Transfers

### Government Debt

The path of government debt is endogenous.  But the initial value is exogenous.  To avoid converting between model units and dollars, we calibrate the initial debt to GDP ratio, rather than the dollar value of the debt.  This is the model parameter $\alpha_D$.  We compute this from the ratio of publicly held debt outstanding to GDP.  Based on [a 2024Q1 report from Treasury](https://www.treasury.gov.ph/?p=64737) the value is 0.60.

### Aggregate transfers

Aggregate (non-Social Security) transfers to households are set as a share of GDP with the parameter $\alpha_T$. We exclude Social Security from transfers since it is modeled specifically. With this definition, the share of transfers to GDP in 2023 is found to be 9.7% using [IMF data](https://www.imf.org/external/datamapper/profile/PHL).  The value found by differencing out government consumption expenditures (described below) from total government spending as report in the IMF data.

### Government expenditures

Government spending on goods and services are also set as a share of GDP with the parameter $\alpha_G$. We define government spending as:
    <center>Government Spending = Total Outlays - Transfers - Net Interest on Debt - Social Security</center>
With this definition, the share of government expenditure to GDP is 14.2% based on the World Bank World Development Indicators.
