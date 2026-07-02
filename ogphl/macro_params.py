"""
Macro parameters for the OG-PHL model.

Most OG-PHL macro parameters are documented, point-in-time Philippine values
held in the packaged default-parameter JSON. Only a parameter whose documented
source is genuinely a live API is refreshed here when ``update_from_api=True``;
the rest stay in the JSON so a live update cannot clobber a value we source
elsewhere. In particular the IMF GFS and World-Bank external-debt calls are NOT
used: the values they overwrote come from other sources (World Bank WDI, DBM
budget tables, the Bureau of the Treasury), and the IMF GFS social-benefit
series is zero for the Philippines, which set ``alpha_T=0`` and broke the
steady-state solve. Demographics stay live (UN) in ``ogphl.calibrate``.
"""

import datetime

import pandas as pd
import requests

GDP_GROWTH_START_YEAR = 2000
GDP_GROWTH_END_YEAR = 2019


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
                f"No dated observations in World Bank response for "
                f"{indicator_code}"
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


def get_macro_params(
    data_start_date=datetime.datetime(1947, 1, 1),
    data_end_date=datetime.datetime(2023, 1, 1),
    country_iso="PHL",
    update_from_api=False,
    imf_data_path=None,
):
    """
    Return macro-parameter overrides for the OG-PHL calibration.

    Only ``g_y_annual`` is refreshed from a live API -- World Bank
    GDP-per-capita growth over the pre-pandemic 2000-2019 window, its
    documented source. Every other macro parameter is held in the packaged
    JSON and is NOT pulled here, so a live update cannot clobber a value
    sourced elsewhere:

      * alpha_T                    -- World Bank WDI (not the IMF GFS series,
                                      which is 0 for PH)
      * alpha_G                    -- DBM BESF FY2026, Table A2 (not an API)
      * initial_foreign_debt_ratio, zeta_D, initial_debt_ratio -- Bureau of the
                                      Treasury (not an API)
      * gamma                      -- ILOSTAT-based private capital share,
                                      frozen at the documented 0.53785
                                      (0.588 total, less gamma_g=0.05)
      * r_gov_shift, r_gov_scale   -- IMF / Li et al. (2021), frozen at the
                                      recentered documented values

    Returns:
        dict: macro-parameter overlay (only ``g_y_annual`` when
        ``update_from_api`` and the World Bank call succeeds)
    """
    macro_parameters = {}
    if update_from_api:
        try:
            wb_data = _annual_index(
                _fetch_wb_data(
                    {"GDP per capita (constant 2015 US$)": "NY.GDP.PCAP.KD"},
                    country_iso,
                    data_start_date.year,
                    data_end_date.year,
                    source=2,
                )
            )
            # Pre-pandemic window avoids COVID-era volatility distorting the
            # steady-state productivity target (docs/calibration/macro.md).
            macro_parameters["g_y_annual"] = (
                wb_data["GDP per capita (constant 2015 US$)"]
                .loc[GDP_GROWTH_START_YEAR:GDP_GROWTH_END_YEAR]
                .pct_change()
                .mean()
            )
            print(
                "g_y_annual updated from World Bank API: "
                f"{macro_parameters['g_y_annual']}"
            )
        except Exception:
            print(
                "Failed to retrieve g_y_annual from World Bank; "
                "keeping packaged value"
            )
    else:
        print("Not updating macro params from World Bank API")
    return macro_parameters
