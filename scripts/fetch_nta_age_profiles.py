"""
Fetch National Transfer Accounts (NTA) labour-income-by-age profiles.

These are the input to the age-shape half of the family's earnings-profile
method (see EAPD-DRB/OG-ZAF#18 and #63). The method adjusts OG-USA's estimated
lifetime earnings curves in two ways:

  1. reshape them so the age pattern matches the target country's own
     income-per-capita-by-age profile  <- this script supplies the data
  2. tilt the gaps between the J income groups to match the target country's
     inequality                        <- already done, ogphl/income.py

The NTA database has no API: it is a session-based form. This script walks the
same two steps a person would (submit a query, then post the returned
download form), which is why it carries cookies and a Referer -- the server
rejects the download POST without one.

Both countries must come from NTA on the same variable and variable type, or
the ratio is meaningless: NTA levels are not comparable to national wage
surveys: a Philippine wage survey cannot be divided by a US NTA profile.

Usage:
    python scripts/fetch_nta_age_profiles.py
Writes:
    ogphl/data/nta_labor_income_PHL.csv
    ogphl/data/nta_labor_income_USA.csv

Source: National Transfer Accounts project, https://ntaccounts.org
        Please observe the NTA attribution and fair-use policy when
        redistributing. Ported from OG-JPN's script (country and year
        windows changed only).
"""

import http.cookiejar
import os
import re
import urllib.parse
import urllib.request

BASE = "https://www.ntaccounts.org"
BROWSE = f"{BASE}/web/nta/show/Browse%20database"
CONFIRM = f"{BASE}/web/nta/download-confirm"

OUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "ogphl", "data"
)

# "Smooth Mean" is the per-capita smoothed series the method specifies.
VAR_NAME = "Labor Income"
VAR_TYPE = "Smooth Mean"


def _opener():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", "OG-PHL calibration (ogphl)")]
    return op


def fetch_country(country, year_lo, year_hi, var_name=VAR_NAME):
    """
    Fetch one country's age profile of an NTA variable as raw CSV text.

    Args:
        country (str): NTA country name, e.g. "Philippines"
        year_lo (int): first year of the search window
        year_hi (int): last year of the search window
        var_name (str): NTA variable name, labour income by default

    Returns:
        str: CSV text, one row per matched age profile
    """
    op = _opener()
    op.open(BROWSE, timeout=60).read()  # establish the session

    query = [
        ("countries", country),
        ("var-names", var_name),
        ("var-types", VAR_TYPE),
        ("year-lo", str(year_lo)),
        ("year-hi", str(year_hi)),
        ("year-latest", ""),
        ("var-attr", ""),
        ("submit", "Submit"),
    ]
    req = urllib.request.Request(
        CONFIRM,
        data=urllib.parse.urlencode(query).encode(),
        headers={"Referer": BROWSE},
    )
    page = op.open(req, timeout=90).read().decode("utf-8", "replace")

    # The confirm page returns session-scoped download forms. The first one
    # that is not the query form itself is the age-profile download.
    actions = [
        a
        for a in re.findall(r"<form[^>]*action='([^']+)'", page)
        if "download-confirm" not in a
    ]
    if not actions:
        raise RuntimeError(f"no download form returned for {country}")

    dl = urllib.request.Request(
        BASE + actions[0],
        data=urllib.parse.urlencode({"submit": "Download"}).encode(),
        # The server 403s without this: it checks the referrer explicitly.
        headers={"Referer": CONFIRM},
    )
    return op.open(dl, timeout=120).read().decode("utf-8", "replace")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # Take a wide window for both countries; the method uses the latest
    # Philippine year against the nearest US year.
    for country, iso, lo, hi in [
        ("Philippines", "PHL", 1990, 2025),
        # NTA names the United States "US", not "United States".
        ("US", "USA", 1990, 2025),
    ]:
        csv_text = fetch_country(country, lo, hi)
        path = os.path.join(OUT_DIR, f"nta_labor_income_{iso}.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(csv_text)
        n = max(0, csv_text.count("\n") - 1)
        print(f"  {country:16s} -> {os.path.relpath(path)}  ({n} record(s))")
    # Private asset income by age: the age shape of household wealth used
    # for the initial distribution of wealth (ogphl/initial_wealth.py)
    csv_text = fetch_country(
        "Philippines", 1990, 2025, var_name="Private Asset Income"
    )
    path = os.path.join(OUT_DIR, "nta_private_asset_income_PHL.csv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(csv_text)
    n = max(0, csv_text.count("\n") - 1)
    print(f"  {'Philippines':16s} -> {os.path.relpath(path)}  ({n} record(s))")


if __name__ == "__main__":
    main()
