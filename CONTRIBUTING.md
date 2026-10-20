# Contributing

Changes should make the analysis easier to inspect or its assumptions easier to test. Please explain the scientific question, source and license of any new data, and which conclusions the proposed change can support.

Before submitting a change, install the pinned dependencies, run `python -m unittest discover -s tests -v`, and reproduce the outputs with `python kinetics.py --out /tmp/enzyme-kinetics-results`. Keep the tests independent where possible: known-parameter recovery and finite-difference derivative checks are more useful than copying an implementation into its test. Review numerical tables and figures after a methods change.

The bundled source files are a historical snapshot. Do not edit their values to improve a fit or silently replace them with a newer source. A deliberate data update needs a new provenance record, hashes, conversion checks and a clear account of changed results. New biological claims need a reliable primary or official source and explicit limits on what the data establish.

Report reproducible software problems with the command, Python/dependency versions and error output. The repository is an educational analysis, not an assay protocol or a validated clinical tool.
