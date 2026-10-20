# Methods and output contract

## Inputs and scope

The pipeline analyzes one fixed, included dataset, not arbitrary uploaded assay tables. `data/Puromycin.R` and `data/Puromycin.Rd` are pinned upstream files; `data/puromycin.csv` is their deterministic data conversion. `load_data()` checks byte lengths and SHA-256 hashes against `data/manifest.json` before parsing. It also reconverts the literal R vectors and requires byte-for-byte equality with the CSV. No R code is evaluated.

The CSV columns are `row_id` (a generated, unique row index), `conc` (ppm), `rate` (counts/min/min) and `state` (`treated` or `untreated`). The R vector called `vel` is renamed `rate`, matching the upstream data-frame construction. All 23 observations are retained; there is no filtering for residual size and no averaging of repeated concentrations. Both labels cover six distinct concentrations; the treated group has 12 observations and the untreated group has 11. No independent experimental-unit IDs are available.

The reusable numerical functions require finite positive observed concentrations and rates, at least three paired observations, and at least two distinct concentrations. Zero substrate is allowed for evaluating a model curve, but not for fitting this fixed positive-input analysis. This contract is a software choice for this project, not a biological claim that zero-substrate controls are inappropriate.

## Fitting and numerical checks

For each label, the script minimizes unweighted residual sum of squares (RSS) for

\[
v(S;V,K)=VS/(K+S),\qquad V>0,\quad K>0.
\]

It optimizes \((\log V,\log K)\) with SciPy `least_squares`, its default trust-region reflective method and ordinary squared-error loss. Both parameters have broad computational bounds of \(10^{-9}\) to \(10^9\) in their respective units. These are numerical limits, not biological prior information. Nine starts combine maximum observed rate multiplied by 0.5, 1 or 2 with minimum, median or maximum observed concentration. The converged fit with the smallest RSS is retained. Multiple starts reduce sensitivity to a particular initialization; they do not prove a global optimum for a general nonlinear problem.

The analytic Jacobian with respect to the log parameters is

\[
\frac{\partial v}{\partial\log V}=v,\qquad
\frac{\partial v}{\partial\log K}=-v\frac{K}{K+S}.
\]

`ftol`, `xtol` and `gtol` are each \(10^{-12}\), with at most 2,000 function evaluations per start. The report records convergence counts and proximity to bounds. All nine starts converge for each of the four included fits, and no selected estimate is near a bound. Tests check recovery of known parameters from a noiseless curve and compare the analytic Jacobian with independent finite differences.

Residuals are observed minus fitted rate. RMSE is \(\sqrt{RSS/n}\); the separately named residual standard deviation is \(\sqrt{RSS/(n-2)}\). Neither number measures prediction accuracy in a new biological experiment. The log-parameter information condition number and local correlation use \(J^\mathsf{T}J\) and its pseudoinverse; they are local approximations, conditional on the model and parameter coordinates.

## Profile calculation

For fixed \(K\), write \(g_i=S_i/(K+S_i)\). The conditional least-squares estimate is

\[
\widehat V(K)=\frac{\sum_i g_i y_i}{\sum_i g_i^2},
\]

clipped to the same computational bounds as the nonlinear fit. This analytic solution avoids repeating a two-parameter optimizer at every profile point. Under independent additive Gaussian errors with common unknown variance, profiling the variance gives the likelihood-ratio statistic

\[
T(K)=n\log\!\left\{RSS(K)/RSS(\widehat K)\right\}.
\]

The displayed interval endpoints solve \(T(K)=\chi^2_{1,0.95}\), approximately 3.84146, by root-finding in log concentration. Each exported profile contains 240 geometric grid points plus the fitted minimum. Tiny negative numerical deviations from zero are clipped to zero. If no cutoff crossing occurs before a computational limit, the relevant endpoint is `null` in JSON and marked open, rather than inventing a finite bound. If RSS is effectively zero, the method stops because this unknown-variance uncertainty calculation cannot estimate its noise scale.

