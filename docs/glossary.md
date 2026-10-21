# Glossary: enzyme kinetics and fitting

These definitions explain how terms are used in this project. A software check, a model assumption and biological evidence answer different questions. See the [assumption register](assumptions.md) for the conditions behind the calculations.

## Biology and measurements

| Term | Meaning here |
| --- | --- |
| Enzyme; catalyst | An enzyme speeds a chemical reaction without being consumed in the overall reaction. |
| Substrate; product | A substrate enters the reaction; a product is formed. The archive does not identify its substrate sufficiently to assign a molar concentration. |
| Enzyme kinetics; initial rate | Kinetics studies how fast reactions proceed. An initial rate describes the early reaction, before substantial changes in conditions; this is how the R source describes the archived rate. |
| Puromycin; galactosyltransferase; Golgi membranes | Puromycin is the historical treatment label. Galactosyltransferase denotes an enzyme that transfers a galactose group; Golgi membranes belong to a cellular processing compartment. The latter terms occur in the upstream thesis title and do not establish the reduced table’s exact assay. |
| ppm | Parts per million. The source records this concentration scale; converting to moles per volume would require additional substance and measurement information. |
| counts/min/min | Change in radioactive counts per minute, per minute of reaction time: `(counts/min)/min`. This instrument-linked rate is not molecules per enzyme per second. |
| Michaelis–Menten curve | The saturating function $`v=\frac{V_{\max}S}{K_m+S}`$ used here. A fit to this shape does not by itself identify its molecular mechanism. |
| $`V_{\max}`$; asymptote; saturation | $`V_{\max}`$ is the curve’s limiting rate as substrate concentration increases. An asymptote is a limiting value approached by a curve. Observing a high concentration does not prove experimental saturation. |
| $`K_m`$; half-saturation | The substrate concentration at which this model predicts half of $`V_{\max}`$. Here it is an apparent parameter in ppm. |
| Apparent parameter | A parameter describing the fitted relationship in the recorded setting without establishing a unique microscopic interpretation. |
| Binding affinity; dissociation constant $`K_d`$ | Affinity concerns binding. $`K_d`$ describes equilibrium dissociation in an appropriate binding model. $`K_m`$ generally also depends on catalytic rates and is not interchangeable with $`K_d`$. |
| Turnover number, kcat | Catalytic events per enzyme per unit time in a specified kinetic model. The archive lacks the enzyme amount and calibrated rate required to estimate it. |
| Steady-state approximation | For the classical simple mechanism, the enzyme–substrate complex changes slowly enough during initial-rate measurement to approximate its derivative as zero; this is not equilibrium of the whole reaction. |
| Cooperativity; substrate inhibition; baseline | Cooperativity is interaction among binding/response events. Substrate inhibition is reduced rate at sufficiently high substrate. A baseline is an additive offset. None is included in the fitted two-parameter curve. |
| Experimental unit; biological replicate | The independently treated or sampled entity, and an independently repeated biological realization. Several rows at one concentration do not establish such replication. |
| Causal effect | A change attributable to a treatment under an adequate design. Separate fits to the two historical labels do not estimate one. |

## Statistics and numerical analysis

| Term | Meaning here |
| --- | --- |
| Parameter; estimate; objective | A parameter is a model constant; an estimate is its fitted value. The objective is the quantity minimized, here the sum of squared residuals. |
| Residual; RSS; RMSE | A residual is observed minus fitted rate. RSS is their squared sum. Root mean squared error (RMSE) is $`\sqrt{\mathrm{RSS}/n}`$ here and uses the same rate units. |
| Residual standard deviation; degrees of freedom | The reported residual standard deviation is $`\sqrt{\mathrm{RSS}/(n-2)}`$; the two fitted parameters consume two degrees of freedom. This formula does not verify the error model. |
| Gaussian; independent; homoscedastic | Gaussian means normally distributed. Independence means one error does not inform another. Homoscedastic means constant error variance. The interval calculation assumes all three. |
| Variance; standard deviation | Variance measures mean squared deviation; standard deviation is its square root, in the original measurement units. |
| Likelihood; profile likelihood | A likelihood scores parameter values using an assumed observation model. A profile varies one parameter while optimizing the others, including the unknown noise variance here. |
| Likelihood-ratio statistic; chi-square cutoff | A comparison of best likelihoods under a restriction. The threshold 3.84146 comes from a chi-square distribution with one degree of freedom; its use is an asymptotic approximation. |
| Asymptotic; confidence interval; coverage | Asymptotic refers to a large-sample approximation. A confidence procedure’s coverage is its long-run probability of containing the target under its assumptions. These small archived groups have no demonstrated 95% coverage. |
| Structural versus practical identifiability | Structural identifiability concerns uniqueness from ideal observations of a specified model. Practical identifiability concerns how finite, noisy observations constrain its parameters. |
| Sensitivity; interpolation; extrapolation | Sensitivity describes change when inputs or choices change. Interpolation predicts within the retained concentration range; extrapolation predicts beyond it. |
| Jacobian; derivative; finite differences | The Jacobian collects derivatives of predictions with respect to parameters. Finite differences approximate derivatives by small numerical changes and provide an independent check here. |
| Log parameters; information matrix | Log parameters are logarithms of positive parameters. The local information matrix `JᵀJ` summarizes sensitivity under unit-variance errors in those coordinates. |
| Eigenvector; eigenvalue; determinant; condition number | An eigenvector specifies a direction preserved by a matrix transformation; its eigenvalue gives the scaling along that direction. For a positive-definite information matrix, the determinant is the product of its eigenvalues and the spectral condition number is their largest-to-smallest ratio. These summaries depend on coordinates and scaling; a singular matrix has no finite condition number. |
| Pseudoinverse; local correlation; degeneracy | A pseudoinverse generalizes an inverse matrix. Its scaled entries provide the reported local parameter correlation. Degeneracy means some parameter directions are much harder to distinguish. |
| Optimization; initialization; bounds; convergence | Optimization searches for a lower objective. Initializations are starting values; bounds restrict the search. Convergence satisfies numerical stopping rules, without proving a biological mechanism or a global optimum. |
| Trust-region reflective method; scalar search; root-finding | The main solver uses bounded local steps. The verifier searches one variable after eliminating Vmax. Root-finding locates where the profile meets its threshold. |
| Tolerance; floating point | A tolerance is an accepted numerical discrepancy. Floating-point arithmetic represents real numbers approximately. |

## Files and reproducibility

| Term | Meaning here |
| --- | --- |
| CLI; API; dependency; CI | Command-line interface; programming interface; required software library; and continuous integration, which runs automated checks after repository changes. |
| CSV; JSON; PNG; Markdown | Plain-text tables; structured data records; image files; and the text format used for this documentation. |
| SHA-256; checksum; fingerprint; manifest; provenance | A SHA-256 fingerprint summarizes file bytes for comparison. A manifest records those values; provenance records origin and processing. Matching bytes do not authenticate a historical experiment. |
| Pinned version; deterministic | Pinned means a specified release or commit. Deterministic means the same inputs and code have no deliberate random variation; small numerical/platform differences can remain. |
| MIT; GPL-2.0-or-later | Separate license labels for original code/documentation and the upstream R data/source. See the actual license files and attribution; one does not replace the other. |
