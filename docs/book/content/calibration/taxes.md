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

The total tax function, $T_{s,t}$, is a function of personal income taxes, taxes on bequests, and wealth taxes. In the default calibration, wealth taxes are set to zero in `OG-PHL`. The bequest tax $\tau_{bq}$ is set to 6%, matching the statutory estate tax rate established by the TRAIN Law (Republic Act No. 10963), as published by the Bureau of Internal Revenue ([source](https://www.bir.gov.ph/estate-tax)).

Personal income taxes are modeled as linear taxes and set to average effective and marginal tax rates. The [OG-Core documentation](https://pslmodels.github.io/OG-Core/content/theory/government.html#taxes) details more sophisticated ways to match the progressivity of the tax system. But given limited data for the Philippines, we start with simple linear tax rates: a 20% effective tax rate on personal income (`etr_params`, calibrated to equal the marginal tax rate on labor income), a 20% marginal tax rate on labor income (`mtrx_params`, calibrated using Department of Finance data), and a 6% marginal tax rate on capital income (`mtry_params`, set to the flat capital gains rate established by the TRAIN Law per the Bureau of Internal Revenue).

The `mean_income_data` parameter, used in tax function estimation, is set to ₱353,230 — the mean family income from the Philippine Statistics Authority's Family Income and Expenditure Survey for 2023 ([source](https://psa.gov.ph/statistics/income-expenditure/fies/index)).

## Corporate income taxes

`OG-PHL` uses the top statutory rate of 25% for the corporate income tax rate.

## Value-added taxes

A value-added tax rate of 12% is applied with the `tau_c` parameter.


## Footnotes

[^TaxEq]: See the online OG-Core documentation, Chapter ["Government"](https://pslmodels.github.io/OG-Core/content/theory/government.html), Section ["Effective and Marginal Tax Rates"](https://pslmodels.github.io/OG-Core/content/theory/government.html#effective-and-marginal-tax-rates), equation [(57)](https://pslmodels.github.io/OG-Core/content/theory/government.html#equation-eqtaxcalcliabetr2).
