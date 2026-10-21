# Rapid literature and practice review

## Question and scope

What small addition would make the archived enzyme-kinetics analysis more useful to someone reviewing a fit? This review focused on parameter identifiability, sensitivity to limited data and inspectable nonlinear fitting. It did not seek new enzyme mechanisms or a protocol for collecting measurements. Recent discovery covered 2022-01-01 through 2026-10-20; the original data documentation and foundational profiling reference were retained separately.

**Round 02, also 2026-10-20.** This update asks a narrower implementation question: can saved parameters be checked through an independent numerical route while preserving the objective? It is not a claim of new elapsed-time surveillance. The first-round search and conclusions remain above; the new record is [search-update-02.json](search-update-02.json).

## Search record

The searches below are the preserved development record, not a claim that the literature search was rerun for the editorial review. The [21 October UTC source recheck](reference-audit.json) records current metadata, inspected passages and access limits. It does not add a new systematic-search yield.

The [machine-readable log](search-log.json) contains exact executed queries, date fields, sorting, returned PMIDs and decisions. PubMed was searched first. The broad title/abstract query for enzyme kinetics plus identifiability, parameter estimation or sensitivity analysis returned 12 records; all 12 were screened by title and abstract. A targeted quoted-title query for Wanika returned zero, with a provider warning. A DOI query then returned that one record. There were 13 distinct recent records screened and two selected for this narrowly defined change. These are query yields, not counts of all relevant literature.

The returned list included a December 2026 issue-dated item despite the upper date filter. It was excluded because earlier publication timing was not resolved. Other exclusions concerned different mechanistic systems, a methods chapter, or applications that did not inform this bounded addition. The source log preserves the individual decisions. Official R and versioned SciPy documentation were inspected by direct URL, and the prior Raue reference was retained. Their retrieval is supplementary and is not counted as PubMed search yield.

A new PubMed query combined “variable projection” with kinetic/biochemical terms, limited to publication dates 2022-01-01 through 2026-10-20. It returned zero records. That narrow-query outcome does not imply absence of relevant methods. Rather than broaden into unrelated biomedical mechanisms, the update inspected the official R partial-linearity example and SciPy 1.17.0 scalar-optimization documentation. No new primary biomedical paper was selected.

## What the sources support

| Source | Type and access | Relevant finding or resource | Limit | Implementation consequence |
| --- | --- | --- | --- | --- |
| [McGuinness et al. (2024; online 2023)](https://pubmed.ncbi.nlm.nih.gov/37165287/), 2024 issue / 2023 online | Primary enzyme-kinetics study; PubMed and publisher abstract only. PMC retrieval failed. | Their CD39 case identifies parameter interactions that remain difficult under nonlinear fitting. | A substrate-competition mechanism differs from this two-parameter curve; no transfer of parameter values or validation. | Keep numerical convergence separate from identifiability and interpretation. |
| [Wanika et al. (2024)](https://pubmed.ncbi.nlm.nih.gov/38438947/), 2024 | Primary illustrative bioengineering analyses; publisher introduction and methods inspected | Distinguishes structural and practical identifiability and explains profile-based analysis. | Its dynamic models are not the Puromycin experiment. | Retain profiles and add a separate data-perturbation view; do not call it another confidence interval. |
| [Raue et al. (2009)](https://doi.org/10.1093/bioinformatics/btp358) | Foundational method, retained from the original project; citation/method description checked previously | Profiles examine compatibility while other parameters are reoptimized. | Does not establish this archive's error model. | Preserve the original profile implementation and its conditional interpretation. |
| [Official R Puromycin documentation](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/Puromycin.html) | Official dataset documentation; pinned source revision `3dc01cf932ce6b21b1fa05883bbecca4bd6fefc2` included | Supplies units, labels and limited experimental provenance. | Does not supply independent replicate IDs or complete conditions. | Omit whole concentration levels and retain row IDs; avoid claims of independent validation. |
| [SciPy 1.17.0 `least_squares`](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.least_squares.html) | Official versioned API documentation | Defines bounded nonlinear least-squares behavior. | A solver's success is not evidence that the model is correct. | Reuse the tested nine-start fit and report computational-bound flags. |

The concentration audit is an independent implementation choice motivated by these concerns. None of the papers is claimed to prescribe or validate this exact leave-one-level-out procedure. No external analysis code was copied. R source/data retain GPL-2.0-or-later terms; original project code remains MIT. SciPy is a dependency, not vendored source.

| Round-02 source | Access and relevant support | Limit and code consequence |
| --- | --- | --- |
| [R Puromycin manual](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/Puromycin.html) | Official example includes fitting through partial linearity; pinned data remain unchanged. | Conceptual starting point only. This code does not run R or claim agreement with R. |
| [SciPy 1.17.0 scalar minimization](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.minimize_scalar.html) | Official API/notes describe local bounded minimization. | Use an explicit preliminary grid and endpoints; do not claim a proof of global optimality. |

The formula eliminating Vmax is derived from this project's squared-error objective. Agreement between independent calculations is evidence of numerical consistency, not biological validation or identifiability. No external implementation was copied.

## Changes made

`audit_kinetics.py` now performs all 12 concentration-level omissions, exports the omitted IDs, parameter shifts and range-aware prediction errors, and leaves baseline results intact. Tests verify grouping, complete coverage, a known noiseless curve, source verification and refusal to overwrite main-result destinations. The [practical guide](practical-use.md) explains how to read the audit without turning sensitivity into automatic data deletion.

Round 02 adds `verify_kinetics.py`: a separately implemented conditional Vmax calculation, scalar log-Km search, and comparison of all 16 saved full, low-range and omitted-level fits. Tolerances are declared before comparison (`rtol=1e-5`, `atol=1e-7`). Known-parameter and deliberately wrong-parameter tests check the verifier's behavior. Existing result files are preserved.

## Remaining work

An independent R comparison would strengthen numerical verification. An alternative error model or new dataset could also be informative, but each would need a declared scientific rationale and separate validation. The practical guide lists acceptance criteria so these remain concrete future tasks.

The independent Python route now replaces the previously unmet numerical cross-check. Cross-language agreement could still add confidence in software implementation; it would not resolve missing experimental metadata. A mathematically certified global bound and alternative error models remain outside scope.

## Limits of this review

This was a bounded, single-workflow rapid review in one publication database plus selected official resources. Search phrasing and title/abstract indexing can miss relevant work; no citation-network expansion or duplicate independent screening was done. One selected paper was appraised only from its abstract. No protected abstracts or paper text are redistributed. The review supports an educational software improvement, not comprehensive methodological guidance or biological validation.

Round 02 did not find a new primary paper through its exact query and relies on official numerical references plus the earlier biological appraisal. The verification is deliberately conditional on the unchanged model and data. The small search is recorded as such, without a fabricated systematic-review yield.
