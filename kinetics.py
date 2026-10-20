"""Nonlinear curve fitting and identifiability checks for an archived teaching dataset."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import brentq, least_squares
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parent
PARAMETER_BOUNDS = (1e-9, 1e9)
LOG_BOUNDS = tuple(np.log(PARAMETER_BOUNDS))
PROFILE_CUTOFF = float(chi2.ppf(.95, 1))


def convert_r_source(source: str) -> bytes:
    """Parse only the literal numeric vectors in this pinned R fixture; never eval R."""
    def vector(label):
        match = re.search(rf"{label}\s*=\s*c\((.*?)\)", source, flags=re.S)
        if match is None:
            raise ValueError(f"Missing literal vector {label}")
        return [float(x.strip()) for x in match.group(1).split(",")]
    match = re.search(r"state\s*=\s*factor\(c\((.*?)\)", source, flags=re.S)
    if match is None:
        raise ValueError("Missing literal state vector")
    states = [int(x.strip().removesuffix("L")) for x in match.group(1).split(",")]
    concentrations, rates = vector("conc"), vector("vel")
    if not len(concentrations) == len(rates) == len(states) == 23 or not set(states) <= {1, 2}:
        raise ValueError("Unexpected source data dimensions or states")
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["row_id", "conc", "rate", "state"])
    for i, (s, v, group) in enumerate(zip(concentrations, rates, states), 1):
        writer.writerow([i, f"{s:g}", f"{v:g}", {1: "treated", 2: "untreated"}[group]])
    return output.getvalue().encode("utf-8")


def load_data(data_dir: Path = ROOT / "data") -> tuple[pd.DataFrame, dict]:
    manifest = json.loads((data_dir / "manifest.json").read_text())
    for entry in manifest["files"]:
        raw = (data_dir / entry["path"]).read_bytes()
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError(f"Input fingerprint mismatch: {entry['path']}")
    if convert_r_source((data_dir / "Puromycin.R").read_text()) != (data_dir / "puromycin.csv").read_bytes():
        raise ValueError("Converted CSV does not match the pinned literal R vectors")
    frame = pd.read_csv(data_dir / "puromycin.csv")
    if list(frame.columns) != ["row_id", "conc", "rate", "state"] or frame.row_id.duplicated().any():
        raise ValueError("Unexpected data columns or repeated row identifiers")
    if not set(frame.state) == {"treated", "untreated"}:
        raise ValueError("Expected the two documented state labels")
    validate_xy(frame.conc, frame.rate)
    return frame, manifest


def validate_xy(x, y) -> tuple[np.ndarray, np.ndarray]:
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x.ndim != 1 or y.shape != x.shape or len(x) < 3:
        raise ValueError("Need at least three paired one-dimensional observations")
    if not np.isfinite(x).all() or not np.isfinite(y).all() or (x <= 0).any() or (y <= 0).any():
        raise ValueError("Observed concentrations and rates must be finite and positive")
    if np.unique(x).size < 2:
        raise ValueError("One concentration cannot identify both curve parameters")
    return x, y


def michaelis_menten(substrate, vmax: float, km: float) -> np.ndarray:
    substrate = np.asarray(substrate, dtype=float)
    if not np.isfinite(substrate).all() or (substrate < 0).any() or not np.isfinite([vmax, km]).all() or min(vmax, km) <= 0:
        raise ValueError("The curve requires nonnegative substrate and positive finite parameters")
    return vmax * substrate / (km + substrate)


def log_parameter_jacobian(x, vmax, km):
    prediction = michaelis_menten(x, vmax, km)
    return np.column_stack([prediction, -prediction * km / (km + np.asarray(x))])


def fit_curve(x, y) -> dict:
    x, y = validate_xy(x, y)
    fits = []
    for multiplier in [.5, 1., 2.]:
        for km_start in [x.min(), np.median(x), x.max()]:
            result = least_squares(
                lambda theta: michaelis_menten(x, *np.exp(theta)) - y,
                np.log([max(y) * multiplier, km_start]),
                jac=lambda theta: log_parameter_jacobian(x, *np.exp(theta)),
                bounds=LOG_BOUNDS, ftol=1e-12, xtol=1e-12, gtol=1e-12,
                max_nfev=2000,
            )
            if result.success and np.isfinite(result.fun).all():
                fits.append(result)
    if not fits:
        raise ValueError("No nonlinear fit converged")
    best = min(fits, key=lambda result: float(np.dot(result.fun, result.fun)))
    vmax, km = np.exp(best.x)
    residuals = y - michaelis_menten(x, vmax, km)
    rss = float(residuals @ residuals)
    information = best.jac.T @ best.jac
    covariance_shape = np.linalg.pinv(information)
    denominator = np.sqrt(covariance_shape[0, 0] * covariance_shape[1, 1])
    return {"vmax": float(vmax), "km": float(km), "rss": rss, "n": len(x),
            "rmse": float(np.sqrt(rss / len(x))),
            "residual_sd": float(np.sqrt(rss / (len(x) - 2))),
            "log_parameter_information_condition": float(np.linalg.cond(information)),
            "local_parameter_correlation": float(covariance_shape[0, 1] / denominator),
            "converged_starts": len(fits), "attempted_starts": 9,
            "at_computational_bound": bool(np.any(best.x < LOG_BOUNDS[0] + .01) or np.any(best.x > LOG_BOUNDS[1] - .01))}


def profile_rss(km: float, x, y) -> tuple[float, float]:
    if not np.isfinite(km) or km <= 0:
        raise ValueError("Profile Km must be positive and finite")
    x, y = validate_xy(x, y)
    basis = x / (km + x)
    vmax = float(np.clip((basis @ y) / (basis @ basis), *PARAMETER_BOUNDS))
    residuals = y - vmax * basis
    return float(residuals @ residuals), vmax


def profile_curve(x, y, fitted: dict, points: int = 240) -> tuple[pd.DataFrame, dict]:
    x, y = validate_xy(x, y)
    if fitted["rss"] <= 1e-15:
        raise ValueError("A zero-residual fit has no estimable noise scale for this profile likelihood")
    lower, upper = LOG_BOUNDS
    center = float(np.log(fitted["km"]))
    def statistic(log_km):
        rss, _ = profile_rss(float(np.exp(log_km)), x, y)
        return float(max(0, len(x) * np.log(rss / fitted["rss"])))
    def crossing(endpoint):
        if statistic(endpoint) <= PROFILE_CUTOFF:
            return None
        return float(np.exp(brentq(lambda value: statistic(value) - PROFILE_CUTOFF,
                                  min(center, endpoint), max(center, endpoint), xtol=1e-12)))
    low, high = crossing(lower), crossing(upper)
    display_low = max(np.exp(lower), (low or fitted["km"] / 100) / 2)
    display_high = min(np.exp(upper), (high or fitted["km"] * 100) * 2)
    grid = np.sort(np.unique(np.r_[np.geomspace(display_low, display_high, points), fitted["km"]]))
    rows = []
    for km in grid:
        rss, vmax = profile_rss(float(km), x, y)
        rows.append({"km": float(km), "profile_vmax": vmax, "rss": rss,
                     "likelihood_ratio": statistic(np.log(km))})
    return pd.DataFrame(rows), {"approximate_95_percent_lower": low, "approximate_95_percent_upper": high,
                               "cutoff": PROFILE_CUTOFF, "lower_closed": low is not None,
                               "upper_closed": high is not None,
                               "assumptions": "Independent additive Gaussian errors with common unknown variance; asymptotic chi-square cutoff, not calibrated small-sample coverage"}


def information_scenarios() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Dimensionless local mathematics, not suggested biological assay settings."""
    scenarios = {"low_only": np.geomspace(.03, .3, 12),
                 "near_km": np.geomspace(.7, 1.3, 12),
                 "wide_range": np.geomspace(.05, 20, 12)}
    summaries, rows = [], []
    for name, x in scenarios.items():
        jac = log_parameter_jacobian(x, 1., 1.)
        info = jac.T @ jac
        inverse = np.linalg.inv(info)
        summaries.append({"scenario": name, "points": len(x),
                          "information_condition_number": float(np.linalg.cond(info)),
                          "information_determinant": float(np.linalg.det(info)),
                          "local_parameter_correlation": float(inverse[0, 1] / np.sqrt(inverse[0, 0] * inverse[1, 1]))})
        rows += [{"scenario": name, "substrate_over_km": float(value)} for value in x]
    return pd.DataFrame(summaries), pd.DataFrame(rows)


