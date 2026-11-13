(Chap_HouseholdCalib)=
# Calibration of Household Preference Parameters

## Behavioral Assumptions

### Elasticity of labor supply

As discussed in the [OG-Core household theory documentation](https://pslmodels.github.io/OG-Core/content/theory/households.html), we use the elliptical disutility of labor function developed by {cite}`EvansPhillips:2017`.  We then fit the parameters of the elliptical utility function to match the marginal disutility from a constant Frisch elasticity function.  `OG-PHL` users enter the constant Frisch elasticity as a parameter; the calibrated value is given in the next subsection.  {cite}`Peterman:2016` finds a range of Frisch elasticities estimated from microeconomic and macroeconomic data, from 0 to 4.

### Intertemporal elasticity of substitution

The default value for the intertemporal elasticity of substitution, $\sigma$, is taken from {cite}`ABMW:1999`.  We set $\sigma=1.5$.

### Rate of time preference

The rate of time preference $\beta$ is tuned rather than sourced: it is the one parameter that sets how much Philippine households save. We set $\beta=0.8981$ (annual, the same for every lifetime-income group) so that fixed investment in the first year of the transition, 2025, is 23.6% of GDP, the national accounts' share (World Bank, 2024). Household wealth in that year is anchored to data (3.35 times GDP, spread across ages by the National Transfer Accounts; see {ref}`Chap_MacroCalib`), so $\beta$ sets how much of the year's income households save on top of it.

$\beta$ is tuned to 2025 rather than to the steady state because the data describe today's population. The Philippine population is young (14% of adults over 60 in 2025 against 31% in the steady state), and older households hold more wealth, so the same patience implies more wealth relative to GDP once the population has aged. Tuning $\beta$ so the steady state held today's capital stock (an earlier version of this calibration) made households too impatient for today: starting from measured wealth, they saved too little and the first year's consumption share came out at 80.8% of GDP against 76.1%. Tuned to 2025, the first year has household consumption at 75.1% of GDP, investment at 23.8%, capital at 3.61 times GDP against the Penn World Table's 3.59 (2023, less public capital), and the foreign share of capital at the IIP's 20%. The steady state then holds 3.69 times GDP in private capital and 3.64 in household wealth, more than today, as an aging population should; it invests 24.4% of GDP and consumes 78.6%. All ratios are to GDP at market prices (see the macro chapter).

The US default from {cite}`Carroll:2009`, 0.96, paired with a US depreciation rate, left the Philippine steady state holding 4.4 times GDP in capital, investing 38% of GDP and consuming 58%. The implied real return to capital is 8.3% in 2025 and 8.0% in the steady state, below OG-ZAF's 11.0% for South Africa; the difference is mostly the capital share, 51.5% here on the model's factor-income basis.

### Disutility of labor by age

The age profile of the disutility of labor, $\chi^n_s$, sets how much households of each age work. Like every OG-Core country model before it, `OG-PHL` used to ship OG-USA's eighty values unchanged. With them, Philippine households in the model worked about 45% of their time endowment at every age up to 55 and still a third of it at 75, against 29% and 5% in the data. `OG-PHL` now calibrates $\chi^n_s$ to Philippine hours, following OG-ETH.

The target is weekly hours worked per person by age from the Philippine Labor Force Survey for 2024, as published by ILOSTAT: the employment-to-population ratio (five-year bands) times the mean weekly hours of the employed (ten-year bands; `scripts/fetch_ilo_hours_by_age.py`). It is per person rather than per worker because the model has no extensive margin: every household of working age supplies some labor, so average labor supply by age corresponds to hours per person in the data, with the non-employed counted at zero. Following OG-USA, labor supply is a share of a 16-hour waking day, seven days a week, so 32 hours a week is $n \approx 0.29$. Philippine hours per person are close to US hours at prime ages (32–33 a week at 30–54) but twice as high over 65 (12 against 6) and lower under 25, where schooling has risen since the K-12 reform. Beyond the survey's open 65+ band the target tapers with the NTA labor-income profile, and it never goes below two percent of the time endowment.

The calibration (`python -m ogphl.labor`) solves the steady state repeatedly. Between solves each $\chi^n_s$ is rescaled toward the ratio of the marginal disutility of labor at the model's labor supply to that at the target, which is the exact adjustment to the household's labor first-order condition when consumption and prices are held fixed. Each step goes half way (in logs), because from the OG-USA profile the full step is four to five times at prime ages and over a hundred at the youngest and oldest, and each solve starts from the previous one (`ogphl/warm_start.py`). The loop stops when every fitted age is within 2% of its target.

| Ages | Survey, hours per person per week | Model steady state |
|---|---|---|
| 20–24 | 16.1 | 16.8 |
| 25–29 | 28.8 | 29.0 |
| 30–34 | 31.8 | 32.0 |
| 35–39 | 32.4 | 32.7 |
| 40–44 | 33.2 | 33.5 |
| 45–49 | 32.9 | 33.2 |
| 50–54 | 31.8 | 32.1 |
| 55–59 | 28.7 | 28.9 |
| 60–64 | 22.8 | 23.0 |
| 65–69 | 12.7 | 12.7 |
| 70–79 | 6.0 | 8.2 |
| 80–99 | 2.2 | 6.9 |

The weights are 240–510 at prime ages against 20–25 in OG-USA. At ages 20–21 and from about 77 on they sit at OG-Core's upper bound of 10,000, where the target cannot be reached, so those ages are left out of the fit: the youngest work slightly more than the survey and the oldest about five hours a week more than the extrapolated target. The level of labor supply roughly halves, which the model absorbs through the `factor` that converts model units to pesos.

Calibrating hours goes together with a change to the earnings profiles: the National Transfer Accounts profile that shapes earnings by age is labor income per person, so it is divided by hours per person before it reshapes the US productivity profiles (see {ref}`Chap_LfEarn`). Otherwise hours would count twice, once in productivity and again in labor supply. Two limits remain. Hours per person mix the decision to work with hours conditional on working, and the elliptical disutility function governs both through one intensive margin. And $\chi^n_s$ has no lifetime-income dimension in OG-Core, so differences in hours between formal and informal workers cannot be represented.

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
