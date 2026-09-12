(Chap_HouseholdCalib)=
# Calibration of Household Preference Parameters

## Behavioral Assumptions

### Elasticity of labor supply

As discussed in the [OG-Core household theory documentation](https://pslmodels.github.io/OG-Core/content/theory/households.html), we use the elliptical disutility of labor function developed by {cite}`EvansPhillips:2017`.  We then fit the parameters of the elliptical utility function to match the marginal disutility from a constant Frisch elasticity function.  `OG-PHL` users enter the constant Frisch elasticity as a parameter; the calibrated value is given in the next subsection.  {cite}`Peterman:2016` finds a range of Frisch elasticities estimated from microeconomic and macroeconomic data, from 0 to 4.

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
groups. It is calibrated to the distribution of remittance *value* across the
Philippine income distribution, which is heavily concentrated at the top —
OG-Core's default of population-proportional allocation (every group receives
exactly its population share) is rejected by every FIES-based source.

The construction uses {cite}`AngSugiyartoJha:2009` (ADB Economics Working
Paper 188), Table 4, which reports average family income and the remittance
share of income by per-capita income quintile for FIES 2000, 2003, and 2006.
Because PSA quintiles hold equal family counts, each quintile's share of total
remittance value is its mean income times its remittance share of income,
normalized; averaging the three survey rounds gives quintile value shares of
0.5%, 2.0%, 6.3%, 18.7%, and 72.5% from bottom to top. The gradient is stable
across all three rounds — receipt incidence in FIES 2006 rises from about 7%
of bottom-quintile households to about 44% at the top — and cross-validates
against FIES 2018: the remittance share of income among receiving households
rises from 16% in the lowest quintile to 31% in the highest
{cite}`KikkawaEtAl:2024`.
The quintile shares are mapped onto the model's seven lifetime-income groups
by linear interpolation of the cumulative distribution (uniform density
within each quintile), and spread per capita across ages within each group —
the surveys say nothing about the age profile of receipt. The matrix is
rebuilt with the demographics by `ogphl.update_baseline_demographics`, and
`tests/test_remittances.py` pins the group shares.

Two caveats are worth recording. FIES quintiles rank households by *current*
income, and remittances are part of that income, so a household can sit in a
higher quintile *because* it receives remittances — concentration measured
this way overstates concentration with respect to the *lifetime* income
concept the model's groups represent. And the top quintile's 72.5% is spread
uniformly across its percentiles, which is conservative in the other
direction (it understates whatever concentration exists within the top 1%).
The two biases push opposite ways and neither can be resolved without the
FIES microdata; either way, the calibrated matrix is far closer to the data
than the uniform default, under which the bottom quarter of households would
receive 25% of remittance value instead of the ~1% the surveys show.
