# Practical use

## Where this fits

Use this workbench to review a nonlinear fit before interpreting its parameters biologically. The concentration audit asks how much each measured substrate level influences the fitted maximum rate and half-saturation parameter. It uses the included historical dataset and the main analysis's model and fitting settings.

The audit removes all rows at a concentration together, so two measurements at the same level do not become two independent tests of that level. Neither the retained nor omitted rows establish independent biological replication. The original metadata describe one run per label, leaving the experimental structure unresolved. See [provenance](../data/README.md).

## Input and output contract

Run `python audit_kinetics.py --out PATH` from the repository. Without `--out`, it writes to `examples/concentration-audit`. Input remains the checksum-verified `data/` snapshot. The command refuses the source-data and main-results directories as audit destinations.

For each label and each of its six concentrations, the script fits the other five levels. `concentration_sensitivity.csv` records omitted row IDs and counts, retained range, fitted parameters, percentage changes from the full fit, and root mean squared error (RMSE) on the omitted rows. `prediction_scope` is `within_retained_range`, `below_retained_range` or `above_retained_range`. Endpoint omissions therefore make the extrapolation visible. `audit.json` adds input hashes, full-fit reference values and maximum absolute changes; `report.md` provides the readable table. The command returns status 2 on invalid inputs or failed fitting.

The separate command `python verify_kinetics.py --out PATH` cross-checks all 16 saved fits through different numerical code. Use `--data-dir` to select another location containing the same pinned source snapshot, and `--results-dir` and `--audit-dir` to select the corresponding result tables; defaults select the included files. A changed dataset is rejected by the source checks and would require a deliberate code and provenance update. The verifier writes `fit_comparison.csv` and `verification.json`, including input-table hashes and declared tolerances. Exit 0 means agreement, 1 a completed disagreement, and 2 an input/numerical/output failure. It does not require R or replace the original fit.

## Worked use case

Start with the full fit, then ask whether the apparent half-saturation parameter is highly dependent on a single substrate level:

```bash
python kinetics.py --out /tmp/kinetics-main
python audit_kinetics.py --out /tmp/kinetics-audit
python verify_kinetics.py --results-dir /tmp/kinetics-main --audit-dir /tmp/kinetics-audit --out /tmp/kinetics-verification
```

The included audit runs 12 refits and omits each of the 23 rows exactly once. Here $`K_m`$ denotes the apparent half-saturation concentration and $`V_{\max}`$ the fitted limiting rate. The largest absolute $`K_m`$ changes are 12.66% for `treated` and 27.36% for `untreated`; the corresponding maximum absolute $`V_{\max}`$ changes are 1.97% and 3.90%. These maxima may arise from different omissions. They describe perturbations of these observations, not confidence intervals or general error rates. Read the individual rows before drawing a conclusion about a concentration's role.

## Checks before relying on a result

- Confirm the source hashes and original units. A $`K_m`$ recorded in ppm is not a molar binding affinity.
- Check which rows left each fit, whether an endpoint was removed and whether the optimizer reached a computational bound.
- Compare parameter movement with residual behavior and the existing profile, rather than treating one summary as a verdict on a point.
- Keep every original observation. Sensitivity is a prompt for review; it is not evidence of an erroneous measurement.

These are operator checks. The software verifies the data snapshot, grouping and numerical contract; it cannot reconstruct missing assay metadata or decide whether the model is biologically adequate.

## Known limits

This deterministic analysis measures sensitivity within two small archived runs. Errors on omitted rows do not estimate independent validation performance. The analysis preserves the original curve and baseline results; it does not reject outliers automatically, correct unknown within-run dependence, calibrate uncertainty, or test causal treatment effects. Alternative weighting or nonlinear mechanisms could change the conclusions and need their own evidence.

## Next improvements

1. **Cross-language comparison:** the separate Python numerical implementation now passes all 16 comparisons. A future R comparison would add another software stack; accept when identical objectives and declared tolerances are checked for every fit.
2. **Documented error-model sensitivity:** add a justified alternative variance model only with an explicit measurement rationale; accept when assumptions, residual diagnostics and comparison outputs are recorded separately.
3. **Additional annotated public data:** support a second dataset only when units, experimental identifiers and reuse terms are verified; accept when no metadata are inferred from variable names.
4. **Run packaging:** add an output manifest containing hashes for every audit artifact; accept when editing or deleting any listed artifact causes verification to fail.

For definitions, see the [glossary](glossary.md); for the rationale and limits of each material choice, see the [assumptions](assumptions.md).
