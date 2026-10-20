# Concentration-level sensitivity

Each refit leaves out all observations at one substrate concentration within one archived label. No observation is permanently removed.

| Label | Omitted ppm | Rows left out | Prediction scope | Vmax change % | Km change % | Omitted RMSE |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| treated | 0.02 | 2 | below_retained_range | 1.85 | 12.66 | 20.53 |
| treated | 0.06 | 2 | within_retained_range | -0.17 | -1.42 | 5.19 |
| treated | 0.11 | 2 | within_retained_range | -0.18 | -3.37 | 9.33 |
| treated | 0.22 | 2 | within_retained_range | 1.06 | -1.79 | 12.13 |
| treated | 0.56 | 2 | within_retained_range | -1.97 | -4.30 | 9.52 |
| treated | 1.1 | 2 | above_retained_range | -1.68 | -4.54 | 6.45 |
| untreated | 0.02 | 2 | below_retained_range | 3.90 | 27.36 | 19.48 |
| untreated | 0.06 | 2 | within_retained_range | -1.11 | -10.24 | 7.55 |
| untreated | 0.11 | 2 | within_retained_range | 0.04 | -5.37 | 11.13 |
| untreated | 0.22 | 2 | within_retained_range | 1.12 | 0.66 | 6.55 |
| untreated | 0.56 | 2 | within_retained_range | -2.57 | -6.77 | 9.43 |
| untreated | 1.1 | 1 | above_retained_range | -2.32 | -6.89 | 9.51 |

RMSE retains the source rate units (counts/min/min). Endpoint omissions ask the refit to extrapolate beyond its retained concentration range. The errors share the same archived experiments and are not an independent validation set. Larger changes are prompts to inspect model dependence, not automatic outlier flags. See [practical use](../../docs/practical-use.md).
