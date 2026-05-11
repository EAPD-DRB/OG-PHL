"""
This module uses data from World Bank WDI, the IMF, and UN ILO to find
values for parameters for the OG-PHL model that rely on macro data for
calibration.
"""

# imports
import datetime
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests

GDP_GROWTH_START_YEAR = 2000
GDP_GROWTH_END_YEAR = 2019
EXTERNAL_DEBT_REPORTING_LAG_YEARS = 2
ILOSTAT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}


def _fetch_wb_data(indicators, country_iso, start_year, end_year, source):
    """
    Fetch a set of World Bank indicators and return a single DataFrame.

    Args:
        indicators (dict): mapping of human-readable labels to indicator codes
        country_iso (str): ISO country code
        start_year (int): first year to request
        end_year (int): last year to request
        source (int): World Bank source ID

    Returns:
        pandas.DataFrame: DataFrame indexed by year/quarter label
    """
    if source == 2:
        date_range = f"{start_year}:{end_year}"
    elif source == 20:
        date_range = f"{start_year}Q1:{end_year}Q4"
    else:
        raise ValueError(f"Unsupported World Bank source: {source}")

    data_frames = []
    for label, indicator_code in indicators.items():
        response = requests.get(
            (
                "https://api.worldbank.org/v2/country/"
                f"{country_iso}/indicator/{indicator_code}"
            ),
            params={
                "date": date_range,
                "source": source,
                "format": "json",
                "per_page": 10000,
            },
            timeout=30,
        )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError(
                f"Malformed World Bank response for {indicator_code}"
            ) from exc

        if (
            not isinstance(payload, list)
            or len(payload) < 2
            or not isinstance(payload[1], list)
            or not payload[1]
        ):
            raise ValueError(
                f"Empty or malformed World Bank response for {indicator_code}"
            )

        series_data = {}
        for row in payload[1]:
            date = row.get("date")
            if date is None:
                continue
            series_data[date] = row.get("value")

        if not series_data:
            raise ValueError(
                f"No dated observations in World Bank response for {indicator_code}"
            )

        series = pd.Series(series_data, name=label)
        series = pd.to_numeric(series, errors="coerce")
        data_frames.append(series.to_frame())

    data = pd.concat(data_frames, axis=1)
    data.index.name = "year"
    return data.sort_index(ascending=False)


def _annual_index(data):
    """
    Convert a World Bank annual response index to integer years.
    """
    annual_data = data.copy()
    annual_data.index = pd.to_numeric(annual_data.index, errors="coerce")
    annual_data = annual_data.loc[annual_data.index.notna()]
    annual_data.index = annual_data.index.astype(int)
    return annual_data.sort_index()


def _latest_at_or_before(series, target_year, source_name):
    """
    Return the value for target_year or the latest nonmissing prior year.
    """
    valid = series.dropna()
    valid = valid.loc[valid.index <= int(target_year)]
    if valid.empty:
        raise ValueError(
            f"No complete {source_name} data available up to {target_year}"
        )

    selected_year = (
        int(target_year)
        if int(target_year) in valid.index
        else int(valid.index.max())
    )
    if selected_year != int(target_year):
        print(
            f"Warning: No {source_name} data for {target_year}. "
            f"Using last available year: {selected_year}"
        )
    return valid.loc[selected_year]


