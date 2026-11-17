"""Check the workbench's profile intervals on simulated responses with known Km."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest

from kinetics import ROOT, fit_curve, load_data, michaelis_menten, profile_curve

VMAX = 180.0
KM = 0.06
NOISE_SD = 6.0


def study(frame, repeats, seed):
    if repeats < 1:
        raise ValueError("At least one simulation per grid is required")
    rng = np.random.default_rng(seed)
    rows = []
    for state, group in frame.groupby("state", sort=True):
        for scope, x in (("full range", group.conc), ("low range", group.loc[group.conc <= .11, "conc"])):
            means = michaelis_menten(x, VMAX, KM)
            covered = open_ends = failed = 0
            for _ in range(repeats):
                rates = means + rng.normal(0, NOISE_SD, len(x))
                try:
                    fit = fit_curve(x, rates)
                    # Display-grid resolution does not enter the endpoint root search.
                    _, interval = profile_curve(x, rates, fit, points=2)
                except (ValueError, RuntimeError):
                    failed += 1
                    continue
                low = interval["approximate_95_percent_lower"]
                high = interval["approximate_95_percent_upper"]
                open_ends += low is None or high is None
                covered += (low is None or low <= KM) and (high is None or KM <= high)
            completed = repeats - failed
            bounds = binomtest(covered, completed).proportion_ci(method="wilson") if completed else (np.nan, np.nan)
            rows.append(dict(state=state, scope=scope, observations=len(x), seed=seed, repeats=repeats,
                             generating_vmax=VMAX, generating_km=KM, noise_sd=NOISE_SD,
                             completed=completed, failed=failed, covered=covered, open_intervals=open_ends,
                             coverage=covered / completed if completed else np.nan,
                             mc_lower=bounds[0], mc_upper=bounds[1]))
    return pd.DataFrame(rows)


def run(out, repeats=200, seed=182):
    frame, _ = load_data()
    table = study(frame, repeats, seed)
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "coverage.csv", index=False, float_format="%.8g")
    fig, ax = plt.subplots(figsize=(7.4, 3.4), layout="constrained")
    positions = np.arange(len(table))
    ax.hlines(positions, table.mc_lower * 100, table.mc_upper * 100, color="#166454", linewidth=2)
    ax.scatter(table.coverage * 100, positions, color="#166454", zorder=3)
    ax.axvline(95, color="#535967", linestyle="--", label="Nominal 95%")
    ax.set(yticks=positions, yticklabels=[f"{row.state} · {row.scope}" for row in table.itertuples()],
           xlabel="Intervals containing the generating Km (%)", title="Profile interval coverage on four archived grids")
    ax.invert_yaxis()
    ax.legend(frameon=False, loc="best")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(out / "coverage.png", dpi=150)
    plt.close(fig)
    lines = ["# How often did the interval include the generating Km?", "",
             f"Each grid uses {repeats} simulated response sets and its archived concentration values. "
             f"The generating curve has Vmax {VMAX:g} and Km {KM:g}, with independent Gaussian errors of standard deviation {NOISE_SD:g}. "
             f"The random seed is {seed}.", "",
             "| Archived grid | Range | Covered / completed | Failed fits or profiles | Intervals with an open end |",
             "| --- | --- | ---: | ---: | ---: |"]
    for row in table.itertuples():
        lines.append(f"| {row.state} | {row.scope} | {row.covered}/{row.completed} | {row.failed} | {row.open_intervals} |")
    lines += ["", "![Coverage and Monte Carlo intervals by concentration grid](coverage.png)", "",
              "Whiskers show 95% Wilson intervals for the simulated coverage fraction among completed runs. "
              "An open end includes all candidate values in that direction up to the workbench’s computational bound. "
              "Only the concentration grids come from the archive. Coverage here describes the declared synthetic curve and noise.", ""]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "examples" / "interval-coverage")
    parser.add_argument("--repeats", type=int, default=200)
    parser.add_argument("--seed", type=int, default=182)
    args = parser.parse_args()
    run(args.out, args.repeats, args.seed)
