# revenue-without-residual-claims

Replication package for the manuscript *Revenue without residual claims: how
contract boundaries and reporting boundaries separate revenue growth from
parent-attributable profit in Chinese tourism listed firms*.

The study asks why revenue growth and growth in profit attributable to the
parent diverge in listed tourism firms whose operating rights are defined by
concession and entrusted-management contracts. It follows the divergence from
the contract boundary, where revenue rights are assigned, to the reporting
boundary, where cost obligations and non-controlling claims enter the
consolidated statements.

Repository: <https://github.com/ristar2018/revenue-without-residual-claims>.
Citation metadata is in `CITATION.cff`.

## Headline numbers

| Item | Value |
|---|---|
| Listed firms / firm-years | 24 / 264 (2015-2025) |
| Firm-years with calculable growth | 240 |
| Revenue up, profit down (level criterion, headline) | 40 of 240 (16.7%) |
| Same, A-level operators (17 firms) | 27 of 170 (15.9%) |
| Same, B-level / C-level operators | 7 of 40 (17.5%) / 6 of 30 (20.0%) |
| Revenue up, profit down (growth-rate criterion, companion) | 68 of 240 (28.3%) |
| Same, A-level, growth-rate criterion | 45 of 170 (26.5%) |
| Firm-years with at least one deduction line | 225 |
| Complete deduction-line cases | 165 |
| Contract clauses coded | 99 (7 firms, 32 reports) |
| Agreement-level records | 39 |
| Estimation sample, deduction-line model | 115 (17 firms) |

## What is here

```
data/        derived panels and result tables (CSV)
code/        collection, parsing, estimation and figure scripts
docs/        coding manual, clause inventory, screening log, robustness
figures/     camera-ready figures used in the manuscript
manuscript/  section sources, front-matter metadata, LaTeX, PDF (v1.6)
```

The underlying annual and semi-annual reports are public filings distributed by
CNINFO (巨潮资讯). They are not redistributed here; `code/collect_w1.py`
retrieves them from the public endpoint and `data/pdf_manifest.csv` records the
exact documents used.

Comments, docstrings and console messages in `code/` are in English. Chinese
strings are kept where they are data rather than prose: firm and counterparty
names, the statement labels the parsers match, the categorical values written to
the CSVs, and the Chinese label map in `figs.py` (translated by `figs_en.py`).
Every categorical value is glossed in `docs/CODING_MANUAL.md`.

## Data files

| File | Content |
|---|---|
| `data/panel_annual_2015_2025_v2.csv` | firm-year panel: revenue, parent net profit, tier, deduction lines |
| `data/fin_panel.csv` | statement items parsed from the notes tables |
| `data/fin_vs_em.csv` | cross-check of parsed items against a vendor database |
| `data/fin_miss.csv` | missing-item matrix behind the typology in `docs/MISSING_DATA.md` |
| `data/cashflow_panel.csv` | depreciation, amortisation and capital expenditure |
| `data/contract_terms_v4.csv` | clause-level contract coding (99 records) |
| `data/contract_protocols.csv` | agreement-level protocol summary |
| `data/contract_fee_panel.csv` | fee-to-revenue ratios by firm-year |
| `data/rq1_stats.csv` | divergence counts under both criteria |
| `data/rq2_decomp.csv` | five-part decomposition of the net margin |
| `data/rq3_descriptive.csv`, `data/rq3_protocols.csv` | contract design descriptives |
| `data/h2_panel.csv`, `data/h2_results.csv` | estimation panel and main estimates |
| `data/h2_robust.csv` | inference references, sample and window variants |
| `data/h2_miss_sensitivity.csv` | zero-fill sensitivity |
| `data/incremental_r2.csv` | incremental explanatory power of the deduction lines |
| `data/miss_typology.csv`, `data/miss_rowclass.csv` | missing-data typology |
| `data/overlap_check.csv` | mechanical-overlap diagnostics |
| `data/mgmt_summary.csv`, `data/pdf_manifest.csv` | retrieval and screening record |

`data/CODEBOOK.md` defines every variable.

## Reproducing the results

Python 3.11 with pandas, numpy, statsmodels, scipy and matplotlib. Run from the
repository root; scripts read and write `../data/` relative to `code/`.

```
cd code
python rq1_stats.py          # divergence counts, both criteria
python rq2_decomp.py         # five-part decomposition, identity closure
python rq3_stats.py          # contract descriptives
python build_h2.py           # estimation panel and main models
python h2_robust.py          # CR1 / t(G-1) / CR2 / wild bootstrap / LOO / windows
python incremental_r2.py     # incremental R2 and partial F
python miss_typology.py      # missing-data typology and zero-fill sensitivity
python overlap_check.py      # mechanical overlap diagnostics
python figs.py --only 2      # figures (Chinese labels)
python figs_en.py --only 2   # figures (English labels, used in the manuscript)
```

Collection and parsing (`collect_w1.py`, `dump_text.sh`, `parse_fin.py`,
`parse_cashflow.py`, `extract_mgmt.py`, `finalize_contract4.py`) require network
access to CNINFO and the PDF text dumps; they document how the derived files
were produced rather than being needed to reproduce the estimates.

Wild cluster bootstrap uses 999 Rademacher draws with the null imposed; the seed
is fixed in `h2_robust.py`.

## License

Code: MIT (`LICENSE`). Data and documentation: CC BY 4.0 (`LICENSE-DATA`).

## Contact

Mengjie Hu, hmj@hist.edu.cn
