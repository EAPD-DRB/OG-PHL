import pandas as pd
import numpy as np
import os
from ogphl.constants import CONS_DICT, PROD_DICT

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
"""
Read in Social Accounting Matrix (SAM) file
"""
sam_path = os.path.join(CUR_DIR, "data", "002_IFPRI_SAM_PHL_2018_SAM.csv")


def read_SAM():
    """
    Read in the packaged Social Accounting Matrix (SAM) file.

    Returns:
        SAM (pd.DataFrame | None): Social Accounting Matrix, or None
            if unavailable
    """
    try:
        sam = pd.read_csv(sam_path, index_col=1, thousands=",")
        sam.fillna(0, inplace=True)
        return sam
    except Exception as exc:
        print(f"Failed to read packaged SAM file: {exc}")
        return None


def get_alpha_c(sam=None, cons_dict=CONS_DICT):
    """
    Calibrate the alpha_c vector, showing the shares of household
    expenditures for each consumption category

    Args:
        sam (pd.DataFrame): SAM file
        cons_dict (dict): Dictionary of consumption categories

    Returns:
        alpha_c (dict): Dictionary of shares of household expenditures
    """
    if sam is None:
        sam = read_SAM()
    if sam is None:
        raise RuntimeError("SAM data is unavailable. Cannot compute alpha_c.")
    hh_cols = [
        "hhd-r1",
        "hhd-r2",
        "hhd-r3",
        "hhd-r4",
        "hhd-r5",
        "hhd-u1",
        "hhd-u2",
        "hhd-u3",
        "hhd-u4",
        "hhd-u5",
    ]
    alpha_c = {}
    overall_sum = 0
    for key, value in cons_dict.items():
        # note the subtraction of the row to focus on domestic consumption
        category_total = (
            sam.loc[sam.index.isin(value), hh_cols].values.astype(float).sum()
        )
        alpha_c[key] = category_total
        overall_sum += category_total
    for key, value in cons_dict.items():
        alpha_c[key] = alpha_c[key] / overall_sum

    return alpha_c


def get_io_matrix(sam=None, cons_dict=CONS_DICT, prod_dict=PROD_DICT):
    """
    Calibrate the io_matrix array.  This array relates the share of each
    production category in each consumption category

    Args:
        sam (pd.DataFrame): SAM file
        cons_dict (dict): Dictionary of consumption categories
        prod_dict (dict): Dictionary of production categories

    Returns:
        io_df (pd.DataFrame): Dataframe of io_matrix
    """
    if sam is None:
        sam = read_SAM()
    if sam is None:
        raise RuntimeError(
            "SAM data is unavailable. Cannot compute io_matrix."
        )
    # Create initial matrix as dataframe of 0's to fill in
    io_dict = {}
    for key in prod_dict.keys():
        io_dict[key] = np.zeros(len(cons_dict.keys()))
    io_df = pd.DataFrame(io_dict, index=cons_dict.keys())
    # Fill in the matrix
    # Note, each cell in the SAM represents a payment from the columns
    # account to the row account
    # (see https://www.un.org/en/development/desa/policy/capacity/presentations/manila/6_sam_mams_philippines.pdf)
    # We are thus going to take the consumption categories from rows and
    # the production categories from columns
    for ck, cv in cons_dict.items():
        for pk, pv in prod_dict.items():
            io_df.loc[io_df.index == ck, pk] = (
                sam.loc[sam.index.isin(cv), pv].values.astype(float).sum()
            )
    # change from levels to share (where each row sums to one)
    io_df = io_df.div(io_df.sum(axis=1), axis=0)

    return io_df


# SAM factor accounts: labor (by education tier), land, and capital.
# Land income is grouped with capital because OG-Core has only two private
# factors (capital and labor); land's return is non-labor income.
LABOR_ACCOUNTS = ["flab-n", "flab-p", "flab-s"]
CAPITAL_ACCOUNTS = ["fcap", "flnd"]


def get_gamma(sam=None, prod_dict=PROD_DICT, target_avg=None):
    """
    Calibrate gamma, the capital share of value added for each production
    industry, from the factor-payment rows of the SAM.

    For each industry, value added is the sum of payments to labor, capital,
    and land (the factor rows) across the industry's activity columns. The
    capital share is

        gamma_m = (capital + land) / (labor + capital + land).

    This is the private capital share entering OG-Core's CES production
    function; the labor share is its complement (1 - gamma_m) when public
    capital's share (gamma_g) is zero.

    The raw SAM capital shares are biased upward by the mixed income of the
    self-employed (large in Philippine agriculture and trade), which the SAM
    books as a return to capital rather than labor. ``target_avg`` corrects
    this: the shares are rescaled multiplicatively so their value-added
    weighted average equals ``target_avg`` (e.g. the economy-wide capital
    share used elsewhere in the calibration), preserving the cross-industry
    pattern while fixing the level. With ``target_avg=None`` the raw,
    unadjusted shares are returned.

    Args:
        sam (pd.DataFrame): SAM file
        prod_dict (dict): Dictionary of production categories
        target_avg (float | None): if given, rescale so the value-added
            weighted mean capital share equals this value

    Returns:
        gamma (dict): Dictionary of capital shares, keyed by industry
    """
    if sam is None:
        sam = read_SAM()
    if sam is None:
        raise RuntimeError("SAM data is unavailable. Cannot compute gamma.")
    gamma = {}
    value_added = {}
    for key, value in prod_dict.items():
        labor = (
            sam.loc[sam.index.isin(LABOR_ACCOUNTS), value]
            .values.astype(float)
            .sum()
        )
        capital = (
            sam.loc[sam.index.isin(CAPITAL_ACCOUNTS), value]
            .values.astype(float)
            .sum()
        )
        value_added[key] = labor + capital
        gamma[key] = (
            capital / value_added[key] if value_added[key] > 0 else 0.0
        )

    if target_avg is not None:
        weights = np.array(list(value_added.values()))
        shares = np.array(list(gamma.values()))
        if weights.sum() > 0:
            current_avg = np.average(shares, weights=weights)
            if current_avg > 0:
                scale = target_avg / current_avg
                gamma = {key: share * scale for key, share in gamma.items()}

    return gamma
