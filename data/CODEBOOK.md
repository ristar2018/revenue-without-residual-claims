# Codebook

## `panel_annual_2015_2025_v2.csv`

Firm-year panel, 24 firms x 11 years (2015-2025) = 264 rows. Monetary values in
RMB unless stated.

| Variable | Type | Missing |
|---|---|---|
| `code` | str | 0 |
| `name` | str | 0 |
| `tier` | str | 0 |
| `year` | int64 | 0 |
| `revenue` | float64 | 0 |
| `net_profit` | float64 | 0 |
| `roe` | float64 | 0 |
| `rev_yoy` | float64 | 1 |
| `np_yoy` | float64 | 1 |
| `gross_margin` | float64 | 0 |
| `unit` | str | 0 |
| `revenue_src` | str | 0 |
| `fetched_at` | str | 0 |

`tier` classifies operating scope: A = firm operates the scenic area directly,
B = partial or indirect operating exposure, C = travel services without direct
scenic operation.

## Other files

`fin_panel.csv` holds statement items in wide form (one column per item, values
in RMB). `fin_miss.csv` is the item-by-firm-year missing matrix with `miss`
listing the absent items separated by semicolons. `contract_terms_v4.csv` is
defined in `docs/CODING_MANUAL.md`. `h2_panel.csv` is the estimation panel with
scaled variables; `h2_results.csv` and `h2_robust.csv` hold coefficients and
standard errors. Monetary fields in `contract_terms_v4.csv` are in RMB; the
scaling used in the regressions is described in the manuscript.