def run(data_dir: Path = ROOT / "data", out: Path = ROOT / "results") -> dict:
    frame, manifest = load_data(data_dir)
    out.mkdir(parents=True, exist_ok=True)
    all_fits, profiles, residuals, summaries = [], [], [], {}
    for state in ["treated", "untreated"]:
        group = frame[frame.state == state]
        summaries[state] = {}
        for scope in ["full_range", "low_range_only"]:
            subset = group if scope == "full_range" else group[group.conc <= .11]
            fit = fit_curve(subset.conc, subset.rate)
            profile, interval = profile_curve(subset.conc, subset.rate, fit)
            profile["state"], profile["scope"] = state, scope
            profiles.append(profile)
            summaries[state][scope] = {**fit, "km_profile": interval,
                                       "concentration_min": float(subset.conc.min()), "concentration_max": float(subset.conc.max())}
            all_fits.append({"state": state, "scope": scope, **fit,
                             "km_interval_lower": interval["approximate_95_percent_lower"],
                             "km_interval_upper": interval["approximate_95_percent_upper"]})
        full = summaries[state]["full_range"]
        predicted = michaelis_menten(group.conc, full["vmax"], full["km"])
        residuals += [{"row_id": int(row.row_id), "state": state, "conc": float(row.conc),
                       "observed_rate": float(row.rate), "fitted_rate": float(prediction),
                       "residual_observed_minus_fitted": float(row.rate - prediction)}
                      for row, prediction in zip(group.itertuples(), predicted)]
    pd.DataFrame(all_fits).to_csv(out / "parameter_estimates.csv", index=False, float_format="%.10g")
    profile_data = pd.concat(profiles, ignore_index=True)
    profile_data.to_csv(out / "km_profiles.csv", index=False, float_format="%.10g")
    residual_data = pd.DataFrame(residuals)
    residual_data.to_csv(out / "residuals.csv", index=False, float_format="%.10g")
    design, grids = information_scenarios()
    design.to_csv(out / "conditional_information.csv", index=False, float_format="%.10g")
    grids.to_csv(out / "hypothetical_substrate_grids.csv", index=False, float_format="%.10g")
    summary = {"version": "0.1.0", "data_kind": "23 archived observations; no new biological experiment",
               "source_commit": manifest["source_commit"], "input_sha256": {r["path"]: r["sha256"] for r in manifest["files"]},
               "fits": summaries, "limitations": ["Enzyme identity and assay details not established from the retained metadata.",
               "Repeated concentration rows are not assumed to be independent biological replicates.",
               "No causal treatment comparison or inhibition-mechanism inference.",
               "Profile intervals are conditional and asymptotic; local information scenarios are hypothetical."],
               "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "matplotlib"]}}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
    make_figures(frame, residual_data, profile_data, summaries, design, out)
    lines = ["# Enzyme kinetics workbench: example results", "", "These are fitted descriptions of the archived R Puromycin data, not new measurements or a causal treatment experiment.", "", "| State | Scope | Rows | Vmax (counts/min/min) | Km (ppm) | Approx. 95% profile interval for Km |", "| --- | --- | ---: | ---: | ---: | --- |"]
    for state, scopes in summaries.items():
        for scope, fit in scopes.items():
            interval = fit["km_profile"]
            lo = f"{interval['approximate_95_percent_lower']:.4f}" if interval["lower_closed"] else "open"
            hi = f"{interval['approximate_95_percent_upper']:.4f}" if interval["upper_closed"] else "open"
            lines.append(f"| {state} | {scope} | {fit['n']} | {fit['vmax']:.2f} | {fit['km']:.4f} | {lo}–{hi} |")
    lines += ["", "The low-range refits deliberately use only concentrations at or below 0.11 ppm. They show sensitivity to removing observed high-concentration data, not a recommendation for future assays. Profile intervals assume independent, constant-variance Gaussian errors and use an asymptotic cutoff; coverage is not validated for these small archived runs.", "", "![Observed data and fitted curves](fitted_curves.png)", "", "Solid curves span the observed range; dotted extensions above 1.1 ppm have no validating observations. The model's asymptote is not direct evidence that saturation was experimentally established.", "", "![Residual checks](residual_diagnostics.png)", "", "Residuals are observed minus fitted rate. Scatter without a visible pattern does not prove the error assumptions.", "", "![Km profiles](km_profiles.png)", "", "The horizontal line is the approximate 95% likelihood-ratio cutoff. An open profile endpoint means the cutoff was not reached within broad computational bounds, not that the true parameter is infinite.", "", "![Conditional information scenarios](conditional_information.png)", "", "These dimensionless comparisons fix Vmax = Km = 1, twelve independent measurements and unit error variance. The grids are mathematical scenarios, not observed data or validated experimental designs. Lower condition numbers indicate less local degeneracy for the chosen log-parameter coordinates only.", "", "See [methods](../docs/methods.md), [biology and concepts](../docs/biology-and-concepts.md), and [provenance](../data/README.md) before interpreting these estimates."]
    (out / "report.md").write_text("\n".join(lines) + "\n")
    return summary


def make_figures(frame, residuals, profiles, summaries, information, out):
    colors = {"treated": "#a64b25", "untreated": "#1c6786"}
    fig, ax = plt.subplots(figsize=(8, 5.2), layout="constrained")
    for state, color in colors.items():
        data = frame[frame.state == state]
        fit = summaries[state]["full_range"]
        ax.scatter(data.conc, data.rate, color=color, s=45, label=f"{state}: observed")
        x = np.linspace(float(data.conc.min()), float(data.conc.max()), 200)
        ax.plot(x, michaelis_menten(x, fit["vmax"], fit["km"]), color=color)
        ext = np.linspace(float(data.conc.max()), 2.2, 100)
        ax.plot(ext, michaelis_menten(ext, fit["vmax"], fit["km"]), color=color, ls=":")
    ax.axvline(1.1, color="#777", lw=1, ls="--", label="Largest observed concentration")
    ax.set(xlabel="Substrate concentration (ppm)", ylabel="Initial rate (counts/min/min)", title="Archived observations and separate nonlinear fits")
    ax.legend(fontsize=9, loc="lower right")
    fig.savefig(out / "fitted_curves.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for state, ax in zip(colors, axes):
        data = residuals[residuals.state == state]
        ax.scatter(data.conc, data.residual_observed_minus_fitted, color=colors[state], s=45)
        ax.axhline(0, color="#888", lw=1)
        ax.set(xlabel="Substrate concentration (ppm)", ylabel="Residual (counts/min/min)", title=state)
    fig.savefig(out / "residual_diagnostics.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for state, ax in zip(colors, axes):
        for scope, style in [("full_range", "-"), ("low_range_only", "--")]:
            data = profiles[(profiles.state == state) & (profiles.scope == scope)]
            ax.plot(data.km, data.likelihood_ratio, color=colors[state], ls=style, label=scope.replace("_", " "))
        ax.axhline(PROFILE_CUTOFF, color="#777", ls=":", label="Approx. 95% cutoff")
        ax.set(xscale="log", ylim=(0, 12), xlabel="Profile Km (ppm)", ylabel="Profile likelihood-ratio statistic", title=state)
        ax.legend(fontsize=8)
    fig.savefig(out / "km_profiles.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4.5), layout="constrained")
    ax.bar(information.scenario, information.information_condition_number, color=["#a64b25", "#947047", "#1c6786"])
    ax.set(yscale="log", ylabel="Local information condition number (log scale)", title="Hypothetical grids under a fixed model and noise assumption")
    fig.savefig(out / "conditional_information.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    try:
        summary = run(out=args.out)
    except (ValueError, OSError, KeyError) as error:
        print(f"Analysis stopped: {error}", file=sys.stderr)
        return 2
    print(f"Verified 23 archived observations; fitted four curves and wrote results to {args.out}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
