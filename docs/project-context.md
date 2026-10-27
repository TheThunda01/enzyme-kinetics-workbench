# Why this project exists

A convincing curve can leave its parameters poorly determined. Enzyme kinetics studies the rates of enzyme-catalyzed reactions, often through curves that rise and level off. Interpreting a curve's height and bend requires examining the measurements, the model and the observed concentration range.

This workbench explores that problem with R's archived `Puromycin` dataset. Its 23 observations contain substrate concentration, initial reaction rate and a treated or untreated label. The original units are retained throughout. The official documentation traces the data through Bates and Watts to Treloar's 1974 thesis, but the small table does not retain enough experimental detail for a new biological or causal interpretation. [The provenance note](../data/README.md) separates that attribution from what the archive actually records.

The script first fits the two groups separately, keeps the parameters positive and reports residuals (observed minus fitted rate) alongside the estimates. These steps let readers inspect how well a nonlinear curve describes the observations.

The next question concerns uncertainty: which other parameter values remain compatible with the observations under the assumed error model? A profile likelihood varies the half-saturation parameter and refits the maximum rate at each candidate value. This approach connects the project to work on practical identifiability, including [Raue et al. (2009)](https://doi.org/10.1093/bioinformatics/btp358) and [Wanika et al. (2024)](https://doi.org/10.1186/s13036-024-00410-x).

The next step removes the high-concentration observations and repeats the fit. It is a sensitivity exercise using the same archive, not a new experiment. A final, dimensionless calculation compares three hypothetical concentration ranges. It makes the link between information and measurement range visible while holding the model and noise assumptions fixed.

The repository demonstrates nonlinear optimization, analytic derivatives, uncertainty profiling, scientific visualization and reproducible data handling. These tools describe the archive and expose questions it cannot answer. They do not establish a drug mechanism, binding affinity or treatment effect.

Read the [biology and concepts](biology-and-concepts.md) for the reasoning behind the model, the [methods](methods.md) for the exact calculation, and the [example report](../results/report.md) for the outputs. The recurring themes are measurement, model assumptions, identifiability and the difference between interpolation and extrapolation.

For definitions, see the [glossary](glossary.md); for the rationale and limits of each material choice, see the [assumptions](assumptions.md).

## Where this fits in the portfolio

Begin the featured reading route here, then visit [GFP active learning](https://github.com/TheThunda01/gfp-active-learning) to examine whether a selection rule helps prediction. [MAPK dynamics](https://github.com/TheThunda01/mapk-dynamics-lab) asks which virtual observation distinguishes competing hypotheses. The [portfolio guide](https://github.com/TheThunda01/TheThunda01/blob/main/PROJECT_GUIDE.md) connects these questions; the studies use separate datasets and models, with no transfer of results between them.
