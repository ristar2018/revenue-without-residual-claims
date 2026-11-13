# Robustness of the deduction-line model

Baseline: firm and year fixed effects, standard errors clustered by firm
(17 clusters), n = 115, R-squared = 0.645.

## Inference reference

| Variable | CR1 normal | t(G-1) | CR2 | Wild bootstrap |
|---|---|---|---|---|
| Depreciation intensity | 0.008 | 0.017 | 0.018 | 0.013 |
| Interest burden | 0.047 | 0.065 | 0.063 | 0.063 |
| Impairment | 0.029 | 0.044 | 0.052 | 0.011 |

## Sample and window variants

| Variable | LOO significant | LOO range | With capex | 2015-2018 | 2019-2024 |
|---|---|---|---|---|---|
| Depreciation intensity | 16/17 | 1.023 to 1.686 | 1.084 (0.051) | 0.442 (0.314) | 1.452 (0.008) |
| Interest burden | 3/17 | -4.707 to -2.206 | -3.906 (0.025) | 1.883 (0.171) | -3.570 (0.134) |
| Impairment | 15/17 | -2.117 to -1.066 | -1.188 (0.062) | -0.382 (0.220) | -0.978 (0.182) |

With a capital expenditure control, the coefficient on capital expenditure
intensity is 0.207 (p = 0.119).

The three results that are not reproduced in `data/h2_robust.csv` are reported in
the manuscript and can be recomputed from `code/build_h2.py`: dropping year
fixed effects, excluding 2022, and excluding the two firms with the largest
revenue bases.

`code/h2_robust.py` regenerates every column above. Wild cluster bootstrap uses
999 Rademacher draws with the null imposed and a fixed seed.
