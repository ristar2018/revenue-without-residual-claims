# Missing statement items

## Typology

Firm-years are classified by the dominant missing pattern of the 28 statement
items parsed from the notes tables.

| Class | Definition | Firm-years |
|---|---|---|
| T1 | Institutional non-applicability: item created by an accounting standard after the observation year | 54 |
| T2 | Structural zero: item not applicable to the firm's business | 42 |
| T3 | Not separately presented: item exists but is not disclosed as a separate line | 90 |
| T4 | Collection gap: item is reported but not captured | 35 |
| T5 | Whole statement missing (13 or more items absent in one firm-year) | 0 |
| **Total** | | **225** |

## Items

`pre2019` and `post2019` counts are in `data/miss_typology.csv`; they separate
items absent because a standard did not yet require them from items absent for
other reasons.

| Variable | Missing firm-years | Share of 225 | Dominant class |
|---|---|---|---|
| `bond` | 186 | 82.7% | T2 |
| `rou` | 133 | 59.1% | T1 |
| `dep_fa` | 130 | 57.8% | T3 |
| `lease_liab` | 129 | 57.3% | T1 |
| `cash_staff` | 118 | 52.4% | T3 |
| `credit_imp` | 116 | 51.6% | T1 |
| `gw` | 98 | 43.6% | T2 |
| `asset_imp` | 84 | 37.3% | T2 |
| `ip` | 80 | 35.6% | T3 |
| `st_loan` | 73 | 32.4% | T4 |
| `ncl_due1y` | 68 | 30.2% | T4 |
| `lt_loan` | 65 | 28.9% | T4 |
| `int_exp` | 28 | 12.4% | T4 |
| `cip` | 27 | 12.0% | T3 |
| `total_revenue` | 17 | 7.6% | T4 |
| `ar` | 16 | 7.1% | T4 |
| `np_parent` | 12 | 5.3% | T4 |
| `other_ar` | 9 | 4.0% | T4 |
| `am_lt` | 7 | 3.1% | T4 |
| `ia` | 5 | 2.2% | T3 |
| `inventory` | 5 | 2.2% | T4 |
| `staff_pay` | 4 | 1.8% | T3 |
| `am_ia` | 4 | 1.8% | T4 |
| `revenue` | 2 | 0.9% | T4 |
| `fa` | 2 | 0.9% | T4 |
| `int_inc` | 1 | 0.4% | T4 |
| `fin_exp` | 1 | 0.4% | T4 |
| `net_profit` | 1 | 0.4% | T4 |

## Zero-fill sensitivity

Setting all T1 and T2 items to zero raises the estimation sample from
115 to 132 firm-years. R-squared falls from 0.645 to 0.508
because the added cases carry no deduction-line variation.

| Variable | Listwise coefficient | p | Zero-filled coefficient | p |
|---|---|---|---|---|
| Depreciation intensity | 1.318 | 0.008 | 0.758 | 0.150 |
| Interest burden | -3.772 | 0.047 | -3.504 | 0.009 |
| Impairment | -1.413 | 0.029 | -1.048 | 0.008 |

Coefficient signs are unchanged and depreciation loses significance at the 5%
level. `code/miss_typology.py` reproduces both tables.
