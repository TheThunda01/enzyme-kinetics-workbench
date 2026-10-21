# References and source roles

References are cited by author and year. The [reference audit](reference-audit.json) records the checked metadata, source role and exact access limits for every item below. Checks were completed on 21 October 2026 UTC as part of the review dated 20 October in the user’s local date. Earlier discovery and access records remain in the [literature review](literature-review.md). The [21 October maintenance review](review-2026-10-21.md) adds separately dated source rechecks without replacing those earlier access records.

## Data and historical attribution

- **R Core Team. (2026). Puromycin: Reaction Velocity of an Enzymatic Reaction.** [Official source](https://github.com/wch/r-source/blob/3dc01cf932ce6b21b1fa05883bbecca4bd6fefc2/src/library/datasets/man/Puromycin.Rd). Version: `same pinned commit; current R-devel manual also inspected`. Archived units, initial-rate description, one experiment per label, historical attribution and the separate-fit/partial-linearity examples. The reduced archive does not resolve the cells/enzyme wording or missing assay details.

- **R Core Team. (2026). Puromycin literal dataset.** [Official source](https://github.com/wch/r-source/blob/3dc01cf932ce6b21b1fa05883bbecca4bd6fefc2/src/library/datasets/data/Puromycin.R). Version: `commit 3dc01cf932ce6b21b1fa05883bbecca4bd6fefc2`. 23 values, factor labels and source ordering; deterministic conversion into the project CSV.

- **Bates DM, Watts DG. (1988). Nonlinear Regression Analysis and Its Applications. Wiley, Appendix A1.3.** [Source](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/Puromycin.html). R attributes the dataset to Appendix A1.3 of this book. Metadata/attribution-level check.

- **Treloar MA. (1974). Effects of Puromycin on Galactosyltransferase in Golgi Membranes. Master’s thesis, University of Toronto.** [Source](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/Puromycin.html). R attributes the observations to this University of Toronto master’s thesis. Metadata/attribution-level check.

## Kinetics and identifiability

- **Briggs GE, Haldane JBS. (1925). A Note on the Kinetics of Enzyme Action. Biochemical Journal, 19(2), 338–339.** [DOI: 10.1042/bj0190338](https://doi.org/10.1042/bj0190338); [PMID 16743508](https://pubmed.ncbi.nlm.nih.gov/16743508/). Bibliographic attribution of the historical theoretical treatment. Metadata/attribution-level check.

- **Johnson KA, Goody RS. (2011). The Original Michaelis Constant: Translation of the 1913 Michaelis–Menten Paper. Biochemistry, 50(39), 8264–8269.** [DOI: 10.1021/bi201284u](https://doi.org/10.1021/bi201284u); [PMID 21888353](https://pubmed.ncbi.nlm.nih.gov/21888353/). Historical assumptions and distinction between a kinetic Michaelis constant and binding affinity. Publisher and PMC headers identify Johnson and Goody as the article authors; the differing PubMed list is documented in the audit.

- **Raue A et al. (2009). Structural and practical identifiability analysis of partially observed dynamical models by exploiting the profile likelihood. Bioinformatics, 25(15), 1923–1929.** [DOI: 10.1093/bioinformatics/btp358](https://doi.org/10.1093/bioinformatics/btp358); [PMID 19505944](https://pubmed.ncbi.nlm.nih.gov/19505944/). Profile-likelihood reasoning and the distinction between structural and practical identifiability. Abstract-level appraisal.

- **Wanika L et al. (2024). Structural and practical identifiability analysis in bioengineering: a beginner’s guide. Journal of Biological Engineering, 18(1), 20.** [DOI: 10.1186/s13036-024-00410-x](https://doi.org/10.1186/s13036-024-00410-x); [PMID 38438947](https://pubmed.ncbi.nlm.nih.gov/38438947/). Definitions and illustrative use of structural/practical identifiability and profile analysis.

- **McGuinness AN et al. (2024). Identifiability of enzyme kinetic parameters in substrate competition: a case study of CD39/NTPDase1. Purinergic Signalling, 20(3), 257–271.** [DOI: 10.1007/s11302-023-09942-1](https://doi.org/10.1007/s11302-023-09942-1); [PMID 37165287](https://pubmed.ncbi.nlm.nih.gov/37165287/). A primary example where enzyme-model parameter interactions complicate interpretation. Abstract-level appraisal. Issue year 2024; first published online in 2023.

## Numerical software

- **SciPy developers. (2026). SciPy 1.17.0: least_squares.** [Official source](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.least_squares.html). Version: `1.17.0`. Bounded trust-region reflective nonlinear least squares, ordinary squared-error loss and stopping controls.

- **SciPy developers. (2026). SciPy 1.17.0: brentq.** [Official source](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.brentq.html). Version: `1.17.0`. Root search on a continuous bracket with a sign change, used for profile crossings.

- **SciPy developers. (2026). SciPy 1.17.0: chi2.** [Official source](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.chi2.html). Version: `1.17.0`. The percent-point function returns the declared chi-square quantile.

- **SciPy developers. (2026). SciPy 1.17.0: minimize_scalar.** [Official source](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.minimize_scalar.html). Version: `1.17.0`. Bounded local scalar minimization for the independent numerical route.

## Reuse and interpretation

The input files retain their upstream license and attribution. A software citation documents an interface; a methodological citation documents an idea. Neither demonstrates that the assumptions fit these data or that the project has been experimentally validated. See [assumptions](assumptions.md) for that distinction.
