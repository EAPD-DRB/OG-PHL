(Chap_Tax)=
# Taxes in OG-PHL

The government is not an optimizing agent in `OG-PHL`. The government levies taxes on household income, corporate income, and value added. With these resources, the government provides transfers to households, spends resources on public goods, and makes rule-based adjustments to stabilize the economy in the long-run. The government can run budget deficits or surpluses in a given year and must, therefore, be able to accumulate debt or savings.  The spending and debt parameters are discussed in Chapter {ref}`Chap_MacroCalib`.  Taxes are discussed in this chapter.


## Personal income taxes
The government sector influences households through two terms in the household budget constraint {eq}`EqHHBC`---government transfers $TR_{t}$ and through the total tax liability function $T_{s,t}$, which can be decomposed into the effective tax rate times total income as shown in the OG-Core documentation.[^TaxEq]. In this chapter, we detail the household tax component of government activity $T_{s,t}$ in `OG-PHL`.

```{math}
:label: EqHHBC
  c_{j,s,t} + b_{j,s+1,t+1} &= (1 + r_{hh,t})b_{j,s,t} + w_t e_{j,s} n_{j,s,t} + \\
  &\quad\quad\zeta_{j,s}\frac{BQ_t}{\lambda_j\omega_{s,t}} + \eta_{j,s,t}\frac{TR_{t}}{\lambda_j\omega_{s,t}} + ubi_{j,s,t} - T_{s,t}  \\
  &\quad\forall j,t\quad\text{and}\quad s\geq E+1 \quad\text{where}\quad b_{j,E+1,t}=0\quad\forall j,t
```

The total tax function, $T_{s,t}$, is a function of personal income taxes, taxes on bequests, and wealth taxes. In the default calibration, wealth taxes are set to zero in `OG-PHL`.

**The organizing principle of this chapter is effective, not statutory, rates.** A large share of Philippine economic activity is informal, exempt, or below filing thresholds, so statutory rates applied to the model's full tax base collect far more revenue than the Bureau of Internal Revenue actually collects. Each instrument below is calibrated so that the model's steady-state collections match actual collections as a share of GDP, taken from the OECD's *Revenue Statistics in Asia and the Pacific 2025* for 2023 — the most recent standardized accounting of Philippine tax revenue by instrument {cite}`OECDRevStatsAP:2025`. An earlier calibration used a flat 20% effective rate on all personal income; that single parameter collected 19.5% of GDP in personal income tax — more than the entire actual Philippine tax take — and financed a spending share that the real tax system cannot support (see the fiscal consistency discussion in {ref}`Chap_MacroCalib`).

The calibration targets, all in percent of GDP for 2023:

| Instrument | Actual (OECD) | Model steady state |
|---|---|---|
| Personal income tax | 3.12 | 3.15 |
| Social security contributions | 2.78 | 2.81 |
| Corporate income tax | 2.90 | 2.90 |
| Taxes on goods and services | 7.39 | 7.37 |
| Estate and donor taxes | ~0.07 | 0.08 |
| Other taxes (property, DST, LGU) | 1.39 | not modeled |
| **Total** | **17.88** | **16.32** |

### Personal income tax: a progressive schedule fit to the TRAIN Law

Personal income taxes use the Gouveia-Strauss (GS) functional form (`tax_func_type = "GS"`), which represents a genuinely progressive schedule with three parameters $(\phi_0, \phi_1, \phi_2)$: the effective rate is exactly zero at the bottom of the income distribution and rises smoothly toward $\phi_0$ at the top. This matches the shape of the Philippine schedule under the TRAIN Law (Republic Act No. 10963, Tax Schedule 2 effective 2023): income below ₱250,000 is exempt, and marginal rates step through 15%, 20%, 25%, and 30% before reaching 35% above ₱8 million.

The three parameters are pinned in three different ways:

- $\phi_0 = 0.35$ is **anchored**, not fitted — it is the statutory top marginal rate, which the GS effective rate approaches asymptotically.
- $\phi_1 = 1.196$ (curvature) is **fit to the statutory schedule**: least squares of the GS effective-rate curve against the schedule's true effective rate over incomes from ₱100,000 to ₱30 million (RMSE 1.7 percentage points).
- $\phi_2 = 1.9 \times 10^{-8}$ (scale) is **tuned in-model to actual collections**. The statutory-fit value ($5.0 \times 10^{-8}$) applied to every peso of model income collects 5.9% of GDP — nearly twice actual PIT collections of 3.12% — because compensation earned informally, below withholding thresholds, or simply not remitted never reaches the BIR. Lowering $\phi_2$ is equivalent to shifting the schedule toward higher incomes, which is exactly what an economy-wide *effective* schedule should do when a large share of earners are effectively untaxed.