This is an asymptotic profile-likelihood construction, not an exact small-sample interval or a calibrated bootstrap. Independence, constant variance, Gaussian noise and the mean curve are assumptions. The archive does not establish them, and the runs are small. The implementation uses the general profiling idea discussed by [Raue et al.](https://doi.org/10.1093/bioinformatics/btp358); it does not reuse their code or reproduce their analyses.

## Range sensitivity and hypothetical information

Each label is also fitted using only `conc <= 0.11` ppm, leaving six rows per label. These fits use the identical objective and uncertainty construction. The comparison is a deliberate loss-of-range exercise, not a data-driven threshold search or a recommended design.

The information exercise uses a separate model with \(V=K=1\), independent Gaussian errors of unit variance and 12 hypothetical measurements per scenario. The dimensionless \(S/K\) grids are geometric: 0.03–0.3, 0.7–1.3 and 0.05–20. It exports \(J^\mathsf{T}J\)'s condition number, determinant and implied local parameter correlation. The determinant is the product of information eigenvalues; the condition number is their ratio. These numbers apply to log-parameter coordinates and the stated scaling. No noisy observations are simulated, and no measurements or assay settings are proposed. This is a local comparison at assumed parameter values, not a global design optimization.

## Outputs and reproducibility

| File in the output directory | Contents |
| --- | --- |
| `parameter_estimates.csv` | Four fits: two labels × full or low concentration range; parameters, error summaries, numerical diagnostics and profile endpoints |
| `km_profiles.csv` | Candidate half-saturation values, reoptimized maximum rates, RSS and likelihood-ratio statistic |
| `residuals.csv` | Original observation IDs, fitted rates and residuals for the full-range fits |
| `conditional_information.csv` | Three hypothetical grid summaries |
| `hypothetical_substrate_grids.csv` | All 36 dimensionless grid points |
| `summary.json` | Full-precision fit results, caveats, dependency versions and input hashes |
| `report.md` | Readable result tables, figures and interpretation limits |
| Four `*.png` figures | Fits, residuals, profiles and information comparison |

The analysis contains no random sampling. Dependencies are pinned, and numerical tables are reproducible to floating-point tolerance; byte-identical figure rendering across operating systems is not promised. Python 3.12 is the CI target. R's examples inspired the choice to fit the two labels separately. The Python implementation, derivative checks, profiles and information comparison were written for this project. [References and related tools](references.md) distinguish source data, conceptual references and runtime dependencies.

The CLI accepts `--out PATH`. Invalid fingerprints, missing or malformed inputs, failed convergence and unwritable output locations produce a nonzero exit status and an `Analysis stopped` message. A crash during output writing may leave partial files; a run should be considered complete only after the success message and all expected outputs are present. The checked-in example is not a replacement for rerunning tests after a code change.


## Independent numerical cross-check (round 2)

`verify_kinetics.py` checks all four saved full/low-range fits and all 12 saved omitted-level fits. It does not call the original model, residual, Jacobian, optimizer wrapper or profile function. For each candidate log Km, it calculates `g = S / (Km + S)` and solves `Vmax = sum(g*y) / sum(g*g)`, clipped to the same `[1e-9, 1e9]` numerical bounds. It evaluates residual sums with `math.fsum`, scans 801 evenly spaced log-Km values over those bounds, refines each detected interior basin with SciPy 1.17.0 bounded scalar minimization (`xatol=1e-12`, at most 1,000 iterations), and compares the best candidate with both endpoints.

The independent estimates and the RSS evaluated at saved parameters must each agree with the saved solution under relative tolerance `1e-5` or absolute tolerance `1e-7`. The output includes every comparison and hashes of the saved tables being checked. This is a finite numerical check of the same least-squares objective, not a proof of a global optimum, an independent experiment, or validation of the error model. Exit 0 means all comparisons pass; 1 means a completed comparison differs; 2 means malformed inputs, unsupported keys, numerical failure or an output error. The CLI accepts `--data-dir`, `--results-dir` and `--audit-dir`; these select the inputs actually checked. The new output directory must be separate from all three selected input directories. Existing files in that new directory are replaced on rerun.
