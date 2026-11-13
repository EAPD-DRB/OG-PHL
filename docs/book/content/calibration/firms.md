(Chap_FirmCalib)=
# Calibration of Firms Parameters

The [OG-Core firm theory documentation](https://pslmodels.github.io/OG-Core/content/theory/firms.html) describes the constant returns to scale, constant elasticity of substitution (CES) production function used by the representative firm in each of the model's $M$ production industries.

## Aggregate Production Function and Capital Accumulation

The production function for industry $m$ is given as:

```{math}
:label: EqFirmsCESprodfun
  \begin{split}
    Y_{m,t} &= F(K_{m,t}, K_{g,m,t}, L_{m,t}) \\
    &\equiv Z_{m,t}\biggl[(\gamma_m)^\frac{1}{\varepsilon_m}(K_{m,t})^\frac{\varepsilon_m-1}{\varepsilon_m} + (\gamma_{g,m})^\frac{1}{\varepsilon_m}(K_{g,m,t})^\frac{\varepsilon_m-1}{\varepsilon_m} + \\
    &\quad\quad\quad\quad\quad(1-\gamma_m-\gamma_{g,m})^\frac{1}{\varepsilon_m}(e^{g_y t}L_{m,t})^\frac{\varepsilon_m-1}{\varepsilon_m}\biggr]^\frac{\varepsilon_m}{\varepsilon_m-1} \quad\forall m,t
  \end{split}
```

This production function has the following parameters:
* $\varepsilon_m$ is the elasticity of substitution between private capital, government capital, and labor in industry $m$.
* $\gamma_m$ is the share of private capital in industry $m$.
* $\gamma_{g,m}$ is the share of government (infrastructure) capital in industry $m$.
* $Z_{m,t}$ is total factor productivity in industry $m$ at time $t$.

`OG-PHL` ships a single-industry calibration ($M=1$), whose parameters are described below.

### Elasticity of substitution

`OG-PHL`'s default parameterization has an elasticity of substitution of $\varepsilon=1.0$, which implies a Cobb-Douglas production function. No Philippine estimate of the capital-labor substitution elasticity is available, and $\varepsilon=1$ is the OG-Core default and the value used by the sibling country models.

### Factor shares of output

The capital share comes from the ILO's labor income share, which adjusts compensation of employees for the labor income of the self-employed: 44.7% of GDP in 2023 for the Philippines (ILOSTAT, `LAP_2GDP_NOC_RT`). The ILO divides by GDP at market prices (SNA item B1g), which includes taxes on products. OG-Core's output $Y$ does not: the consumption tax is paid on top of it, so $Y$ is the sum of factor incomes and market-price GDP is $Y$ plus the consumption tax, about 1.086 times $Y$ (see {ref}`Chap_MacroCalib`). On the model's basis the labor share is therefore $44.7\% \times 1.086 = 48.5\%$ and the total capital share is 51.5%. The Penn World Table's labor share gives almost the same figure (44.9% of GDP in 2023, 48.8% of $Y$). Of that, we allocate 5 percentage points to infrastructure (government) capital, $\gamma_{g,m}=0.05$ for all $m$, leaving private capital's share at $\gamma_m=0.465$.

The previous value, a total capital share of 58.8%, matched one minus the ILO labor share of 2015 on the market-price basis. Both the vintage and the basis moved it: the labor share has risen since 2015 (41.3% then), and the product taxes in market-price GDP are not income to capital. The 2018 social accounting matrix puts capital and land at 62% of factor income, but it books the earnings of self-employed owner-operators as capital income, which is the bias the ILO's adjustment removes.

### Depreciation

The depreciation rate is the consumption of fixed capital divided by the capital stock. The World Bank puts Philippine consumption of fixed capital at 10.12% of GNI in 2021 (series `NY.ADJ.DKAP.GN.ZS`), which is 10.48% of GDP at that year's GNI-to-GDP ratio of 1.036. The Penn World Table 11 capital stock at constant national prices is 4.04 times GDP in the same year. The ratio gives $\delta = 0.026$ (2020 gives 0.025). There is no published split of depreciation between public and private capital, so public capital is assumed to depreciate at the same rate. The previous value, 0.05, was the OG-Core default calibrated to the United States. The low Philippine rate is plausible for a capital stock weighted toward long-lived structures, and it is what lets the steady state hold the measured capital stock while investing the measured 24% of GDP.
