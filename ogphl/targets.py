"""
Data targets for the OG-PHL steady-state dashboard, and the function that
computes the matching model moments from a solved ``SS_vars.pkl``.

Every target carries its source; the same numbers are pinned against the
packaged parameters in ``tests/test_taxes.py`` and
``tests/test_remittances.py``. Revenue shares are the OECD Revenue
Statistics in Asia and the Pacific 2025 (Philippines, 2023) plus the BESF/BTr
non-tax lines the calibration captures. Fiscal rows first, then external,
production and households.

Every ratio is to GDP at market prices, the national-accounts GDP the data
are published against. OG-Core's output Y is GDP before consumption taxes:
households pay (1 + tau_c) times the producer price and the tax is collected
on top of Y, so GDP at market prices is Y plus consumption-tax revenue (the
mapping of Prescott 2004, following Mendoza, Razin and Tesar 1994). Model
moments are therefore divided by Y + consumption tax, and parameters that
OG-Core multiplies by its own Y (alpha_T, alpha_G, alpha_I, alpha_RM, the
debt ratios, initial wealth and public capital) are the data share times
``MODEL_PER_MARKET_GDP``.
"""

import numpy as np

# Consumption-tax revenue as a share of GDP at market prices (the "cons tax"
# target below) and the ratio of market-price GDP to the model's Y it
# implies: Y_mkt = Y + tax and tax = share x Y_mkt, so Y_mkt / Y = 1/(1-share)
CONS_TAX_SHARE = 0.0794
MODEL_PER_MARKET_GDP = 1 / (1 - CONS_TAX_SHARE)

# National Government debt contracted abroad (foreign loans and bonds issued
# abroad), share of GDP at market prices, end-2024: P5,120.9bn on 2024 GDP of
# P26,446.4bn (BTr Debt Indicators, December 2025). It is OG-Core's
# alpha_D_ext (times MODEL_PER_MARKET_GDP), held at this level; the debt
# targets below are all government debt, market plus external, so the
# market-debt parameters are the totals less this share.
EXTERNAL_DEBT_SHARE = 0.193633

# moment: (target, source)
TARGETS = {
    # Fiscal: revenue by instrument
    "PIT/Y": (0.0312, "OECD Revenue Statistics Asia-Pacific 2025, PHL 2023"),
    "payroll/Y": (0.0278, "SSC, OECD Revenue Statistics 2025, PHL 2023"),
    "CIT/Y": (
        0.0420,
        "CIT 2.90 + BTr income from government capital ~1.00 + "
        "unallocable income taxes 0.30 (OECD 2023; BESF)",
    ),
    "cons tax/Y": (
        CONS_TAX_SHARE,
        "VAT + excises + customs 7.39 (OECD 2023) + fees and charges "
        "0.55 (BESF non-tax)",
    ),
    "wealth tax/Y": (
        0.0132,
        "property-type taxes: RPT, DST, LGU levies (OECD 'other taxes' "
        "less estate)",
    ),
    "bequest tax/Y": (0.0007, "estate tax collections, BIR"),
    "r_gov": (
        0.0233,
        "rate on market (domestic) debt, BTr 2024-2025: domestic interest "
        "P539.8bn and P634.8bn on average domestic debt of P10.47tn and "
        "P11.52tn (5.33% nominal), less ~3% expected inflation",
    ),
    "D/Y": (
        0.60,
        "MTFF program anchor, all government debt: debt_ratio_ss (market) "
        "plus alpha_D_ext (external)",
    ),
    # Spending
    "TR/Y": (0.0448, "alpha_T: social transfers, DBM/BESF"),
    "I_g/Y": (0.052, "alpha_I: public infrastructure program, MTFF/BESF"),
    "pensions/Y": (
        0.0697,
        "today's 2.28% (SSS 1.06% 2023, GSIS 0.68% 2024, MUP fund 0.54% 2024 "
        "GAA) x 3.056, the rise in covered retirees per worker to the steady "
        "state (a mature system in the long-run population)",
    ),
    # External
    "RM/Y": (
        0.0812,
        "BSP 2025 personal remittances US$39.62bn (BPM6), the household "
        "income measure; the published 7.3% ratio is the narrower cash "
        "measure",
    ),
    # Production and households: private capital and its foreign share are
    # scored in the first transition period (TRANSITION_TARGETS), where the
    # data describe today's population, and reported here as outcomes
}


