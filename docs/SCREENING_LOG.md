# Retrieval and screening record

| Stage | Records | Basis |
|---|---|---|
| Filings indexed | 43,906 | CNINFO announcement index, 24 firms, 1993-2026 |
| Reports retrieved | 311 | 226 annual and 85 semi-annual reports, 2015-2024 |
| Documents converted to layout text | 311 | page-level text with page marks |
| Page-level keyword hits | 1,180 | entrusted management, management fee, sharing, contracting, 2020-2024 |
| Clause entries extracted | 99 | 94 notes-table entries, 5 related-party main-text entries |
| Firms and reports | 7 firms, 32 reports | disclosure units |
| Agreement-level records | 39 | same counterparty, subject and start date |
| Entries with a fee-to-revenue ratio | 78 | annual entries with both amounts |

Inclusion required a stated fee amount or an explicit formula, an identifiable
counterparty and a subject located in a tourism operation. Generic related-party
disclosures without remuneration, brand licensing without revenue rights and
pure service contracts without an operating right were excluded.

The retrieval is reproducible from `code/collect_w1.py` (index and downloads),
`code/dump_text.sh` (layout text) and `code/extract_mgmt.py` (keyword hits).
`data/pdf_manifest.csv` lists the documents; `data/mgmt_summary.csv` reports the
keyword hits by firm and year.