def _get_imf_macro_params(country_iso, target_year, data_path=None):
    """
    Fetch IMF GFS data and compute alpha_T and alpha_G.

    Args:
        country_iso (str): ISO alpha-3 country code
        target_year (int): preferred calibration year
        data_path (str | Path | None): optional path to save IMF CSV data

    Returns:
        dict: IMF-derived macro parameters
    """
    required_indicators = {"G2_T", "G24_T", "G27_T", "G271_T"}
    data_path = Path(data_path) if data_path is not None else None
    response = requests.get(
        (
            "https://api.imf.org/external/sdmx/3.0/data/dataflow/"
            f"IMF.STA/GFS_SOO/12.0.0/"
            f"{country_iso}.S1311.G2M.*.POGDP_PT.A"
        ),
        timeout=30,
    )
    response.raise_for_status()
    try:
        payload = response.json()
        data = payload["data"]
        structure = data["structures"][0]
        data_set = data["dataSets"][0]
        series_dimensions = structure["dimensions"]["series"]
        observation_years = [
            value.get("id", value.get("value"))
            for value in structure["dimensions"]["observation"][0]["values"]
        ]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ValueError(
            "Empty or malformed IMF response for GFS_SOO"
        ) from exc

    records = []
    for series_key, series in data_set["series"].items():
        dimension_indexes = [int(idx) for idx in series_key.split(":")]
        labels = {
            dim["id"]: dim["values"][idx]["id"]
            for dim, idx in zip(series_dimensions, dimension_indexes)
        }
        indicator = labels.get("INDICATOR")
        if indicator not in required_indicators:
            continue
        for observation_key, observation in series.get(
            "observations", {}
        ).items():
            value = observation[0]
            if value is None:
                continue
            records.append(
                {
                    "year": observation_years[int(observation_key)],
                    "indicator": indicator,
                    "value": float(value),
                    "country_iso": country_iso,
                    "sector": "S1311",
                    "dataset": "IMF.STA:GFS_SOO(12.0.0)",
                }
            )

    imf_data = pd.DataFrame(records)
    if imf_data.empty:
        raise ValueError("Empty or malformed IMF response for GFS_SOO")

    if data_path is not None:
        data_path.parent.mkdir(parents=True, exist_ok=True)
        imf_data.sort_values(["indicator", "year"]).to_csv(
            data_path, index=False
        )
        print(f"IMF data saved to {data_path}")

    imf_data["year"] = pd.to_numeric(imf_data["year"], errors="coerce")
    imf_data["value"] = pd.to_numeric(imf_data["value"], errors="coerce")
    imf_data = imf_data.dropna(subset=["year", "value"])

    available = (
        imf_data.pivot_table(
            index="year",
            columns="indicator",
            values="value",
            aggfunc="first",
        )
        .sort_index()
        .dropna(subset=sorted(required_indicators))
    )
    available = available.loc[available.index <= int(target_year)]

    if available.empty:
        raise ValueError(
            f"No complete IMF data available for {country_iso} up to {target_year}"
        )

    selected_year = (
        int(target_year)
        if int(target_year) in available.index
        else int(available.index.max())
    )
    if selected_year != int(target_year):
        print(
            f"Warning: No IMF data for {target_year}. "
            f"Using last available year: {selected_year}"
        )

    values = available.loc[selected_year]
    return {
        "alpha_T": [(values["G27_T"] - values["G271_T"]) / 100],
        "alpha_G": [
            (values["G2_T"] - values["G24_T"] - values["G27_T"]) / 100
        ],
    }


def _get_ilo_gamma(country_iso, start_year, target_year):
    """
    Fetch ILO labor-share data and compute capital's share of income.
    """
    target = (
        "https://rplumber.ilo.org/data/indicator/"
        + "?id=LAP_2GDP_NOC_RT_A"
        + "&ref_area="
        + str(country_iso)
        + "&timefrom="
        + str(start_year)
        + "&type=both&format=.csv"
    )
    print("ILO data target = ", target)
    response = requests.get(target, headers=ILOSTAT_HEADERS, timeout=30)
    response.raise_for_status()
    ilo_data = pd.read_csv(StringIO(response.text))[["time", "obs_value"]]
    ilo_data["time"] = pd.to_numeric(ilo_data["time"], errors="coerce")
    ilo_data["obs_value"] = pd.to_numeric(
        ilo_data["obs_value"], errors="coerce"
    )
    ilo_data = ilo_data.dropna(subset=["time", "obs_value"])
    labor_share = _latest_at_or_before(
        ilo_data.set_index("time")["obs_value"],
        target_year,
        "ILOSTAT",
    )
    return [1 - (labor_share / 100)]