# Moments of the first transition period (2025), scored from TPI_vars.pkl.
# The discount factor and the foreign-capital fill share are tuned to these
# rather than to steady-state ratios: the data describe the Philippines
# today, and its population is far younger than the steady state's.
TRANSITION_TARGETS = {
    "(I+I_g)/Y[2025]": (
        0.236,
        "gross fixed capital formation, World Bank WDI 2024; beta",
    ),
    "K_f/K[2025]": (
        0.20,
        "BSP International Investment Position, inward share; zeta_K",
    ),
    "B/Y[2025]": (3.35, "initial_wealth_ratio construction (anchor)"),
    "K/Y[2025]": (
        3.59,
        "PWT 11 capital stock 2023 (3.97) less public capital ~0.38 (IMF "
        "ICSD); set by the initial wealth anchor and the foreign share",
    ),
}


def tpi_moments(tpi, t=0):
    """
    Transition moments in period t, as shares of GDP at market prices.

    Args:
        tpi (dict): a solved ``TPI_vars.pkl``
        t (int): model period, 0 for the start year

    Returns:
        m (dict): moments keyed like ``TRANSITION_TARGETS``, plus untargeted
            ratios
    """

    def at(key):
        if key not in tpi:  # an ogcore without debt contracted abroad
            return 0.0
        return float(np.squeeze(tpi[key])[t])

    Y = at("Y") + at("cons_tax_revenue")
    year = "[2025]" if t == 0 else f"[t={t}]"
    return {
        "(I+I_g)/Y" + year: (at("I_total") + at("I_g")) / Y,
        "K_f/K" + year: at("K_f") / at("K"),
        "K/Y" + year: at("K") / Y,
        "B/Y" + year: at("B") / Y,
        "C/Y purch." + year: (at("C") + at("cons_tax_revenue")) / Y,
        "pensions/Y" + year: at("agg_pension_outlays") / Y,
        "D/Y" + year: (at("D") + at("D_ext")) / Y,
        "D_ext/Y" + year: at("D_ext") / Y,
        "interest abroad/Y" + year: (
            at("debt_service_ext") + at("r_p") * at("D_f")
        )
        / Y,
        "primary balance/Y" + year: (
            at("total_tax_revenue") - at("total_primary_government_outlays")
        )
        / Y,
        "total tax/Y" + year: at("total_tax_revenue") / Y,
        "r" + year: at("r"),
    }


def ss_moments(ss):
    """
    Model side of every dashboard row from a solved steady state.

    Args:
        ss (dict): a solved ``SS_vars.pkl``

    Returns:
        m (dict): model moments, keyed like ``TARGETS``, plus untargeted
            ratios
    """

    def sc(key):
        if key not in ss:  # an ogcore without debt contracted abroad
            return 0.0
        return float(np.sum(ss[key]))

    Y_model = float(np.squeeze(ss["Y"]))
    # GDP at market prices: the model's Y plus the consumption tax
    Y = Y_model + sc("cons_tax_revenue")
    C = sc("C")
    nx = Y_model - C - sc("I_total") - sc("I_g") - sc("G")
    m = {
        "PIT/Y": sc("iit_revenue") / Y,
        "payroll/Y": sc("payroll_tax_revenue") / Y,
        "CIT/Y": sc("business_tax_revenue") / Y,
        "cons tax/Y": sc("cons_tax_revenue") / Y,
        "wealth tax/Y": sc("wealth_tax_revenue") / Y,
        "bequest tax/Y": sc("bequest_tax_revenue") / Y,
        "total tax/Y": sc("total_tax_revenue") / Y,
        "r_gov": sc("r_gov"),
        "D/Y": (sc("D") + sc("D_ext")) / Y,
        "D market/Y": sc("D") / Y,
        "D_ext/Y": sc("D_ext") / Y,
        "D_f/D": sc("D_f") / sc("D") if sc("D") else np.nan,
        "interest abroad/Y": (sc("debt_service_ext") + sc("r_p") * sc("D_f"))
        / Y,
        "G/Y": sc("G") / Y,
        "TR/Y": sc("TR") / Y,
        "I_g/Y": sc("I_g") / Y,
        "pensions/Y": sc("agg_pension_outlays") / Y,
        "K_f/K": sc("K_f") / sc("K"),
        "RM/Y": sc("RM") / Y,
        "NX/Y": nx / Y,
        "K/Y": sc("K") / Y,
        "(I+I_g)/Y": (sc("I_total") + sc("I_g")) / Y,
        "C/Y purch.": (C + sc("cons_tax_revenue")) / Y,
        "B/Y": sc("B") / Y,
        "BQ/Y": sc("BQ") / Y,
        "r": sc("r"),
        "factor": sc("factor"),
        "GDP mkt / Y": Y / Y_model,
    }
    return m
