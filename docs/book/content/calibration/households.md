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

Remittances are a first-order part of Philippine household income, so the model
calibrates both how large they are and how they are shared out across
households. The theory is documented in the OG-Core chapter
"[Remittances](https://pslmodels.github.io/OG-Core/content/theory/households.html#remittances)";
the level, $\alpha_{RM}$, is set in {doc}`macro`.

### Which remittance measure

Bangko Sentral ng Pilipinas (BSP) publishes two series, and they are not
interchangeable. *Cash remittances* count only money sent through banks and
formal courier services; *personal remittances* is the broader BPM6 concept
that also captures in-kind and informal transfers. BSP's own researchers put
personal remittances at 8.0–9.0% of GDP since 2017 and cash remittances at
7.0–8.0% {cite}`BayangosLubangco:2025`.

The model's $RM$ enters the household budget constraint as income received
from abroad and the resource constraint as an inflow, so it takes the *personal*
measure. This distinction is easy to lose: BSP's press releases headline a GDP
ratio only for the cash series, so quoting the published percentage directly
calibrates the model about one percentage point of GDP too low.

### Growth path

$g_{RM}$ is not the growth rate of remittances in dollars. OG-Core advances
detrended remittances by $(1+g_{RM,t})/\left(e^{g_y}(1+g_{n,t-1})\right)$, so
$g_{RM}$ must be stated in the model's own growth units. We calibrate
remittances to a *constant* share of GDP, which means setting $g_{RM,t}$ so
that ratio is exactly one in every period. Because $g_{n}$ falls over the
transition, this is a path rather than a scalar — no single constant holds the
share flat. It is regenerated from $g_{n}$ by
`ogphl.update_baseline_demographics` whenever demographics are rebuilt, and
`tests/test_remittances.py` asserts the resulting share is flat.

Setting $\alpha_{RM,1} = \alpha_{RM,T}$ is not sufficient on its own: those two
parameters pin the endpoints, while $g_{RM}$ governs everything in between.

### Distribution across households

`eta_RM` allocates aggregate remittances across ages and lifetime-income
groups. It is left at OG-Core's default, which distributes remittances in
proportion to population, so every lifetime-income group receives exactly its
population share. **This is an uncalibrated placeholder, not a Philippine
estimate.** The evidence points the other way: income from abroad is a larger
share of household income for higher-income households, and remittance-driven
spending shifts are "significantly more pronounced among wealthier households"
{cite}`BayangosLubangco:2025`. Published sources report this direction but not
the shares by income decile needed to build the matrix; that requires the PSA
Family Income and Expenditure Survey microdata. Until then the model spreads
remittances more evenly across the distribution than the data suggest.