The same parameter triple is used for `etr_params`, `mtrx_params`, and `mtry_params` — the GS marginal-rate formula is the analytic derivative of its tax function, so effective and marginal rates are mutually consistent, and marginal rates on labor and capital income are equal (the schedule taxes total income). This replaces the previous flat 6% capital-income marginal rate; note that Philippine capital income is in fact taxed at final withholding rates of 10–20%, so a top-bracket-consistent capital MTR is not a stretch. Tax functions are evaluated at incomes in pesos via the `factor` parameter; `mean_income_data` is ₱353,230, the mean family income from the Philippine Statistics Authority's Family Income and Expenditure Survey for 2023 ([source](https://psa.gov.ph/statistics/income-expenditure/fies/index)).

### Social security contributions

Social security contributions (SSS, GSIS, PhilHealth, Pag-IBIG) are modeled with the payroll tax parameter `tau_payroll`, which applies to labor income on top of the personal income tax function. The statutory SSS contribution rate alone is 15% of the monthly salary credit (2025, employer and employee shares combined), but contributions are collected mostly from formal employment and are capped, so actual collections are far below the statutory rate times the economy-wide wage bill. We set the effective rate from collections: SSC revenue of 2.78% of GDP (OECD, 2023) divided by labor's share of income in the model ($1 - \gamma - \gamma_g = 0.412$) gives `tau_payroll` $= 0.0675$. The reporting split `frac_tax_payroll` $= 0.4712$ divides the model's combined household-tax revenue into its PIT and payroll components in the model output ($2.78 / (2.78 + 3.12)$).

### Corporate income tax

The statutory corporate rate is 25% under the CREATE Act (20% for small corporations), held in `cit_rate`. Effective collections are much lower than the statutory rate times the model's full capital income base — incentives, exemptions, and unincorporated business income all shrink the base. OG-Core composes the effective rate as `cit_rate` × `c_corp_share_of_assets` (0.7) × `adjustment_factor_for_cit_receipts`; the adjustment factor is set to 0.406 so that steady-state corporate tax collections equal actual collections of 2.90% of GDP (OECD, 2023).

### Taxes on goods and services

`tau_c` covers **all** indirect taxes — VAT, excises (fuel, tobacco, alcohol, automobiles, sweetened beverages), customs duties, and other taxes on specific goods and services — which together collected 7.39% of GDP in 2023 (OECD: VAT 4.14, specific goods and services 3.16, of which excises 2.14 and customs 0.50). The rate is tuned in-model so steady-state collections match: `tau_c` $= 0.1263$. This lands close to the 12% statutory VAT rate, but the near-coincidence is accidental: the effective VAT rate on consumption is well below 12% (VAT c-efficiency in the Philippines is roughly 40%), while excises and customs add revenue on top, and the model's consumption share of GDP (~66%) is below the national-accounts household consumption share (~74%), which requires a higher rate on the narrower base to reproduce actual collections.

### Estate and donor taxes

The bequest tax $\tau_{bq}$ is set to 0.35% — an *effective* rate, in contrast to the 6% statutory estate tax rate under the TRAIN Law ([BIR](https://www.bir.gov.ph/estate-tax)). BIR estate and donor tax collections are roughly 0.07% of GDP, while the statutory 6% applied to all model bequest flows would collect 1.19% of GDP — seventeen times actual. The gap is the ₱5 million standard deduction, the family-home exemption, and pervasive non-filing of small estates. This replicates a finding from OG-ZAF, where a statutory-style bequest rate silently collected 3.9% of GDP against negligible actual estate duty.


## Footnotes

[^TaxEq]: See the online OG-Core documentation, Chapter ["Government"](https://pslmodels.github.io/OG-Core/content/theory/government.html), Section ["Effective and Marginal Tax Rates"](https://pslmodels.github.io/OG-Core/content/theory/government.html#effective-and-marginal-tax-rates), equation [(57)](https://pslmodels.github.io/OG-Core/content/theory/government.html#equation-eqtaxcalcliabetr2).
