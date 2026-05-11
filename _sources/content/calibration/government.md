(Chap_GovCalib)=
# Calibration of Government Parameters

## Government Transfers as a Share of GDP

We calibrate Philippine government spending on transfer programs as a percent of GDP as $\alpha_T=[0.0448]$, using World Bank World Development Indicators data for 2023.

## Government Spending as a Share of GDP

The Department of Budget and Management (DBM), Budget of Expenditures and Sources of Financing (BESF) for FY 2026, Table A2 ([source](https://www.dbm.gov.ph/wp-content/uploads/BESF/BESF2026/A2.pdf)) forecasts total federal disbursements as a percent of GDP in 2026, 2027, and 2028 as 21.5%, 20.8%, and 20.6%, respectively. To get the portion that is net of transfers, we subtract off the calibrated share of spending on transfers $\alpha_T=[0.0448]$ from each. This gives our calibration for government spending net of transfers as a percent of GDP for 2026, 2027, and 2028 as $\alpha_G=[0.1702, 0.1632, 0.1612]$.


### Government spending on infrastructure as a share of GDP

We calibrate the vector $\alpha_I=[0.051, 0.051, 0.052]$. These values are forecasts for 2026, 2027, and 2028, taken directly from the "Infrastructure Program (Disbursements), Percent of GDP" row of the DBM, BESF for FY 2026, Table A2 ([source](https://www.dbm.gov.ph/wp-content/uploads/BESF/BESF2026/A2.pdf)).
