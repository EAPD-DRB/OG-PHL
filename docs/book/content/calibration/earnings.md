---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

(Chap_LfEarn)=
# Lifetime Earnings Profiles

Among households in `OG-PHL`, we model variations in the labor productivity over the lifecycle and between households of different skill groups. Together, these variations in productivity generate a distribution of earnings that is calibrated to match the level of inequality in the Philippines. This chapter describes the calibration of the lifecycle earnings profiles and the distribution of earnings in the model.

Differences among workers' productivity is one of the key dimensions of heterogeneity to model in a micro-founded macroeconomy. In this chapter, we characterize this heterogeneity as deterministic lifetime productivity paths to which new cohorts of agents in the model are randomly assigned. In `OG-PHL`, households' labor income comes from the equilibrium wage and the agent's endogenous quantity of labor supply. In this section, we augment the labor income expression with an individual productivity $e_{j,s}$, where $j$ is the index of the ability type or path of the individual and $s$ is the age of the individual with that ability path.

```{math}
:label: EqLaborIncome
  \text{labor income:}\quad x_{j,s,t}\equiv w_t e_{j,s}n_{j,s,t} \quad\forall j,t \quad\text{and}\quad E+1\leq s\leq E+S
```

In this specification, $w_t$ is an equilibrium wage representing a portion of labor income that is common to all workers. Individual quantity of labor supply is $n_{j,s,t}$, and $e_{j,s}$ represents a labor productivity factor that augments or diminishes the productivity of a worker's labor supply relative to average productivity.

We calibrate the model such that each lifetime income group has a different life-cycle profile of earnings. Since the distribution on income and wealth are key aspects of our model, we calibrate these processes so that we can represent earners in the top 1 percent of the distribution of lifetime income.

We calibrate deterministic productivity paths such that each lifetime income group has a different life-cycle profile of earnings. The distribution of income and wealth are often focal components of macroeconomic models. These calibrations require the use of microeconomic data on household incomes, but this level of data is not readily available for Philippines from public sources or surveys. To overcome this, we start with the proposition that estimated productivity curves calibrated for the [OG-USA](https://pslmodels.github.io/OG-USA/content/calibration/earnings.html) model, generated from micro-level earnings data, represent a generalized relationship between age and lifetime income {cite}`DeBackerEtAl:2017`. As such, our objective is to generate the curves for the U.S. and then adjust their generalized shapes to produce those for the Philippines. The adjustment has two halves (EAPD-DRB/OG-ZAF#18): first reshape the US curves to the Philippine *age* pattern of earnings, then tilt the gaps between income groups to the Philippine level of inequality.

**The age shape.** Each US curve is multiplied, age by age, by the ratio of the Philippine to the US labor income *per hour worked* by age. Labor income comes from the National Transfer Accounts (NTA, "Labor Income", "Smooth Mean"): the Philippines' latest profile, for 2015 (prepared by Michael Abrigo), against the nearest US year, 2011. NTA labor income is per person at each age, so it carries hours and participation as well as pay; each country's profile is therefore divided by its hours worked per person in the same year (ILOSTAT, from the Labor Force Survey and the CPS) before the ratio is taken. The model's labor supply is calibrated to Philippine hours separately (see {ref}`Chap_HouseholdCalib`), so without the division hours would count twice. Each profile is normalized by its own average over ages 20–64, since only the shape transfers across currencies, and the ratio is held flat from age 67, the midpoint of the hours data's open 65+ band, beyond which hours by age are not observed.

The shapes differ sharply. Philippine labor income per person peaks at age 39, against 49 in the US; per hour the gap widens at older ages, because Filipinos over 65 work twice the US hours per person. The factor is 1.78 at age 20, 1.38 at 30, 0.77 at 55, 0.38 at 65 and 0.25 from 67, reflecting earlier labor-market entry, informality and a pension age of 60. In the solved model, labor income per person peaks at age 46 and productivity per hour at 47 (the US shape peaks at 58). The NTA profiles are fetched by `scripts/fetch_nta_age_profiles.py` and the method is ported from OG-JPN; the hours by `scripts/fetch_ilo_hours_by_age.py`.

**The inequality tilt.** The reshaped curves are then tilted to match the distribution of income in the Philippines, as measured with the Gini coefficient. This is done by finding the value of $a$, such that:

```{math}
  :label: eqnEarningsCalib
    e^{PHL} = e^{USA} * exp^{(a * e^{USA})}
```

and where, $e^{PHL}$, when applied to the population distribution of the Philippines, returns a Gini coefficient that matches the observed Gini coefficient for the Philippines, 39.3: the World Bank Poverty and Inequality Platform's 2023 income Gini (from the FIES; PSA reports 39.16). It is the income concept, the same as the US reference Gini of 41.5, not the PIP consumption Gini of 35.2, so the target and the reference are comparable. The previous value, 40.7, was the 2021 income Gini.

```{figure} ./images/ability_profiles.png
---
height: 350px
name: FigLogAbil
---
Exogenous life cycle income ability paths $\log(e_{j,s})$ with $S=80$ and $J=7$
```

{numref}`Figure %s <FigLogAbil>` shows a calibration for $J=7$ deterministic lifetime ability paths $e_{j,s}$ corresponding to labor income percentiles $\boldsymbol{\lambda}=[0.25, 0.25, 0.20, 0.10, 0.10, 0.09, 0.01]$. Because there are few individuals above age 80 in the data, {cite}`DeBackerEtAl:2017` extrapolate these estimates for model ages 80-100 using an arctan function.
