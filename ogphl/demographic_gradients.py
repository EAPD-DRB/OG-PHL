"""
Income gradients in fertility and mortality for OG-Core's demographics.

Since ogcore 0.18, fertility, mortality and infant mortality can differ by
lifetime-income group. The gradients come from the EAPD-DRB
Demographic-Gradients library:

  * fertility and infant and under-five mortality: the Philippines' own DHS
    2022 wealth-quintile tilts (ogphl/data/demographic_gradients_PHL.csv);
  * adult mortality: the library has no Philippine census measurement, so
    the tilt comes from its cross-country income rule (general_gradient.csv,
    fitted on 17 censuses between about $200 and $10,000 of GNI per head,
    r = -0.88, leave-one-out mean absolute error 0.14),
        tilt(45q15) = 1.291 - 0.2443 ln(GNI per capita, current US$),
    plus the library's offsets for each age band (median absolute error
    0.17). The rule steepens as income grows, so the tilt follows GNI per
    head along the model's own growth rate, capped where the rule's fit
    ends. This is the lower rung of the library's ladder (OG-ETH uses a
    measured census gradient); replace it with a Philippine measurement
    when one is published.

A tilt is the change in the log rate from the bottom to the top of the
wealth distribution. OG-Core reads a log-odds slope per centered percentile
point, so each tilt is passed as tilt / (100 x (1 - p)), with p OG-Core's own
rate at that age (the library's conversion rule, verified against ogcore
0.24.1). Fertility goes in by age: the Philippine TFR tilt plus the library's
pooled age offsets (data/fertility_age_offsets.csv), because the rich-poor
fertility gap is mostly one of timing.
"""

import os

import numpy as np
import pandas as pd
from ogcore import demographics

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
GRADIENT_FILE = os.path.join(CUR_PATH, "data", "demographic_gradients_PHL.csv")
AGE_OFFSET_FILE = os.path.join(CUR_PATH, "data", "fertility_age_offsets.csv")
TILT_PER_PERCENTILE = 1 / 100
UN_COUNTRY_CODE = "608"
# ages 1-4 take the under-five tilt; age 0 is handled by infmort_gradient
UNDER_FIVE_AGES = (1, 5)
# the library's adult-mortality income rule and its age-band offsets
INCOME_RULE_INTERCEPT = 1.291
INCOME_RULE_SLOPE = -0.2443
INCOME_RULE_MAX_GNI = 10000.0
AGE_BAND_OFFSETS = {
    (15, 29): -0.407,
    (30, 44): -0.2001,
    (45, 59): 0.1338,
    (60, 74): 0.3972,
}
# World Bank Atlas GNI per capita, current US$ (NY.GNP.PCAP.CD)
GNI_PER_CAPITA = 4470.0
GNI_YEAR = 2024


def adult_mortality_tilts(gni):
    """
    Adult-mortality tilt for each age band at a level of GNI per head.

    Args:
        gni (array_like): GNI per capita, current US$

    Returns:
        tilts (dict): age band (lo, hi) -> tilt, same shape as gni
    """
    gni = np.minimum(np.asarray(gni, dtype=float), INCOME_RULE_MAX_GNI)
    base = INCOME_RULE_INTERCEPT + INCOME_RULE_SLOPE * np.log(gni)
    return {band: base + off for band, off in AGE_BAND_OFFSETS.items()}


def fertility_age_offsets(ages, path=AGE_OFFSET_FILE):
    """
    The library's pooled fertility age offsets at single ages; ages outside
    the reported five-year bands take the nearest band.

    Args:
        ages (array_like): ages in years
        path (str): CSV of pooled offsets by five-year band

    Returns:
        offsets (Numpy array): offset to add to the TFR tilt at each age
    """
    df = pd.read_csv(path).set_index("age_lo")["offset"]
    lo = np.clip(np.asarray(ages) // 5 * 5, df.index.min(), df.index.max())
    return df.loc[lo].to_numpy()


def ogcore_rates(E, S, start_year):
    """
    OG-Core's own fertility and mortality rates for the Philippines in the
    last data year the model reads (rates are held constant after it).

    Returns:
        fert (Numpy array): births per person by age, length E+S
        mort (Numpy array): probability of death by age, length E+S
        infmort (float): infant mortality rate
    """
    fert = demographics.get_fert(
        E + S, 0, 99, UN_COUNTRY_CODE, start_year - 1, start_year + 1
    )
    mort, infmort = demographics.get_mort(
        E + S, 0, 99, UN_COUNTRY_CODE, start_year - 1, start_year + 1
    )
    return (
        np.atleast_2d(fert)[-1],
        np.atleast_2d(mort)[-1],
        float(np.atleast_1d(infmort)[-1]),
    )


def demographic_gradients(
    E, S, T, start_year, g_y_annual, path=GRADIENT_FILE, rates=None
):
    """
    Income gradients ready for ogcore's get_pop_objs.

    Args:
        E (int): age at which agents become economically active
        S (int): number of model periods in a lifetime
        T (int): number of periods in the transition path
        start_year (int): calendar year of the first model period
        g_y_annual (float): annual growth of income per head
        path (str): CSV with the library's Philippine DHS rows
        rates (tuple): (fert, mort, infmort) as returned by ogcore_rates;
            fetched when None

    Returns:
        gradients (dict): fert_gradient (by age, length E+S),
            infmort_gradient (scalar) and mort_gradient (size (T+S, E+S),
            by period and single age)
    """
    df = pd.read_csv(path)

    def tilt(indicator):
        rows = df[df.indicator == indicator]
        if rows.empty:
            raise ValueError(f"No {indicator} gradient in {path}")
        return float(rows.slope.iloc[0])

    fert_p, mort_p, infmort_p = (
        ogcore_rates(E, S, start_year) if rates is None else rates
    )
    years = start_year + np.arange(T + S)
    gni = GNI_PER_CAPITA * (1 + g_y_annual) ** (years - GNI_YEAR)
    bands = adult_mortality_tilts(gni)
    ages = np.arange(E + S)
    mort = np.zeros((T + S, E + S))
    u5 = (ages >= UNDER_FIVE_AGES[0]) & (ages < UNDER_FIVE_AGES[1])
    mort[:, u5] = tilt("U5MR")
    for (lo, hi), band_tilt in bands.items():
        sel = (ages >= lo) & (ages <= hi)
        mort[:, sel] = band_tilt.reshape(-1, 1)
    fert_tilt = tilt("TFR") + fertility_age_offsets(ages)
    return {
        "fert_gradient": fert_tilt * TILT_PER_PERCENTILE / (1 - fert_p),
        "infmort_gradient": (
            tilt("IMR") * TILT_PER_PERCENTILE / (1 - infmort_p)
        ),
        "mort_gradient": mort * TILT_PER_PERCENTILE / (1 - mort_p),
    }
