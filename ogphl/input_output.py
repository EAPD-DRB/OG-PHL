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
    Legacy io_matrix from direct intermediate-use cells, retained as a
    comparison baseline. ``get_io_matrix_value_added`` is the construction used
    by the calibration; it traces the full domestic supply chain and
    corresponds to a value-added accounting identity, whereas this one does
    not.

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

# Rest-of-world (imports) account and household columns in the SAM.
ROW_ACCOUNT = "row"
HH_COLS = [
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


def get_io_matrix_value_added(
    sam=None, cons_dict=CONS_DICT, prod_dict=PROD_DICT
):
    """
    Calibrate the io_matrix as the domestic value-added content of each
    consumption good, by production industry.

    OG-Core's ``io_matrix[i, m]`` is the amount of industry-m output embodied
    in one unit of consumption good i (rows sum to one). Because OG-Core's
    production side has no intermediate inputs (each industry's gross output is
    its value added), the object it needs is the *value added embodied in final
    demand*: of one peso spent on consumption good i, how much is value added
    by each industry once the entire domestic supply chain is traced. This is
    the standard input-output value-added-content calculation, and it differs
    from ``get_io_matrix`` (which sums direct intermediate-use cells and
    corresponds to no accounting identity).

    Steps:

      1. Pair each commodity ``cX`` with the activity ``aX`` that produces it
         (the SAM make matrix is diagonal).
      2. Read the use matrix (commodity x activity intermediate inputs), gross
         output, imports, and value added (SAM factor rows).
      3. Split domestic vs imported supply with the domestic supply share
         ``sigma`` (import proportionality), giving domestic technical
         coefficients ``A_d = sigma * use / output``.
      4. ``L = (I - A_d)^{-1}`` is total domestic output per unit of domestic
         final demand; ``v = value_added / output`` the value-added share. The
         domestic value added of sector i embodied per unit of domestic final
         demand for commodity k is ``v_i * L[i, k]``.
      5. For each consumption good, average over its commodities weighted by
         household final consumption, scale by ``sigma`` (the domestic share of
         the final good itself), aggregate sectors into industries, and
         renormalize each row to one so it is the domestic composition
         (imported content is netted out and excluded).

    Args:
        sam (pd.DataFrame): SAM file
        cons_dict (dict): Dictionary of consumption categories
        prod_dict (dict): Dictionary of production categories

    Returns:
        io_df (pd.DataFrame): I x M io_matrix (rows sum to one)
    """
    if sam is None:
        sam = read_SAM()
    if sam is None:
        raise RuntimeError(
            "SAM data is unavailable. Cannot compute io_matrix."
        )
    sam = sam.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    # Pair commodities (cX) with their producing activities (aX); keep only
    # those present as both rows and columns of the SAM.
    rows, cols = set(sam.index), set(sam.columns)
    sectors = [
        c
        for c in sam.index
        if c[:1] == "c"
        and c in cols
        and ("a" + c[1:]) in rows
        and ("a" + c[1:]) in cols
    ]
    activities = ["a" + c[1:] for c in sectors]
    n = len(sectors)
    sector_pos = {c: i for i, c in enumerate(sectors)}

    use = sam.loc[sectors, activities].to_numpy(dtype=float)
    output = sam.loc[activities, sectors].to_numpy(dtype=float).sum(axis=0)
    imports = (
        sam.loc[ROW_ACCOUNT, sectors].to_numpy(dtype=float)
        if ROW_ACCOUNT in rows
        else np.zeros(n)
    )
    factor_rows = sam.index.isin(LABOR_ACCOUNTS + CAPITAL_ACCOUNTS)
    value_added = (
        sam.loc[factor_rows, activities].to_numpy(dtype=float).sum(axis=0)
    )

    supply = output + imports
    sigma = np.divide(output, supply, out=np.ones(n), where=supply > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        a_d = (sigma[:, None] * use) / output[None, :]
    a_d = np.nan_to_num(a_d)
    leontief = np.linalg.inv(np.eye(n) - a_d)
    v = np.divide(value_added, output, out=np.zeros(n), where=output > 0)
    # domestic value added of sector i per unit domestic final demand of k
    va_content = v[:, None] * leontief

    act_to_ind = {a: m for m, acts in prod_dict.items() for a in acts}
    sector_ind = [act_to_ind.get(a) for a in activities]

    io_df = pd.DataFrame(
        0.0, index=list(cons_dict.keys()), columns=list(prod_dict.keys())
    )
    for good, commodities in cons_dict.items():
        present = [c for c in commodities if c in sector_pos]
        if not present:
            continue
        idx = np.array([sector_pos[c] for c in present])
        fc = sam.loc[present, HH_COLS].to_numpy(dtype=float).sum(axis=1)
        if fc.sum() <= 0:
            continue
        weights = fc / fc.sum()
        # domestic value added by source sector per peso consumed of the good;
        # sigma[idx] nets out the imported share of the final good itself
        src = (va_content[:, idx] * (weights * sigma[idx])[None, :]).sum(
            axis=1
        )
        for i in range(n):
            if sector_ind[i] is not None:
                io_df.loc[good, sector_ind[i]] += src[i]
        total = io_df.loc[good].sum()
        if total > 0:
            io_df.loc[good] = io_df.loc[good] / total

    return io_df
