import numpy as np
import scipy.optimize as opt
import scipy.interpolate as si
from ogcore import parameter_plots as pp
from ogcore import utils
import csv
import os
import json
import urllib.request

CUR_PATH = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(CUR_PATH, "OUTPUT", "ability")


def get_e_interp(E, S, J, lambdas, age_wgts, gini_to_match=39.3, plot=False):
    """
    This function takes the calibrated lifetime earnings profiles
    (abilities, e matrix) from OG-USA and then adjusts the shape of those
    profiles to match the Gini coefficient for another economy. The
    Gini coefficient to match is given in the argument gini_to_match.
    Note that the calibrated OG-USA e matrix is of size (80, 10), where
    80 is the number of ages and 10 is the number of ability types.
    Users of this function specify their own number of age groups (S)
    and ability types (J). The function will map the fitted functions
    into these dimensions so long as the percentiles of the ability types
    given in lambdas is not more refined at the top end than those in
    OG-USA (which identifies up to the top 0.1%).

    Args:
        E (int): the age agents become economically active
        S (int): number of ages to interpolate. This method assumes that
            ages are evenly spaced between the beginning of age E
            up to E+S, >= 3
        J (int): number of ability types to interpolate
        lambdas (Numpy array): distribution of population in each
            ability group, length J
        age_wgts (Numpy array): distribution of population in each age
            group, length S; an SxJ age-by-income distribution (as
            returned by ogcore >= 0.18) is also accepted, in which case
            the age distribution is its sum over income groups
        gini_to_match (float): Gini coefficient to match, default is
            39.3, the World Bank PIP income Gini for PHL in 2023 (FIES;
            the same income concept as the US reference of 41.5, not the
            PIP consumption Gini of 35.2), https://pip.worldbank.org
        plot (bool): if True, creates plots of emat_orig and the new
            interpolated emat_new

    Returns:
        emat_new_scaled (Numpy array): interpolated ability matrix scaled
            so that population-weighted average is 1, size SxJ

    """
    lambdas = np.asarray(lambdas, dtype=float).flatten()
    assert lambdas.shape[0] == J
    age_wgts = np.asarray(age_wgts)
    if age_wgts.ndim == 2:  # SxJ from ogcore >= 0.18: age dist is the J-sum
        age_wgts = age_wgts.sum(axis=1)
    assert age_wgts.shape[0] == S
    # Load the USA e matrix as a baseline. Read the raw JSON values directly:
    # loading the snapshot through a Specifications object would couple this
    # function to the installed ogcore's array schema, which rejects the
    # snapshot whenever OG-USA and ogcore sit on different demographic
    # conventions (e.g. ogcore 0.18's SxJ arrays vs OG-USA's 1-D ones).
    usa_json = json.load(
        urllib.request.urlopen(
            "https://raw.githubusercontent.com/PSLmodels/OG-USA/master/ogusa/ogusa_default_parameters.json"
        )
    )
    usa_S = int(usa_json["S"])
    usa_J = int(usa_json["J"])
    # E is not stored in the JSON; derive it the way ogcore's
    # Specifications does from the ages and S.
    usa_E = int(
        usa_json["starting_age"]
        * (usa_S / (usa_json["ending_age"] - usa_json["starting_age"]))
    )
    usa_lambdas = np.array(usa_json["lambdas"])
    usa_e = np.array(usa_json["e"])
    if usa_e.ndim == 3:  # TxSxJ snapshot: use the first model period
        usa_e = usa_e[0, :, :]
    usa_omega_SS = np.array(usa_json["omega_SS"])
    if usa_omega_SS.ndim == 2:  # SxJ snapshot: age dist is the J-sum
        usa_omega_SS = usa_omega_SS.sum(axis=1)
    # Half one of the method (EAPD-DRB/OG-ZAF#18): reshape the US age pattern
    # to the Philippine one before tilting the income-group gaps.
    usa_e = apply_age_shape(usa_e, usa_E, usa_S)

    # Define a function that will find the "a" in the equation:
    # e_Y = e_USA * exp(a * e_USA)
    # such that the e_Y produces a gini coefficient in the model that
    # gives the same ratio between the model implied Gini's in the USA
    # and the target country and the empirical Gini's in the USA and given
    # by gin_to_match for the target country
    def f(
        a,
        emat_orig,
        age_wgts,
        abil_wgts,
        gini_to_match,
        gini_usa_data,
        gini_usa_model,
    ):
        gini_target_model = utils.Inequality(
            emat_orig * np.exp(a * emat_orig),
            age_wgts,
            abil_wgts,
            len(age_wgts),
            len(abil_wgts),
        ).gini()
        error = (gini_to_match / gini_usa_data) - (
            gini_target_model / gini_usa_model
        )
        return error

    # Note, USA gini in the World Bank data is 41.5
    # See https://data.worldbank.org/indicator/SI.POV.GINI
    gini_usa_data = 41.5
    # Find the model implied Gini for the USA
    gini_usa_model = utils.Inequality(
        usa_e,
        usa_omega_SS,
        usa_lambdas,
        usa_S,
        usa_J,
    ).gini()

    x = opt.root_scalar(
        f,
        args=(
            usa_e,
            usa_omega_SS,
            usa_lambdas,
            gini_to_match,
            gini_usa_data,
            gini_usa_model,
        ),
        method="bisect",
        bracket=[-1, 1],
        xtol=1e-10,
    )
    a = x.root
    e_new = usa_e * np.exp(a * usa_e)
    emat_new_scaled = (
        e_new
        / (
            e_new
            * usa_omega_SS.reshape(usa_S, 1)
            * usa_lambdas.reshape(1, usa_J)
        ).sum()
    )
    # Now interpolate for the cases where S and/or J not the same in the
    # country parameterization as in the default USA parameterization
    if (
        S == usa_S
        and np.array_equal(
            usa_lambdas,
            lambdas,
        )
        is True
    ):
        pass  # will return the e_new_scaled found above since dims the same
    else:
        # generate vector of mid points for the Filipino ability groups
        abil_midp = np.zeros(J)
        pct_lb = 0.0
        for j in range(J):
            abil_midp[j] = pct_lb + 0.5 * lambdas[j]
            pct_lb += lambdas[j]
        # generate vector of mid points for the USA ability groups
        M = usa_lambdas.shape[0]
        emat_j_midp = np.zeros(M)
        pct_lb = 0.0
        for m in range(M):
            emat_j_midp[m] = pct_lb + 0.5 * usa_lambdas[m]
            pct_lb += usa_lambdas[m]

        # Make sure that values in abil_midp are within interpolating
        # bounds
        if abil_midp.min() < emat_j_midp.min() or abil_midp.max() > (
            1 - usa_lambdas[-1]
        ):
            err = (
                "One or more entries in abilities vector (lambdas) is "
                + "outside the allowable bounds for interpolation."
            )
            raise RuntimeError(err)
        usa_step = 80 / usa_S
        emat_s_midp = np.linspace(
            usa_E + 0.5 * usa_step,
            usa_E + usa_S - 0.5 * usa_step,
            usa_S,
        )
        emat_j_mesh, emat_s_mesh = np.meshgrid(emat_j_midp, emat_s_midp)
        newstep = 80 / S
        new_s_midp = np.linspace(E + 0.5 * newstep, E + S - 0.5 * newstep, S)
        new_j_mesh, new_s_mesh = np.meshgrid(abil_midp, new_s_midp)
        newcoords = np.hstack(
            (
                emat_s_mesh.reshape((usa_S * usa_J, 1)),
                emat_j_mesh.reshape((usa_S * usa_J, 1)),
            )
        )
        emat_new = si.griddata(
            newcoords,
            emat_new_scaled.flatten(),
            (new_s_mesh, new_j_mesh),
            method="linear",
        )
        emat_new_scaled = (
            emat_new
            / (emat_new * age_wgts.reshape(S, 1) * lambdas.reshape(1, J)).sum()
        )

        if plot:
            kwargs = {"filesuffix": "_intrp_scaled"}
            pp.plot_income_data(
                new_s_midp,
                abil_midp,
                lambdas,
                emat_new_scaled,
                OUTPUT_DIR,
                **kwargs,
            )

    return emat_new_scaled


