"""
Plot the baseline transition's fiscal paths against actuals and the program.

The validation panel of the macro chapter: debt, primary balance, revenue and
public investment, each as a share of GDP at market prices (the model's Y
plus the consumption tax), against the national government's actuals and
fiscal program in ogphl/data/fiscal_program_PHL.csv.

    python scripts/plot_fiscal_paths.py examples/OG-PHL-Example/OUTPUT_BASELINE

Writes docs/book/content/calibration/images/fiscal_paths_vs_program.png and
prints the minimum and maximum of each model path with their years.
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from ogcore.utils import safe_read_pickle  # noqa: E402

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(REPO, "ogphl", "data", "fiscal_program_PHL.csv")
OUT = os.path.join(
    REPO,
    "docs",
    "book",
    "content",
    "calibration",
    "images",
    "fiscal_paths_vs_program.png",
)
# National-government cash revenue to the model's general-government
# concept: the 2023 gap between OECD Revenue Statistics (19.4% of GDP) and
# BTr revenue, mostly social security contributions and local taxes
REVENUE_BRIDGE = 3.78
YEARS = 30


def main(output_dir):
    tpi = safe_read_pickle(os.path.join(output_dir, "TPI", "TPI_vars.pkl"))
    p = safe_read_pickle(os.path.join(output_dir, "model_params.pkl"))
    years = p.start_year + np.arange(YEARS)

    def path(key):
        if key not in tpi:  # an ogcore without debt contracted abroad
            return np.zeros(YEARS)
        return np.squeeze(tpi[key])[:YEARS]

    gdp = path("Y") + path("cons_tax_revenue")
    model = {
        # all government debt: market debt plus debt contracted abroad
        "debt": 100 * (path("D") + path("D_ext")) / gdp,
        "primary_balance": 100
        * (
            path("total_tax_revenue")
            - path("total_primary_government_outlays")
        )
        / gdp,
        "revenue": 100 * path("total_tax_revenue") / gdp,
        "infrastructure": 100 * path("I_g") / gdp,
    }
    data = pd.read_csv(DATA)
    data["revenue"] = data.ng_revenue + REVENUE_BRIDGE
    act, prog = data[data.kind == "actual"], data[data.kind == "program"]

    panels = [
        ("debt", "Debt (% of GDP)", 60.0),
        ("primary_balance", "Primary balance (% of GDP)", 0.0),
        ("revenue", "General-government revenue (% of GDP)", None),
        ("infrastructure", "Public investment (% of GDP)", None),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    for ax, (key, title, ref) in zip(axes.ravel(), panels):
        ax.plot(years, model[key], color="#1f4e9c", lw=2, label="Model")
        if key in act and act[key].notna().any():
            a = act.dropna(subset=[key])
            ax.plot(a.year, a[key], "ko", label="Actual")
        if key in prog and prog[key].notna().any():
            ax.plot(
                prog.year, prog[key], "s--", color="#2e7d32", label="Program"
            )
        if ref is not None:
            ax.axhline(ref, color="grey", lw=0.8, ls=":")
        ax.set_title(title)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        lo, hi = int(np.argmin(model[key])), int(np.argmax(model[key]))
        print(
            f"{key:16s} min {model[key][lo]:6.2f} in {years[lo]}, "
            f"max {model[key][hi]:6.2f} in {years[hi]}"
        )
    fig.suptitle(
        "OG-PHL baseline fiscal paths against actuals and the program"
    )
    fig.tight_layout()
    fig.savefig(OUT, dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
