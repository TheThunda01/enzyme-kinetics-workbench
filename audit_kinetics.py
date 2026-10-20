"""Describe sensitivity to leaving out one complete concentration level at a time."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from kinetics import ROOT, fit_curve, load_data, michaelis_menten, validate_xy


def concentration_audit(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Rows at one concentration leave together; this is not independent validation."""
    required = {"row_id", "state", "conc", "rate"}
    if not required <= set(frame) or frame.empty or frame.row_id.duplicated().any():
        raise ValueError("Audit needs unique row IDs, states, concentrations and rates")
    rows, baseline = [], {}
    for state in sorted(frame.state.unique()):
        group = frame[frame.state == state]
        validate_xy(group.conc, group.rate)
        if group.conc.nunique() < 3:
            raise ValueError("Audit needs at least three distinct concentration levels per state")
        full = fit_curve(group.conc, group.rate)
        baseline[state] = full
        for concentration in sorted(group.conc.unique()):
            omitted = group[group.conc == concentration]
            retained = group[group.conc != concentration]
            reduced = fit_curve(retained.conc, retained.rate)
            predicted = michaelis_menten(omitted.conc, reduced["vmax"], reduced["km"])
            position = "below_retained_range" if concentration < retained.conc.min() else (
                "above_retained_range" if concentration > retained.conc.max() else "within_retained_range")
            rows.append({
                "state": state, "omitted_concentration_ppm": float(concentration),
                "omitted_row_ids": ";".join(map(str, omitted.row_id)),
                "omitted_rows": len(omitted), "retained_rows": len(retained),
                "retained_concentration_min_ppm": float(retained.conc.min()),
                "retained_concentration_max_ppm": float(retained.conc.max()),
                "prediction_scope": position,
                "vmax": reduced["vmax"], "km": reduced["km"],
                "vmax_change_percent": 100 * (reduced["vmax"] / full["vmax"] - 1),
                "km_change_percent": 100 * (reduced["km"] / full["km"] - 1),
                "omitted_rmse_counts_per_min_per_min": float(np.sqrt(np.mean((omitted.rate - predicted) ** 2))),
                "at_computational_bound": reduced["at_computational_bound"],
            })
    return pd.DataFrame(rows), baseline


def run(out: Path, data_dir: Path = ROOT / "data") -> dict:
    frame, manifest = load_data(data_dir)
    table, baseline = concentration_audit(frame)
    out = Path(out)
    # Keep the sensitivity report separate from input and baseline result files.
    if out.resolve() in {Path(data_dir).resolve(), (ROOT / "results").resolve()}:
        raise ValueError("Choose an audit output directory separate from data and baseline results")
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "concentration_sensitivity.csv", index=False, float_format="%.10g")
    report = {
        "schema_version": "1.0", "audit": "leave-one-concentration-level-out sensitivity",
        "source_commit": manifest["source_commit"],
        "input_sha256": {entry["path"]: entry["sha256"] for entry in manifest["files"]},
        "baseline_fits": baseline, "refits": len(table),
        "omitted_rows_total": int(table.omitted_rows.sum()),
        "boundary_refits": int(table.at_computational_bound.sum()),
        "max_absolute_percent_changes": {
            state: {parameter: float(group[parameter + "_change_percent"].abs().max())
                    for parameter in ["vmax", "km"]}
            for state, group in table.groupby("state", sort=True)},
        "scope": "Descriptive sensitivity within the same archived experiments; not independent test performance, confidence intervals, or a reason to remove observations.",
    }
    (out / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    lines = ["# Concentration-level sensitivity", "",
             "Each refit leaves out all observations at one substrate concentration within one archived label. No observation is permanently removed.", "",
             "| Label | Omitted ppm | Rows left out | Prediction scope | Vmax change % | Km change % | Omitted RMSE |",
             "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
    for row in table.itertuples():
        lines.append(f"| {row.state} | {row.omitted_concentration_ppm:g} | {row.omitted_rows} | {row.prediction_scope} | {row.vmax_change_percent:.2f} | {row.km_change_percent:.2f} | {row.omitted_rmse_counts_per_min_per_min:.2f} |")
    lines += ["", "RMSE retains the source rate units (counts/min/min). Endpoint omissions ask the refit to extrapolate beyond its retained concentration range. The errors share the same archived experiments and are not an independent validation set. Larger changes are prompts to inspect model dependence, not automatic outlier flags. See [practical use](../../docs/practical-use.md).", ""]
    (out / "report.md").write_text("\n".join(lines))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "examples" / "concentration-audit")
    args = parser.parse_args(argv)
    try:
        result = run(args.out)
    except (ValueError, OSError, KeyError) as error:
        print(f"Audit stopped: {error}", file=sys.stderr)
        return 2
    print(f"Verified inputs; completed {result['refits']} concentration-level refits in {args.out}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
