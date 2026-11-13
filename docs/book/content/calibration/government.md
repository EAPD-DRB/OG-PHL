(Chap_GovCalib)=
# Calibration of Government Parameters

## Government Transfers as a Share of GDP

We calibrate Philippine government spending on transfer programs at 4.48% of GDP, using World Bank World Development Indicators data for 2023. OG-Core multiplies $\alpha_T$ by its own output, which excludes consumption taxes, so the packaged value is $\alpha_T = 0.0487$, the same 4.48% of GDP at market prices (see {ref}`Chap_MacroCalib`). The same conversion, a factor of 1.086, applies to every spending share below.

## Government Spending as a Share of GDP

Government spending on goods and services, $\alpha_G$, is not set to the observed spending share. It follows the government's own fiscal program where the program is data and the level consistent with the debt target after that: 9.5%, 9.2%, 8.4% and 7.5% of GDP for 2025–2028, the values that reproduce the Medium-Term Fiscal Framework's programmed primary balance given the model's revenue and pension outlays, then 6.5% of GDP from 2029 until the budget rule takes over in 2045. The derivation, and why the observed share of about 13% of GDP on a primary basis cannot be used, are in {ref}`Chap_MacroCalib`.

### Government spending on infrastructure as a share of GDP

Public investment follows the infrastructure program of the DBM Budget of Expenditures and Sources of Financing for FY 2026, Table A2 ([source](https://www.dbm.gov.ph/wp-content/uploads/BESF/BESF2026/A2.pdf)), "Infrastructure Program (Disbursements), Percent of GDP": 5.3% of GDP for 2025, 5.1% for 2026 and 2027, and 5.2% from 2028, packaged as $\alpha_I = [0.0576, 0.0554, 0.0554, 0.0565]$ of the model's output.

## Public pensions

The Philippines has three public pension schemes: the Social Security System (SSS) for private-sector workers, the Government Service Insurance System (GSIS) for civil servants, and the uniformed-service pensions paid from the national budget's Pension and Gratuity Fund. Together they paid about 2.28% of GDP in benefits: SSS ₱257.4 billion in 2023 (1.06% of GDP), GSIS ₱179.9 billion in 2024 (0.68%), and the Pension and Gratuity Fund ₱143.0 billion in the 2024 General Appropriations Act (0.54%). The OECD's *Pensions at a Glance Asia/Pacific 2024* reports 7.7% of GDP for public pension spending without a breakdown; it cannot be reconciled with the paying institutions' own totals, which this calibration uses. (Earlier versions of the calibration switched pensions off entirely, with the US benefit formula's rates set to zero, while the payroll tax collected the contributions.)

The model uses OG-Core's defined-benefit system with the SSS rules (Republic Act 11199; OECD *Pensions at a Glance Asia/Pacific 2024*):

- **Pension age** 60 (`retirement_age`), after a career of 40 years (`yr_contrib`).
- **Benefit rate** `alpha_db` = 0.0217 per year of contribution. The SSS benefit is 20% of average monthly earnings plus 2% for each credited year beyond ten, which over a 40-year career is 80%, almost exactly 2% a year; it is paid 13 times a year, so $0.02 \times 13/12$.
- **Earnings base** the average of the last five years (`avg_earn_num_years` = 5). The SSS pays on the greater of the last five years' average or the career average; salary credits are nominal and unindexed, so the last five years is the larger in practice.
- **Coverage** by lifetime-income group, `replacement_rate_adjust` = $[0, 0, 0.5, 1, 1, 1, 1] \times 0.856$ for the mature system: the formal groups draw a pension (about 36% of the employed contribute to SSS or GSIS), and the informal groups do not. The scale also carries generosity, so it may exceed one: the SSS formula is the base, but GSIS and uniformed-service pensions (54% of spending) pay more (GSIS reaches 90% replacement), and the formula's flat ₱1,000 and ₱300 components (about 8% of average earnings) are not modeled.

The scale is set so outlays match spending, but at the right point in time. OG-Core pays every retiree as if the system had always existed, so its steady state is a *mature* system in the long-run population, while today's 2.28% comes from a young population. The steady-state target is therefore today's spending times the rise in covered retirees per worker between 2025 and the steady state, 3.06 (from the model's own population arrays, weighted by coverage, since the covered groups live longer): 6.97% of GDP.

**The system matures over 25 years.** A mature system from the first year pays about 2.8% of GDP in 2025, a quarter more than today's 2.28%: today's retirees built their entitlements when coverage was lower than the model's formal groups now imply. The scale therefore starts at 80% of its mature value in 2025 and rises linearly to it in 2050 (`replacement_rate_adjust` has one row per year to 2050; the steady state uses the last). The 25 years follow OG-THA, where the same mature-from-the-start error paid 4.8% of GDP against 2.1% and a 25-year phase-in matched today's spending; no Philippine series fixes the length, so it is an assumption. The solved transition pays 2.27% of GDP in 2025, 2.64% in 2030, 3.21% in 2040, 4.17% in 2050 and 6.7–6.8% from about 2075, when the population has aged into the steady state.

**A long-run fiscal consequence.** With tax rates held at today's collections, a mature pension system in an aged population squeezes the rest of the budget. In the steady state the budget rule sets government consumption to about 3.2% of GDP, against 14.7% today. That is the model's answer to the question "current tax and pension policy, forever, in the long-run population"; it is not a fitting error, and the pension rates are deliberately not shrunk to avoid it. Raising contributions or adjusting benefits are natural reform scenarios to study against this baseline.
