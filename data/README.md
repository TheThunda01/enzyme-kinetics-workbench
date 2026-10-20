# Data provenance and terms

This directory contains the `Puromycin` dataset from R's `datasets` package. The [official manual](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/Puromycin.html) describes an archived initial-reaction-rate dataset and attributes it to Bates and Watts (1988), Appendix A1.3, and Treloar's 1974 University of Toronto thesis. The thesis title mentions galactosyltransferase in Golgi membranes; the reduced archive does not supply enough information to reconstruct the original assay.

## Pinned files

Retrieved 2026-10-20 from the `wch/r-source` mirror at commit `3dc01cf932ce6b21b1fa05883bbecca4bd6fefc2`:

| File | Role | SHA-256 |
| --- | --- | --- |
| `Puromycin.R` | Unmodified literal data and R data-frame construction | `87a14de98652c3f861d4477752d3293c7943045d6492b59c1d5c0939932feab8` |
| `Puromycin.Rd` | Unmodified upstream documentation | `40359bad37dfcbb1750c3a527b539558b1ccd2cde9faccbde0209996e908e482` |
| `puromycin.csv` | Deterministic data conversion for Python | `38485c080eb7babdabf1e8849b5f08c0b81b0c524a62d7b223eae3399cb49514` |

`manifest.json` records the raw source URLs, file lengths and hashes. The analysis verifies all three files before fitting. These checks establish consistency with this snapshot; they do not authenticate every historical step between the thesis and R.

`convert_r_source()` parses the literal concentration, velocity and state vectors without evaluating R. It preserves order and numeric values, translates factor code 1 to `treated` and 2 to `untreated`, renames `vel` to `rate` to match the final R data frame, and adds `row_id` from 1 through 23. CSV serialization uses UTF-8 and LF line endings. The source is preserved so that the conversion remains inspectable.

## What is actually recorded

There are 12 treated and 11 untreated observations, each labeled with concentration and rate. Concentration is in ppm; rate is in counts/min/min. Both groups cover 0.02, 0.06, 0.11, 0.22, 0.56 and 1.1 ppm. There are repeated concentration rows, but no experimental-unit IDs, calibration data or complete assay metadata. The R documentation describes one treated and one untreated experiment. Consequently, the rows are observations, not a documented sample of 23 independent biological replicates.

The source does not establish a species, molar substrate units, a turnover number, or how puromycin acted in the reported system. `treated` and `untreated` are retained labels, not a basis for causal interpretation.

## License

The upstream `.Rd` file retains R Core Team's copyright and the GNU General Public License, version 2 or later notice. The bundled R files and this converted dataset are distributed with those **GPL-2.0-or-later** terms; [GPL-2.txt](GPL-2.txt) is included. Original project code and documentation have their separate MIT license. The MIT license does not replace upstream notices or relicense these data files.
