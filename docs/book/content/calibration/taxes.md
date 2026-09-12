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

Government revenue beyond the OECD tax total is also captured, so the model government's resources match the general picture rather than stopping at the tax line: recurring non-tax revenue (Bureau of the Treasury income and agency fees, about 1.55% of GDP, excluding one-off items like the 2024 PHIC/PDIC fund-balance transfers and PPP concession fee) is mapped onto the nearest-equivalent model instrument, and the OECD "other taxes" residual is carried by the wealth tax. The full mapping, in percent of GDP:

| Revenue line | Actual | Model instrument | Model steady state |
|---|---|---|---|
| Personal income tax | 3.12 | GS schedule (`etr/mtrx/mtry_params`) | 3.12 |
| Social security contributions | 2.78 | `tau_payroll` | 2.78 |
| CIT 2.90 + BTr income 1.00 + unallocable income taxes 0.30 | 4.20 | `cit_rate` × adjustment | 4.21 |
| Goods and services 7.39 + fees and charges 0.55 | 7.94 | `tau_c` | 7.95 |
| Other taxes less estate (property, DST, LGU) | 1.32 | wealth tax (`p_wealth`) | 1.32 |
| Estate and donor taxes | ~0.07 | `tau_bq` | 0.07 |
| **Total** | **19.43** | | **19.46** |