def get_macro_params(
    data_start_date=datetime.datetime(1947, 1, 1),
    data_end_date=datetime.datetime(2023, 1, 1),
    country_iso="PHL",
    update_from_api=False,
    imf_data_path=None,
):
    """
    Compute values of parameters that are derived from macro data.

    Args:
        data_start_date (datetime): start date for data
        data_end_date (datetime): end date for data
        country_iso (str): ISO code for country
        update_from_api (bool): Set True to pull updated macro data
        imf_data_path (str | Path | None): optional path to save IMF CSV data

    Returns:
        macro_parameters (dict): dictionary of parameter values
    """
    macro_parameters = {}

    wb_a_variable_dict = {
        "GDP per capita (constant 2015 US$)": "NY.GDP.PCAP.KD",
        "Real GDP (constant 2015 US$)": "NY.GDP.MKTP.KD",
        "Nominal GDP (current US$)": "NY.GDP.MKTP.CD",
        "General government final consumption expenditure (current US$)": "NE.CON.GOVT.CD",
        "External debt stocks, public and publicly guaranteed (PPG) (DOD, current US$)": "DT.DOD.DPPG.CD",
        "External debt stocks, total (DOD, current US$)": "DT.DOD.DECT.CD",
        r"External debt stocks (% of GNI)": "DT.DOD.DECT.GN.ZS",
    }

    if update_from_api:
        try:
            wb_data_a = _annual_index(
                _fetch_wb_data(
                    wb_a_variable_dict,
                    country_iso,
                    data_start_date.year,
                    data_end_date.year,
                    source=2,
                )
            )
            # Gross national government debt as a share of GDP. This is a
            # documented baseline source value, not computed from the WDI pull.
            macro_parameters["initial_debt_ratio"] = 0.60
            foreign_debt_ratio = (
                wb_data_a[r"External debt stocks (% of GNI)"]
                * (
                    wb_data_a[
                        "External debt stocks, public and publicly guaranteed (PPG) (DOD, current US$)"
                    ]
                    / wb_data_a[
                        "External debt stocks, total (DOD, current US$)"
                    ]
                )
                / 100
            )
            macro_parameters["initial_foreign_debt_ratio"] = (
                _latest_at_or_before(
                    foreign_debt_ratio,
                    data_end_date.year - EXTERNAL_DEBT_REPORTING_LAG_YEARS,
                    "World Bank external debt",
                )
            )
            macro_parameters["zeta_D"] = [
                macro_parameters["initial_foreign_debt_ratio"]
            ]
            macro_parameters["g_y_annual"] = (
                wb_data_a["GDP per capita (constant 2015 US$)"]
                # Use the pre-pandemic growth window to avoid COVID-era
                # volatility driving the steady-state productivity target.
                .loc[GDP_GROWTH_START_YEAR:GDP_GROWTH_END_YEAR]
                .pct_change()
                .mean()
            )
            print(
                f"initial_debt_ratio set from documented source: {macro_parameters['initial_debt_ratio']}"
            )
            print(
                f"initial_foreign_debt_ratio updated from World Bank API: {macro_parameters['initial_foreign_debt_ratio']}"
            )
            print(
                f"zeta_D updated from World Bank API: {macro_parameters['zeta_D']}"
            )
            print(
                f"g_y_annual updated from World Bank API: {macro_parameters['g_y_annual']}"
            )
        except Exception:
            print("Failed to retrieve data from World Bank")
            print("Will not update the following parameters:")
            print(
                "[initial_debt_ratio, initial_foreign_debt_ratio, zeta_D, g_y]"
            )
    else:
        print("Not updating from World Bank API")

    if update_from_api:
        try:
            macro_parameters["gamma"] = _get_ilo_gamma(
                country_iso,
                data_start_date.year,
                data_end_date.year,
            )
            print(
                f"gamma updated from ILOSTAT API: {macro_parameters['gamma']}"
            )
        except Exception:
            print("Failed to retrieve data from ILOSTAT")
            print("Will not update gamma")
    else:
        print("Not updating from ILOSTAT API")

    if update_from_api:
        try:
            macro_parameters.update(
                _get_imf_macro_params(
                    country_iso,
                    data_end_date.year,
                    data_path=imf_data_path,
                )
            )
            print(
                f"alpha_T updated from IMF data: {macro_parameters['alpha_T']}"
            )
            print(
                f"alpha_G updated from IMF data: {macro_parameters['alpha_G']}"
            )
        except Exception:
            print("Failed to retrieve data from IMF")
            print("Will not update alpha_T, alpha_G")

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
        try:
            import statsmodels.api as sm

            sov_y = np.arange(20, 120) / 10
            corp_yhat = 8.199 - (2.975 * sov_y) + (0.478 * sov_y**2)
            corp_yhat = sm.add_constant(corp_yhat)
            mod = sm.OLS(
                sov_y,
                corp_yhat,
            )
            res = mod.fit()
            # First term is the constant and needs to be divided by 100 to
            # have the correct unit. Second term is the coefficient.
            macro_parameters["r_gov_shift"] = [-res.params[0] / 100]
            macro_parameters["r_gov_scale"] = [res.params[1]]
            print(
                f"r_gov_shift updated from IMF data: {macro_parameters['r_gov_shift']}"
            )
            print(
                f"r_gov_scale updated from IMF data: {macro_parameters['r_gov_scale']}"
            )
        except Exception:
            print("Failed to compute r_gov_shift, r_gov_scale")
            print("Will not update r_gov_shift, r_gov_scale")
    else:
        print("Not updating alpha_T, alpha_G, r_gov_shift, r_gov_scale")

    return macro_parameters
