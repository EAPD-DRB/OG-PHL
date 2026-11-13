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

(Chap_Exog)=
# Exogenous Parameters


  The JSON file [`ogphl_default_parameters.json`](https://github.com/EAPD-DRB/OG-PHL/blob/master/ogphl/ogphl_default_parameters.json) provides values for all the model parameters used as defaults for `OG-PHL`. Below, we provide a table highlighting some of the parameters describing the scale of the model (number of periods, aged, productivity types) and some parameters of the solution method (dampening parameter for TPI). The table below provides a list of the exogenous parameters and their baseline calibration values. Shares of GDP in the table (transfers, spending, public investment, remittances, the debt and initial-wealth ratios) are shares of the model's output $Y$, which excludes the consumption tax; each is the published share of GDP at market prices times 1.086 (see {ref}`Chap_MacroCalib`).

  <!-- +++
  ```{code-cell} ogphl-dev
  :tags: [hide-cell]
  from myst_nb import glue
  import ogcore.parameter_tables as pt
  from ogcore import Specifications
  import ogphl
  import importlib
  import json
  p = Specifications()
  with importlib.resources.open_text(
      "ogphl", "ogphl_default_parameters.json"
      ) as file:
          defaults = json.load(file)
  table = pt.param_table(p, table_format="md", path=None)
  glue("param_table", table, display=False)
  ```
  -->

| Symbol                                   | Description                                                                                                                  | Value                                                 |
|:-----------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------|
| $\theta$                                 | Frisch elasticity of labor supply                                                                                            | 0.250                                                 |
| $g_{y,ann,t}$                            | Annual growth rate of labor augmenting technological change                                                                  | 0.031                                                 |
| $S$                                      | Maximum periods in economically active individual life                                                                       | 80                                                    |
| $J$                                      | Number of lifetime income groups                                                                                             | 7                                                     |
| $T$                                      | Number of periods to steady-state                                                                                            | 320                                                   |
| $M$                                      | Number of different production industries                                                                                    | 1                                                     |
| $I$                                      | Number of different consumption goods                                                                                        | 1                                                     |
| $\lambda_{j}$                            | Lifetime income group percentages                                                                                            | Too large to report here, see default parameters JSON |
| $e_{j,s,t}$                              | Deterministic ability process                                                                                                | Too large to report here, see default parameters JSON |
| $\beta_{j,ann}$                          | Annual rate of time preference for households                                                                                | [0.903...0.903]                                       |
| $\sigma$                                 | Coefficient of constant relative risk aversion                                                                               | 1.500                                                 |
| $\alpha_i$                               | Share parameters for each good in the composite consumption good                                                             | [1.000...1.000]                                       |
| $c_{min,i}$                              | Minimum consumption levels for each good in the composite consumption good                                                   | [0.000...0.000]                                       |
| $\gamma_m$                               | Capital share of income by industry                                                                                          | [0.465...0.465]                                       |
| $\gamma_{g,m}$                           | Public capital's share of output in firm production function by industry                                                     | [0.050...0.050]                                       |
| $\varepsilon_m$                          | Elasticity of substitution between capital and labor by industry                                                             | [1.000...1.000]                                       |
| $\Pi^I$                                  | Input-output matrix                                                                                                          | Too large to report here, see default parameters JSON |
| $Z_{m,t}$                                | Total factor productivity by industry                                                                                        | Too large to report here, see default parameters JSON |
| $\delta_{M,ann}$                         | Annual rate of economic depreciation of capital                                                                              | 0.026                                                 |
| $\delta_{g,ann}$                         | Annual rate of economic depreciation of public capital                                                                       | 0.020                                                 |
| $\tilde{l}$                              | Maximum hours of labor supply                                                                                                | 1.000                                                 |
| $r^*_t$                                  | Exogenous annual world interest rate                                                                                         | [0.050...0.050]                                       |
| $D_{f,0}$                                | Share of government debt held by foreigners in initial period                                                                | 0.200                                                 |
| $\zeta_{D,t}$                            | Share of new debt issues purchased by foreigners                                                                             | [0.200...0.200]                                       |
| $\zeta_{K,t}$                            | Share of excess capital demand satisfied by foreigners                                                                       | [0.145...0.145]                                       |
| $T_{G1}$                                 | Model period in which budget closure rule starts                                                                             | 20                                                    |
| $T_{G2}$                                 | Model period in which budget closure rule ends                                                                               | 256                                                   |
| $\alpha^{T}_{t}$                         | Transfers as a share of GDP                                                                                                  | [0.049...0.049]                                       |
| $\alpha^{G}_{t}$                         | Government spending as a share of GDP                                                                                        | [0.102...0.073]                                       |
| $\alpha^{I}_{t}$                         | Exogenous fraction of GDP for infrastructure investment                                                                      | [0.058...0.056]                                       |
| $\phi_g$                                 | Infrastructure investment leakage rate                                                                                       | 0.00E+00                                              |
| $\alpha^{BS}_{T,t}$                      | Proportional adjustment to government transfers relative to baseline amount when baseline_spending is True                   | [1.000...1.000]                                       |
| $\alpha^{BS}_{G,t}$                      | Proportional adjustment to government consumption expenditures relative to baseline amount when baseline_spending is True    | [1.000...1.000]                                       |
| $\alpha^{BS}_{I,t}$                      | Proportional adjustment to infrastructure spending relative to baseline amount when baseline_spending is True                | [1.000...1.000]                                       |
| $\alpha^{BS}_{FA,t}$                     | Proportional adjustment to foreign aid relative to baseline amount when baseline_spending is True                            | [1.000...1.000]                                       |
| $\rho_{G}$                               | Budget closure rule smoothing parameter                                                                                      | 0.100                                                 |
| $\alpha_{FA,t}$                          | Foreign aid as a share of GDP                                                                                                | [0.000...0.000]                                       |
| $\alpha_{RM,1}$                          | Remittances as a share of GDP in initial period                                                                              | 0.088                                                 |
| $\alpha_{RM,T}$                          | Remittances as a share of GDP in long run                                                                                    | 0.088                                                 |
| $g_{RM,t}$                               | Growth rate of remittances in initial periods                                                                                | [0.052...0.026]                                       |
| $\bar{\alpha}_{D}$                       | Steady-state Debt-to-GDP ratio                                                                                               | 0.652                                                 |
| $\Gamma_{1}$                             | Initial period household wealth distribution                                                                                 | Too large to report here, see default parameters JSON |
| $\alpha_{B,1}$                           | Initial period wealth-to-GDP ratio                                                                                           | 3.639                                                 |
| $\alpha_{D,0}$                           | Initial period Debt-to-GDP ratio                                                                                             | 0.652                                                 |
| $\tau_{d,t}$                             | Scale parameter in government interest rate wedge                                                                            | [0.245...0.245]                                       |
| $\mu_{d,t}$                              | Shift parameter in government interest rate wedge                                                                            | [-0.015...-0.015]                                     |
| $\underline{r}_{gov}$                    | Floor on the government interest rate                                                                                        | 0.00E+00                                              |
| $\tau^{c}_{t,s,j}$                       | Consumption tax rates                                                                                                        | Too large to report here, see default parameters JSON |
| $H$                                      | Coefficient on linear term in wealth tax function                                                                            | [1.000...1.000]                                       |
| $M$                                      | Constant in wealth tax function                                                                                              | [0.001...0.001]                                       |
| $P$                                      | Coefficient on level term in wealth tax function                                                                             | [0.004...0.004]                                       |
| $\tau^{BQ}_{t}$                          | Bequest (estate) tax rate                                                                                                    | [0.004...0.004]                                       |
| $\tau^{p}_{j,t}$                         | Payroll tax rate                                                                                                             | Too large to report here, see default parameters JSON |
| $\chi^{b}_{j}$                           | Utility of bequests level parameters                                                                                         | [80.000...80.000]                                     |
| $\chi^{n}_{s,t}$                         | Disutility of labor level parameters                                                                                         | Too large to report here, see default parameters JSON |
| $\eta_{j,s,t}$                           | Distribution of transfers                                                                                                    | Too large to report here, see default parameters JSON |
| $\eta_{RM,j,s,t}$                        | Distribution of remittances                                                                                                  | Too large to report here, see default parameters JSON |
| $\zeta_{j,s,t}$                          | Distribution of bequests                                                                                                     | Too large to report here, see default parameters JSON |
| $\texttt{use_zeta}$                      | Whether to distribute bequests between lifetime income groups                                                                | 0.00E+00                                              |
| $\texttt{analytical_mtrs}$               | Whether use analytical MTRs or estimate MTRs                                                                                 | 0.00E+00                                              |
| $\texttt{age_specific}$                  | Whether use age-specific tax functions                                                                                       | 1.000                                                 |
| $R$                                      | Retirement age                                                                                                               | [60.000...60.000]                                     |
| $\texttt{avg_earn_num_years}$            | Number of years over which compute average earnings for pension benefit                                                      | Too large to report here, see default parameters JSON |
| $\texttt{AIME_bkt_1}$                    | First AIME bracket threshold                                                                                                 | 749.000                                               |
| $\texttt{AIME_bkt_2}$                    | Second AIME bracket threshold                                                                                                | 4517.000                                              |
| $\texttt{PIA_rate_bkt_1}$                | First AIME bracket PIA rate                                                                                                  | 0.00E+00                                              |
| $\texttt{PIA_rate_bkt_2}$                | Second AIME bracket PIA rate                                                                                                 | 0.00E+00                                              |
| $\texttt{PIA_rate_bkt_3}$                | Third AIME bracket PIA rate                                                                                                  | 0.00E+00                                              |
| $\texttt{PIA_maxpayment}$                | Maximum PIA payment                                                                                                          | 0.00E+00                                              |
| $\texttt{PIA_minpayment}$                | Minimum PIA payment                                                                                                          | 0.00E+00                                              |
| $\theta_{adj,t}$                         | Adjustment to replacement rate                                                                                               | Too large to report here, see default parameters JSON |
| $\texttt{budget_balance}$                | Whether have a balanced budget in each period                                                                                | 0.00E+00                                              |
| $\texttt{baseline_spending}$             | Whether level of spending constant between the baseline and reform runs                                                      | 0.00E+00                                              |
| $\texttt{baseline_theta}$                | Flag for use in reform simulations to keep Social Security system replacement rate constant between baseline and reform runs | 0.00E+00                                              |
| $\texttt{use_sparse_FOC_jac}$            | Use a banded finite-difference Jacobian in the household solver                                                              | 1.000                                                 |
| $\texttt{start_year}$                    | Initial year                                                                                                                 | 2025                                                  |
| $\texttt{tax_func_type}$                 | Functional form used for income tax functions                                                                                | GS                                                    |
| $\xi$                                    | Dampening parameter for TPI                                                                                                  | 0.200                                                 |
| $\texttt{maxiter}$                       | Maximum number of iterations for TPI                                                                                         | 250                                                   |
| $\texttt{mindist_SS}$                    | SS solution tolerance                                                                                                        | 1.00E-09                                              |
| $\texttt{mindist_TPI}$                   | TPI solution tolerance                                                                                                       | 1.00E-05                                              |
| \texttt{initial\_guess\_b\_SS}           | Initial guess for SS savings (use_zeta True)                                                                                 | 0.005                                                 |
| \texttt{initial\_guess\_n\_SS}           | Initial guess for SS labor supply (use_zeta True)                                                                            | 0.400                                                 |
| \texttt{initial\_guess\_b\_SS\_no\_zeta} | Initial guess for SS savings (use_zeta False)                                                                                | 0.070                                                 |
| \texttt{initial\_guess\_n\_SS\_no\_zeta} | Initial guess for SS labor supply (use_zeta False)                                                                           | 0.350                                                 |
| $\omega_{s,t}$                           | Population by age over time                                                                                                  | Too large to report here, see default parameters JSON |
| $\bar{\omega}_s$                         | Steady-state population distribution                                                                                         | Too large to report here, see default parameters JSON |
| $g_{n,t}$                                | Population growth rate over the time path                                                                                    | [0.019...-0.006]                                      |
| $\bar{g}_n$                              | Population growth rate in the steady-state                                                                                   | -5.64E-03                                             |
| $i_{s,t}$                                | Immigration rates by age                                                                                                     | Too large to report here, see default parameters JSON |
| $\rho_{s,t}$                             | Mortality rates by age                                                                                                       | Too large to report here, see default parameters JSON |
