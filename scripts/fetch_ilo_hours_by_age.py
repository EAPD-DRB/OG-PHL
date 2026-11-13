"""
Fetch hours worked and employment rates by age from ILOSTAT.

These are the inputs to the labor-supply half of the household calibration
(ogphl/labor.py) and to the per-hour split of the earnings age shape
(ogphl/income.py). Both need hours worked per person by age: the
employment-to-population ratio times the mean weekly hours of the employed.

ILOSTAT publishes hours in ten-year bands and employment rates in five-year
bands, both from the Labour Force Survey (PSA for the Philippines, the CPS for
the United States). Each five-year band takes the hours of the ten-year band
that contains it.

Usage:
    python scripts/fetch_ilo_hours_by_age.py
Writes:
    ogphl/data/ilo_hours_by_age.csv

Source: ILOSTAT SDMX API, https://sdmx.ilo.org (series HOW_TEMP_SEX_AGE_NB,
        mean weekly hours actually worked per employed person, main job; and
        EMP_DWAP_SEX_AGE_RT, employment-to-population ratio), both sexes.
"""

import csv
import io
import os
import urllib.request

SDMX = (
    "https://sdmx.ilo.org/rest/data/ILO,{flow},1.0/{iso}.A..SEX_T."
    "?startPeriod={lo}&endPeriod={hi}&format=csvfile"
)
HOURS = "DF_HOW_TEMP_SEX_AGE_NB"
EMP_RATE = "DF_EMP_DWAP_SEX_AGE_RT"

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "ogphl",
    "data",
    "ilo_hours_by_age.csv",
)

COUNTRIES = ["PHL", "USA"]
YEARS = (2010, 2025)

# five-year employment band -> the ten-year hours band that contains it
BANDS = {
    "15-19": "15-24",
    "20-24": "15-24",
    "25-29": "25-34",
    "30-34": "25-34",
    "35-39": "35-44",
    "40-44": "35-44",
    "45-49": "45-54",
    "50-54": "45-54",
    "55-59": "55-64",
    "60-64": "55-64",
    "65+": "65+",
}


def _code(band, width):
    """ILOSTAT's age code for a band, e.g. AGE_5YRBANDS_Y20-24."""
    tail = "YGE65" if band == "65+" else f"Y{band}"
    return f"AGE_{width}YRBANDS_{tail}"


def fetch(flow, iso):
    """
    One ILOSTAT series for one country.

    Returns:
        dict: {(age code, year): value}
    """
    url = SDMX.format(flow=flow, iso=iso, lo=YEARS[0], hi=YEARS[1])
    req = urllib.request.Request(url, headers={"User-Agent": "OG-PHL"})
    text = urllib.request.urlopen(req, timeout=120).read().decode("utf-8")
    out = {}
    for row in csv.DictReader(io.StringIO(text)):
        out[(row["AGE"], int(row["TIME_PERIOD"]))] = float(row["OBS_VALUE"])
    return out


def main():
    rows = []
    for iso in COUNTRIES:
        hours = fetch(HOURS, iso)
        emp = fetch(EMP_RATE, iso)
        years = sorted({y for _, y in emp})
        for year in years:
            for band, hours_band in BANDS.items():
                e = emp.get((_code(band, 5), year))
                h = hours.get((_code(hours_band, 10), year))
                if e is None or h is None:
                    continue
                rows.append(
                    {
                        "country": iso,
                        "year": year,
                        "age_band": band,
                        "emp_pop_ratio": round(e / 100, 5),
                        "mean_weekly_hours_employed": h,
                    }
                )
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