# ---------------------------------------------------------------------------
# Age shape of earnings (ported from OG-JPN's ogjpn/income.py)
#
# EAPD-DRB/OG-ZAF#18 sets out two adjustments to OG-USA's estimated lifetime
# earnings curves:
#   1. reshape the AGE pattern to the target country's own labour-income-by-
#      age profile   <- this section
#   2. tilt the gaps between the J income groups to the target country's
#      inequality <- get_e_interp above
# Both profiles are National Transfer Accounts labour income ("Labor Income",
# "Smooth Mean"), fetched by scripts/fetch_nta_age_profiles.py: the
# Philippines' latest (2015, prepared by M. Abrigo) against the nearest US
# year (2011). NTA labour income is per person at each age; the model's e is
# pay per hour and its labour supply is hours per person (ogphl/labor.py), so
# each profile is divided by that year's hours per person from ILOSTAT before
# the ratio is taken. Otherwise hours would count twice: once in e and again
# in the calibrated labour supply.
# ---------------------------------------------------------------------------

NTA_DIR = os.path.join(CUR_PATH, "data")

# ILOSTAT five-year bands placed at their midpoint; the open 65+ band at 67
HOURS_BAND_MIDPOINTS = {
    "15-19": 17,
    "20-24": 22,
    "25-29": 27,
    "30-34": 32,
    "35-39": 37,
    "40-44": 42,
    "45-49": 47,
    "50-54": 52,
    "55-59": 57,
    "60-64": 62,
    "65+": 67,
}

