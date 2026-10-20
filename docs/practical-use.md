# Practical use

## Where this fits

This workbench is useful when learning how to review a nonlinear fit before attaching biological meaning to its parameters. Its new concentration audit asks a specific question: how much does each measured substrate level influence the fitted maximum rate and half-saturation parameter? It works on the included historical dataset, with the same model and fitting settings as the main analysis.

The audit removes all rows at a concentration together. This avoids describing two measurements at the same substrate level as two independent tests of that level. It does not establish that either the remaining or omitted rows are independent biological replicates. The original metadata describe one run per label; the underlying experimental structure remains a limitation. See [provenance](../data/README.md).

## Input and output contract

Run `python audit_kinetics.py --out PATH` from the repository. Without `--out`, it writes to `examples/concentration-audit`. Input remains the checksum-verified `data/` snapshot. The command refuses the source-data and main-results directories as audit destinations.

For each label and each of its six concentrations, the script fits the other five levels. `concentration_sensitivity.csv` records omitted row IDs and counts, retained range, fitted parameters, percentage changes from the full fit, and RMSE on the omitted rows. `prediction_scope` is `within_retained_range`, `below_retained_range` or `above_retained_range`. Endpoint omissions therefore make the extrapolation visible. `audit.json` adds input hashes, full-fit reference values and maximum absolute changes; `report.md` provides the readable table. The command returns status 2 on invalid inputs or failed fitting.

The separate command `python verify_kinetics.py --out PATH` cross-checks all 16 saved fits through different numerical code. Use `--data-dir`, `--results-dir` and `--audit-dir` to verify a different source snapshot and the corresponding newly generated result tables; defaults select the included files. It writes `fit_comparison.csv` and `verification.json`, including input-table hashes and declared tolerances. Exit 0 means agreement, 1 a completed disagreement, and 2 an input/numerical/output failure. It does not require R or replace the original fit.

## Worked use case

Start with the full fit, then ask whether the apparent half-saturation parameter is highly dependent on a single substrate level:

```bash
python kinetics.py --out /tmp/kinetics-main
python audit_kinetics.py --out /tmp/kinetics-audit
python verify_kinetics.py --results-dir /tmp/kinetics-main --audit-dir /tmp/kinetics-audit --out /tmp/kinetics-verification
```

The included audit runs 12 refits and omits each of the 23 rows exactly once. The largest absolute Km changes are 12.66% for `treated` and 27.36% for `untreated`; the corresponding maximum absolute Vmax changes are 1.97% and 3.90%. These maxima may arise from different omissions. They describe perturbations of these observations, not confidence intervals or general error rates. Read the individual rows before drawing a conclusion about a concentration's role.

## Checks before relying on a result

- Confirm the source hashes and original units. A Km recorded in ppm is not a molar binding affinity.
- Check which rows left each fit, whether an endpoint was removed and whether the optimizer reached a computational bound.
- Compare parameter movement with residual behavior and the existing profile, rather than treating one summary as a verdict on a point.
- Keep every original observation. Sensitivity is a prompt for review; it is not evidence of an erroneous measurement.

These are operator checks. The software verifies the data snapshot, grouping and numerical contract; it cannot reconstruct missing assay metadata or decide whether the model is biologically adequate.

## Known limits

This is a deterministic sensitivity analysis within two small archived runs. Omitted-row errors are not an independent validation estimate. There is no automatic outlier rejection, correction for unknown within-run dependence, uncertainty calibration, or causal treatment test. The original curve and recorded baseline results are preserved. Alternative weighting or nonlinear mechanisms could change the conclusions and need their own evidence.

## Next improvements

1. **Cross-language comparison:** the separate Python numerical implementation now passes all 16 comparisons. A future R comparison would add another software stack; accept when identical objectives and declared tolerances are checked for every fit.
2. **Documented error-model sensitivity:** add a justified alternative variance model only with an explicit measurement rationale; accept when assumptions, residual diagnostics and comparison outputs are recorded separately.
3. **Additional annotated public data:** support a second dataset only when units, experimental identifiers and reuse terms are verified; accept when no metadata are inferred from variable names.
4. **Run packaging:** add an output manifest containing hashes for every audit artifact; accept when editing or deleting any listed artifact causes verification to fail.
