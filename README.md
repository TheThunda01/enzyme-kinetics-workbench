# Enzyme kinetics workbench

How much can a smooth enzyme-kinetics curve really tell us about its parameters? Enzyme kinetics studies reaction rates; parameters are the constants defining a model’s curve. This project fits a classic saturating model to the 23 archived observations in R's `Puromycin` dataset, then examines residuals, parameter uncertainty and the effect of removing the high-concentration observations. A separate mathematical exercise asks how the range of substrate concentrations changes local parameter information.

## Why this project

The aim is to make model fitting inspectable. A residual is an observed rate minus its fitted value; uncertainty describes how strongly the data constrain the fitted parameters under stated assumptions. You can follow every estimate back to a pinned input, see the assumptions behind an interval and distinguish a fitted curve from evidence about a biological mechanism.

Figure 1 shows why the measured range matters before looking at the archived data. Two illustrative curves have the same slope at zero but different limiting rates. A short rising segment can therefore make those limits difficult to distinguish.

![Two illustrative saturating curves are close near zero but approach different limiting rates over a wider concentration range](docs/figures/concentration-range-illustration.svg)

**Figure 1. Concentration range changes what a curve can reveal.** This is a mathematical illustration, not Puromycin data: curve A uses $`V_{\max}=K_m=1`$ and curve B uses $`V_{\max}=K_m=2`$ in arbitrary units. Both follow the equation in the [biology guide](docs/biology-and-concepts.md#what-the-michaelismenten-equation-says). The [figure builder](tools/build_documentation_figures.py) records these choices in a [manifest](docs/figures/figure-manifest.json).

## What it does

- Fits positive parameters of the saturating Michaelis–Menten curve separately for the archived `treated` and `untreated` labels, using nine starting points for each fit.
- Plots observed rates, fitted curves and residuals, and marks curve extensions beyond the observed concentration range.
- Profiles the apparent half-saturation parameter, reoptimizing the maximum rate at each candidate value. The resulting intervals depend on the assumed curve and error model and use a large-sample (asymptotic) approximation.
- Refits just the observations at or below 0.11 ppm (parts per million) to show how a narrower range changes the estimates and uncertainty.
- Compares three explicitly hypothetical substrate grids using local information in log-parameter coordinates.

Here, a substrate is a reacting molecule; half-saturation is the concentration at which the curve reaches half its limiting rate. Local information describes how predictions respond to small parameter changes. Log-parameter coordinates use logarithms of the positive constants.

The separate concentration audit leaves out each complete concentration level in turn, reports changes in apparent parameters, and labels held-out predictions as interpolation or extrapolation relative to the retained range. It preserves the original analysis.

## Quick start

Use Python 3.12 and the pinned dependencies. No R installation, API key or download is needed for the analysis; the source data are included.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python kinetics.py
```

On Windows, activate the environment with `.venv\Scripts\activate`. To keep a new run separate from the checked-in example:

```bash
python kinetics.py --out /tmp/enzyme-kinetics-results
```

Every run verifies the SHA-256 hashes (fingerprints of file bytes) of the bundled source and data, reproduces the CSV conversion from the original R literals, and stops if the inputs do not match. The command writes five CSV tables, a JSON summary, a Markdown report and four PNG figures. It replaces files with those names in the chosen output directory. [The example report](results/report.md) is ready to read without running Python.

Run the new sensitivity audit separately:

```bash
python audit_kinetics.py
```

The independent numerical check compares all 16 saved full-range, low-range and omitted-level fits using an analytic maximum-rate solution and a one-dimensional half-saturation search:

```bash
python verify_kinetics.py
```

## Example results

Table 1 summarizes the archived-data fits; Figure 2 shows the observations behind those summaries.

**Table 1. Full-range fits to the archived labels.**

| Archived label | Observations | Fitted maximum rate, counts/min/min | Fitted half-saturation, ppm | Approximate 95% profile interval, ppm |
| --- | ---: | ---: | ---: | --- |
| treated | 12 | 212.68 | 0.0641 | 0.0489–0.0830 |
| untreated | 11 | 160.28 | 0.0477 | 0.0334–0.0664 |

The source’s `counts/min/min` means change in radioactive count rate, `(counts/min)`, per minute of reaction time. It is not a turnover rate per enzyme.

These are separate descriptive fits, not an estimate of a causal treatment effect. When only the low-concentration observations are retained, the fitted maximum rates become 174.50 and 126.75 counts/min/min. That sensitivity is a useful reason to inspect the measured range before interpreting the model's asymptote, its limiting rate at very high concentration.

![Observed rates, fitted curves and marked extrapolation](results/fitted_curves.png)

**Figure 2. Archived observations and fitted curves.** Source: [included Puromycin data](data/README.md) and [saved parameter estimates](results/parameter_estimates.csv). Dotted extensions are predictions outside the measured concentration range, not additional observations. These fits describe the labels separately and do not establish a treatment mechanism.

Across the 12 concentration-level refits, the largest absolute change in the apparent half-saturation parameter, Km, is 12.66% for the treated label and 27.36% for the untreated label. These are sensitivity summaries, not confidence limits. See the [audit report](examples/concentration-audit/report.md).

All 16 saved fits also pass the [independent numerical check](examples/numerical-verification/verification.json), using relative tolerance `1e-5` and absolute tolerance `1e-7` for parameters and residual sums of squares. This compares the same objective using different numerical code.

## Practical use and limitations

The [official R documentation](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/Puromycin.html) describes one treated and one untreated experiment. It supplies neither experimental-unit identifiers nor enough assay metadata to reconstruct the work. Repeated rows at a concentration are therefore not assumed to be independent biological replicates. Concentrations are in ppm; the fitted half-saturation parameter is not a molar binding affinity. The thesis title cited by R mentions galactosyltransferase in Golgi membranes, but that attribution does not establish a species, detailed protocol or inhibition mechanism for this reduced table.

The model assumes a simple saturating relationship. A good fit does not verify its mechanism, establish enzyme turnover, or demonstrate that experimental saturation was reached. The uncertainty calculations additionally assume independent, constant-variance normally distributed (Gaussian) errors; those assumptions and small-sample coverage are not established by this archive. The hypothetical information comparison holds the model and noise fixed and is not a validated experimental design recommendation.

## Documentation

| Guide | What you will find |
| --- | --- |
| [Project context](docs/project-context.md) | Question, rationale and skills |
| [Biology and concepts](docs/biology-and-concepts.md) | Meaning of rates, parameters and uncertainty |
| [Methods](docs/methods.md) | Exact model, numerical choices and output fields |
| [References](docs/references.md) | Primary literature and related tools |
| [Data provenance](data/README.md) | Source revision, conversion, hashes and terms |
| [Practical use](docs/practical-use.md) | Worked audit and acceptance checks |
| [Literature review](docs/literature-review.md) | Search, appraisal and implementation decisions |

Definitions and interpretation: [glossary](docs/glossary.md), [assumptions](docs/assumptions.md), [reference audit](docs/reference-audit.json) and [dated review](docs/review-2026-10-20.md).

## Development and reuse

The [methods](docs/methods.md) describe equations, parameter bounds, output fields and failure cases. Tests cover known-parameter recovery, analytic derivatives, source integrity, profile calculations, invalid inputs and an end-to-end run. GitHub Actions runs those tests and reproduces all outputs. See [CONTRIBUTING.md](CONTRIBUTING.md) for changing the analysis responsibly.

Original code and documentation use the [MIT license](LICENSE). The bundled R source files and converted dataset retain their separate [GPL-2.0-or-later terms](data/README.md).

Rebuild Figure 1 with `python tools/build_documentation_figures.py`. It writes only `docs/figures/` and does not rerun or replace the archived-data analysis.
