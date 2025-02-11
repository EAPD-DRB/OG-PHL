"""
This module uses data from World Bank WDI, World Bank Quarterly Public
Sector Debt (QPSD) database, the IMF, and UN ILO to find values for
parameters for the OG-PHL model that rely on macro data for calibration.
"""

# imports
from pandas_datareader import wb
import pandas as pd
import numpy as np
import requests
import datetime
import statsmodels.api as sm
from io import StringIO


def get_macro_params(
    data_start_date=datetime.datetime(1947, 1, 1),
    data_end_date=datetime.datetime(2023, 1, 1),
    country_iso="PHL",
):
    """
    Compute values of parameters that are derived from macro data

    Args:
        data_start_date (datetime): start date for data
        data_end_date (datetime): end date for data
        country_iso (str): ISO code for country

    Returns:
        macro_parameters (dict): dictionary of parameter values
    """
    # initialize a dictionary of parameters
    macro_parameters = {}

    """
    Retrieve data from the World Bank World Development Indicators.
    """
    # Dictionaries of variables and their corresponding World Bank codes
    # Annual data
    wb_a_variable_dict = {
        "GDP per capita (constant 2015 US$)": "NY.GDP.PCAP.KD",
        "Real GDP (constant 2015 US$)": "NY.GDP.MKTP.KD",
        "Nominal GDP (current US$)": "NY.GDP.MKTP.CD",
        "General government final consumption expenditure (current US$)": "NE.CON.GOVT.CD",
        "External debt stocks, public and publicly guaranteed (PPG) (DOD, current US$)": "DT.DOD.DPPG.CD",
        "External debt stocks, total (DOD, current US$)": "DT.DOD.DECT.CD",
        r"External debt stocks (% of GNI)": "DT.DOD.DECT.GN.ZS",
        r"Central government debt, total (% of GDP)": "GC.DOD.TOTL.GD.ZS",
        r"General government final consumption expenditure (% of GDP)": "NE.CON.GOVT.ZS",
    }
    try:
        # pull series of interest from the WB using pandas_datareader
        # Annual data
        wb_data_a = wb.WorldBankReader(
            symbols=wb_a_variable_dict.values(),
            countries=country_iso,
            start=data_start_date,
            end=data_end_date,
            freq="A",
        ).read()
        wb_data_a.rename(
            columns=dict((y, x) for x, y in wb_a_variable_dict.items()),
            inplace=True,
        )
        # Remove the hierarchical index (country and year) of
        # wb_data_a and create a single row index using year
        wb_data_a.reset_index(inplace=True)
        wb_data_a["year"] = wb_data_a.year.astype(int)
        wb_data_a = wb_data_a.set_index("year")
        # Compute macro parameters from WB data
        # Latest from WB WDI data is 2014, so use: https://www.treasury.gov.ph/?p=64737
        macro_parameters["initial_debt_ratio"] = 0.60
        macro_parameters["initial_foreign_debt_ratio"] = (
            pd.Series(
                wb_data_a[r"External debt stocks (% of GNI)"]
                * (
                    wb_data_a[
                        "External debt stocks, public and publicly guaranteed (PPG) (DOD, current US$)"
                    ]
                    / wb_data_a[
                        "External debt stocks, total (DOD, current US$)"
                    ]
                )
            ).loc[data_end_date.year - 2]
            / 100
        )
        # zeta_D = share of new debt issues from government that are
        # purchased by foreigners
        # set to initial ratio without better info
        macro_parameters["zeta_D"] = [
            macro_parameters["initial_foreign_debt_ratio"]
        ]
        macro_parameters["g_y_annual"] = (
            wb_data_a["GDP per capita (constant 2015 US$)"]
            .loc[2000:2019]  # stop pre-COVID
            .pct_change()
            .mean()
        )
        macro_parameters["alpha_G"] = [
            (
                wb_data_a[
                    r"General government final consumption expenditure (% of GDP)"
                ].loc[data_end_date.year]
                / 100
            )
        ]
    except:
        print("Failed to retrieve data from World Bank")
        print("Will not update the following parameters:")
        print(
            "[initial_debt_ratio, initial_foreign_debt_ratio, zeta_D, g_y, alpha_G]"
        )

    """
    Retrieve labour share data from the United Nations ILOSTAT Data API
    (see https://rshiny.ilo.org/dataexplorer9/?lang=en)
    """
    target = (
        "https://rplumber.ilo.org/data/indicator/"
        + "?id=LAP_2GDP_NOC_RT_A"
        + "&ref_area="
        + str(country_iso)
        + "&timefrom="
        + str(data_start_date.year)
        + "&timeto="
        + str(data_end_date.year)
        + "&type=both&format=.csv"
    )
    response = requests.get(target)
    if response.status_code == 200:
        csv_content = StringIO(response.text)
        df_temp = pd.read_csv(csv_content)
    else:
        print(
            f"Failed to retrieve data. HTTP status code: {response.status_code}"
        )
    ilo_data = df_temp[["time", "obs_value"]]
    # find gamma, capital's share of income
    macro_parameters["gamma"] = [
        1
        - (
            (
                ilo_data.loc[
                    ilo_data["time"] == min(data_end_date.year, 2021),
                    "obs_value",  # 2021 is latest year of data
                ].squeeze()
            )
            / 100
        )
    ]

    """
    Calibrate parameters from IMF data
    """
    # alpha_T, non-social security benefits as a fraction of GDP
    # can't find this specifically, so use primary expenditures minus
    # final consumption expenditures
    # source: https://www.imf.org/external/datamapper/profile/PHL
    macro_parameters["alpha_T"] = [0.2391 - 0.142]

    """"
    Esimate the discount on sovereign yields relative to private debt
    Follow the methodology in Li, Magud, Werner, Witte (2021)
    available at:
    https://www.imf.org/en/Publications/WP/Issues/2021/06/04/The-Long-Run-Impact-of-Sovereign-Yields-on-Corporate-Yields-in-Emerging-Markets-50224

    Steps:
    1) Generate modelled corporate yields (corp_yhat) for a range of
    sovereign yields (sov_y)  using the estimated equation in col 2 of
    table 8 (and figure 3). 2) Estimate the OLS using sovereign yields
    as the dependent variable
    """

    # # estimate r_gov_shift and r_gov_scale
    sov_y = np.arange(20, 120) / 10
    corp_yhat = 8.199 - (2.975 * sov_y) + (0.478 * sov_y**2)
    corp_yhat = sm.add_constant(corp_yhat)
    mod = sm.OLS(
        sov_y,
        corp_yhat,
    )
    res = mod.fit()
    # First term is the constant and needs to be divided by 100 to have
    # the correct unit. Second term is the coefficient
    macro_parameters["r_gov_shift"] = [-res.params[0] / 100]
    macro_parameters["r_gov_scale"] = [res.params[1]]

    return macro_parameters