Sources: tax lines from OECD Revenue Statistics 2023 {cite}`OECDRevStatsAP:2025`; non-tax lines from the Bureau of the Treasury FY 2024 Cash Operations Report ([source](https://www.treasury.gov.ph/wp-content/uploads/2025/02/COR-Press-Release-FY-2024.pdf)): BTr income of ₱283.4 billion (dividend remittances from GOCCs and the BSP, PAGCOR profit share, guarantee fees, interest) and recurring other-office fees of roughly ₱135 billion after excluding ₱197 billion of one-off remittances.

### Personal income tax: a progressive schedule fit to the TRAIN Law

Personal income taxes use the Gouveia-Strauss (GS) functional form (`tax_func_type = "GS"`), which represents a genuinely progressive schedule with three parameters $(\phi_0, \phi_1, \phi_2)$: the effective rate is exactly zero at the bottom of the income distribution and rises smoothly toward $\phi_0$ at the top. This matches the shape of the Philippine schedule under the TRAIN Law (Republic Act No. 10963, Tax Schedule 2 effective 2023): income below ₱250,000 is exempt, and marginal rates step through 15%, 20%, 25%, and 30% before reaching 35% above ₱8 million.

The three parameters are pinned in three different ways:

- $\phi_0 = 0.35$ is **anchored**, not fitted — it is the statutory top marginal rate, which the GS effective rate approaches asymptotically.
- $\phi_1 = 1.196$ (curvature) is **fit to the statutory schedule**: least squares of the GS effective-rate curve against the schedule's true effective rate over incomes from ₱100,000 to ₱30 million (RMSE 1.7 percentage points).
- $\phi_2 = 1.9 \times 10^{-8}$ (scale) is **tuned in-model to actual collections**. The statutory-fit value ($5.0 \times 10^{-8}$) applied to every peso of model income collects 5.9% of GDP — nearly twice actual PIT collections of 3.12% — because compensation earned informally, below withholding thresholds, or simply not remitted never reaches the BIR. Lowering $\phi_2$ is equivalent to shifting the schedule toward higher incomes, which is exactly what an economy-wide *effective* schedule should do when a large share of earners are effectively untaxed.

The same parameter triple is used for `etr_params`, `mtrx_params`, and `mtry_params` — the GS marginal-rate formula is the analytic derivative of its tax function, so effective and marginal rates are mutually consistent, and marginal rates on labor and capital income are equal (the schedule taxes total income). This replaces the previous flat 6% capital-income marginal rate; note that Philippine capital income is in fact taxed at final withholding rates of 10–20%, so a top-bracket-consistent capital MTR is not a stretch. Tax functions are evaluated at incomes in pesos via the `factor` parameter; `mean_income_data` is ₱353,230, the mean family income from the Philippine Statistics Authority's Family Income and Expenditure Survey for 2023 ([source](https://psa.gov.ph/statistics/income-expenditure/fies/index)).

### Social security contributions

Social security contributions (SSS, GSIS, PhilHealth, Pag-IBIG) are modeled with the payroll tax parameter `tau_payroll`, which applies to labor income on top of the personal income tax function. The statutory SSS contribution rate alone is 15% of the monthly salary credit (2025, employer and employee shares combined), but contributions are collected mostly from formal employment and are capped, so actual collections are far below the statutory rate times the economy-wide wage bill. We set the effective rate from collections: SSC revenue of 2.78% of GDP (OECD, 2023) divided by labor's share of income in the model ($1 - \gamma - \gamma_g = 0.412$) gives `tau_payroll` $= 0.0675$. The reporting split `frac_tax_payroll` $= 0.4712$ divides the model's combined household-tax revenue into its PIT and payroll components in the model output ($2.78 / (2.78 + 3.12)$).

### Corporate income tax and government capital income

The statutory corporate rate is 25% under the CREATE Act (20% for small corporations), held in `cit_rate`. OG-Core composes the effective rate as `cit_rate` × `c_corp_share_of_assets` (0.7) × `adjustment_factor_for_cit_receipts`, and the adjustment factor (0.583) is tuned so the model's business-tax line collects the government's full take from capital-sector income, 4.20% of GDP: CIT proper (2.90, OECD 2023), the OECD's unallocable income taxes (0.30 — largely final withholding on deposits and similar capital income collected at source), and BTr income (about 1.00 — GOCC and BSP dividend remittances, the national government's share of PAGCOR profits, guarantee fees, and interest income). The last piece is not a tax, but it is recurring government revenue drawn from capital income, and the business-tax instrument is the closest match the model offers; leaving it out understates government resources and forces spending correspondingly too low.

### Taxes on goods and services, and fees

`tau_c` covers **all** indirect taxes — VAT, excises (fuel, tobacco, alcohol, automobiles, sweetened beverages), customs duties, and other taxes on specific goods and services (together 7.39% of GDP in 2023: VAT 4.14, specific 3.16, of which excises 2.14 and customs 0.50) — plus government fees and charges (about 0.55% of GDP, recurring), which are user payments for services and sit most naturally on the consumption margin. The rate is tuned in-model so steady-state collections match the combined 7.94%: `tau_c` $= 0.1451$. That it lands above the 12% statutory VAT rate is not a contradiction: the effective VAT rate on consumption is well below 12% (VAT c-efficiency in the Philippines is roughly 40%), but excises, customs, and fees add revenue on top, and the model's consumption share of GDP (~63%) is below the national-accounts household consumption share (~74%), which requires a higher rate on the narrower base to reproduce actual collections.

### Property-type taxes: the wealth tax instrument

The OECD "other taxes" residual — 1.39% of GDP of real property taxes, documentary stamp taxes, motor vehicle taxes, and local government levies, less the estate and donor taxes carried separately below (net 1.32%) — has no dedicated OG-Core instrument, but most of it is levied on property and property transactions, so the model's **wealth tax** is the honest carrier. Setting `h_wealth` $= 1$ and `m_wealth` $= 0.001$ makes the wealth-tax effective rate essentially flat at `p_wealth` for any positive wealth (and exactly zero at zero wealth); `p_wealth` $= 0.00348$ — a 0.35% annual effective rate on household wealth — is tuned so collections equal the 1.32% target. This prices a real distortion on the saving margin, which is economically appropriate: recurrent property taxes are exactly that.

### Estate and donor taxes

The bequest tax $\tau_{bq}$ is set to 0.35% — an *effective* rate, in contrast to the 6% statutory estate tax rate under the TRAIN Law ([BIR](https://www.bir.gov.ph/estate-tax)). BIR estate and donor tax collections are roughly 0.07% of GDP, while the statutory 6% applied to all model bequest flows would collect 1.19% of GDP — seventeen times actual. The gap is the ₱5 million standard deduction, the family-home exemption, and pervasive non-filing of small estates. This replicates a finding from OG-ZAF, where a statutory-style bequest rate silently collected 3.9% of GDP against negligible actual estate duty.


## Footnotes

[^TaxEq]: See the online OG-Core documentation, Chapter ["Government"](https://pslmodels.github.io/OG-Core/content/theory/government.html), Section ["Effective and Marginal Tax Rates"](https://pslmodels.github.io/OG-Core/content/theory/government.html#effective-and-marginal-tax-rates), equation [(57)](https://pslmodels.github.io/OG-Core/content/theory/government.html#equation-eqtaxcalcliabetr2).
