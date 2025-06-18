(Chap_FirmCalib)=
# Calibration of Firms Parameters

## Aggregate Production Function and Capital Accumulation

The [OG-Core firm theory documentation](https://pslmodels.github.io/OG-Core/content/theory/firms.html) outlines the constant returns to scale, constant elasticity of substitution production function of the representative firm.  This function has two parameters; the elasticity of substitution and capital's share of output.

### Elasticity of substitution

`OG-PHL`'s default parameterization has an elasticity of substitution of $\varepsilon=1.0$, which implies a Cobb-Douglas production function.

### Capital's share of output

Philippine national accounts data suggest that the capital share of income is 58.785%. However, we allocate 5% of that to infrastructure investment $\gamma_{g,m}=0.05$ for all $m$ and $\gamma_m=0.53785$. We are simply allocating 5% of the capital share of output to infrastructure investment. We tried a higher percentage of 10% to infrastructure investment, but the steady-state solution would not solve.
