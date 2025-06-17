(Chap_HouseholdCalib)=
# Calibration of Household Preference Parameters

## Behavioral Assumptions

### Elasticity of labor supply

As discussed in the [OG-Core household theory documentation](https://pslmodels.github.io/OG-Core/content/theory/households.html), we use the elliptical disutility of labor function developed by {cite}`EvansPhillips:2017`.  We then fit the parameters of the elliptical utility function to match the marginal disutility from a constant Frisch elasticity function.  `OG-PHL` users enter the constant Frisch elasticity as a parameter.  {cite}`Peterman:2016` finds a range of Frisch elasticities estimated from microeconomic and macroeconomic data.  These range from 0 to 4.  Peterman makes the case that in lifecycle models without an extensive margin for employment the  Frisch elasticity should be higher. For `OG-PHL` we take a default value of 0.4 from {cite}`Altonji:1986`.

### Intertemporal elasticity of substitution

The default value for the intertemporal elasticity of substitution, $\sigma$, is taken from {cite}`ABMW:1999`.  We set $\sigma=1.5$.

### Rate of time preference

We take our default value for the rate of time preference parameter, $\beta$ from {cite}`Carroll:2009`.  We set the value to $\beta=0.96$ (on an annual basis).

### Frisch elasticity of labor supply
We take our default value for the Frisch elasticity of labor supply as $\nu=0.25$. This value was estimated by {cite}`McNelisEtAl:2009` (see p. 19).

## Remittances
To calibrate remittances, we use Bangko Sentral Ng Pilipinas February 17, 2025 report entitled, "\href{https://www.bsp.gov.ph/SitePages/MediaAndResearch/MediaDisp.aspx?ItemId=7426}{Personal Remittances Reach a Record High of US$3.7 Billion in December 2024; Full-Year Level of US$38.3 Billion Highest to Date}". Annual growth rate in remittances ($g_{RM}$ or \texttt{g_RM}) is approximately 3.0% (US$3.73B in Dec. 2024 versus US$3.62B in DeC. 2023). Remittances in 2024 represented 8.3% of GDP. We assume that is the level of remittances in the initial period, then remittances grow at a 3.0% rate until period $t_{G1}$ after which they revert to 8.3% of GDP. The theory for how remittances are modeled in OG-PHL can be found in the OG-Core online documentation chapter entitled "\href{https://pslmodels.github.io/OG-Core/content/theory/households.html#remittances}{Remittances}".