# Ages over which each profile is normalised before the ratio is taken. NTA
# reports levels in each country's own currency, so only the SHAPE transfers;
# normalising over prime working ages makes the two comparable.
NORMALISE_AGES = (20, 65)

# The factor is held flat from this age: it is the midpoint of ILOSTAT's open
# 65+ band, beyond which hours by age are not observed, and above it both NTA
# profiles approach zero and their ratio becomes noise.
FACTOR_TAPER_AGE = 67


def _load_nta_profile(iso):
    """
    Read one NTA labour-income age profile written by
    ``scripts/fetch_nta_age_profiles.py``.

    Args:
        iso (str): "PHL" or "USA"

    Returns:
        dict: {year (int): numpy array of income by single year of age 0-110}
    """
    path = os.path.join(NTA_DIR, f"nta_labor_income_{iso}.csv")
    out = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ages = []
            for age in range(0, 111):
                val = row.get(f"Age{age}", "")
                ages.append(float(val) if val not in ("", None) else np.nan)
            out[int(row["Year"])] = np.array(ages)
    return out


def hours_per_person(iso, year, ages):
    """
    Weekly hours worked per person by single year of age: the ILOSTAT
    employment-to-population ratio times the mean weekly hours of the
    employed, written by ``scripts/fetch_ilo_hours_by_age.py``. Bands sit at
    their midpoints; ages outside them take the nearest band's value.

    Args:
        iso (str): "PHL" or "USA"
        year (int): survey year
        ages (array_like): ages to evaluate at

    Returns:
        numpy array: hours per person per week at each age
    """
    path = os.path.join(NTA_DIR, "ilo_hours_by_age.csv")
    x, y = [], []
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["country"] == iso and int(row["year"]) == year:
                x.append(HOURS_BAND_MIDPOINTS[row["age_band"]])
                y.append(
                    float(row["emp_pop_ratio"])
                    * float(row["mean_weekly_hours_employed"])
                )
    if not x:
        raise ValueError(f"No ILOSTAT hours for {iso} {year}")
    order = np.argsort(x)
    return np.interp(ages, np.array(x)[order], np.array(y)[order])


def get_age_shape_factor(E, S):
    """
    Ratio of the Philippines' to the USA's labour income per hour by age, by
    model age.

    Philippine labour income per person peaks at 39, against 49 in the US.
    Hours per person are close to the US's in the prime ages but twice as
    high after 65, so per hour the Philippine profile falls further still:
    the factor is 1.78 at 20, 1.38 at 30, 0.77 at 55 and 0.25 from 67, once
    both profiles are put on a common scale.

    Args:
        E (int): age at which agents become economically active
        S (int): number of model ages

    Returns:
        numpy array of length S: multiplicative factor to apply to the OG-USA
        earnings profile at each model age
    """
    phl, usa = _load_nta_profile("PHL"), _load_nta_profile("USA")
    phl_year = max(phl)
    # Nearest-year comparator, as the method specifies.
    usa_year = min(usa, key=lambda y: abs(y - phl_year))
    all_ages = np.arange(len(phl[phl_year]))
    p = phl[phl_year] / hours_per_person("PHL", phl_year, all_ages)
    u = usa[usa_year] / hours_per_person("USA", usa_year, all_ages)

    lo, hi = NORMALISE_AGES
    p_norm = p / np.nanmean(p[lo:hi])
    u_norm = u / np.nanmean(u[lo:hi])

    ages = np.arange(E, E + S)
    capped = np.minimum(ages, FACTOR_TAPER_AGE)
    factor = p_norm[capped] / u_norm[capped]
    return np.nan_to_num(factor, nan=1.0, posinf=1.0, neginf=1.0)


def apply_age_shape(emat, E, S):
    """
    Reshape an earnings matrix by the Philippines/USA age factor.

    Args:
        emat (numpy array): SxJ earnings matrix
        E (int): age agents become economically active
        S (int): number of model ages

    Returns:
        numpy array: SxJ matrix with the Philippine age shape imposed
    """
    factor = get_age_shape_factor(E, S)
    return emat * factor[:, None]
