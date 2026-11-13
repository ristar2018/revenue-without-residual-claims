# Coding manual for contract clauses

Unit of analysis: one disclosure entry for one counterparty and one subject in
one report. Agreement-level records aggregate entries that name the same
counterparty, subject and start date.

*Panel A. Recorded fields (`data/contract_terms_v4.csv`, 99 rows).*

| Column | Definition | Values or form |
|---|---|---|
| `code` | Six-digit exchange code of the disclosing listed firm | 7 codes |
| `year` | Reporting year | 2016-2024 |
| `kind` | Report type | `A` annual (78 rows), `H1` semi-annual (21 rows) |
| `page` | Page of the entry in the layout text | integer |
| `rec` | Order of the entry within that page | 1-5 |
| `channel` | Location of the clause | `附注表` notes table (94), `关联交易正文` related-party main text (5) |
| `counterparty` | Principal granting the revenue right | firm name, verbatim as disclosed |
| `operator` | Entity receiving the fee | firm name, verbatim; the disclosing firm itself is kept as disclosed (`本公司`) |
| `scope` | Subject of the arrangement, standardised | `经营管理权托管` (33), `饭店` (26), `其他资产托管` (21), `旅行社` (13), `股权托管` (1), named scenic area (5) |
| `scope_raw` | Subject as worded in the report | verbatim |
| `start_date`, `end_date` | Term as disclosed | ISO dates; `end_date` empty when no end date is disclosed (41 of 99) |
| `pricing` | Basis of the fee | verbatim excerpt |
| `amount_yuan` | Fee recognised in the period | RMB, numeric |
| `nature` | Sector of the subject | `景区` (5), `酒店` (26), `旅行社` (13), `港口` (1), `其他` (54) |
| `pct_same_type` | Share of same-type transactions as stated in the report | percent; stated for 5 of 99 |
| `parse_flag` | Cleaning applied during extraction | free text |
| `note` | Coder note | free text |

*Panel B. Analytic codes read from the verbatim fields.* These are readings of
`pricing` and `end_date` rather than separate columns, so that the recorded text
and the code can always be checked against each other.

| Code | Read from | Rule | Values |
|---|---|---|---|
| Fee basis class | `pricing` | fixed sum; cost-based; revenue- or profit-sharing formula; stepwise or progressive schedule; not disclosed | 5 classes |
| Sharing | `pricing` | yes when the fee is a stated function of the counterparty's revenue or profit, no otherwise | yes / no |
| Termination disclosed | `end_date` | yes when an end date is stated, no otherwise | yes / no |
| Agreement | `counterparty` + `scope` + `start_date` | entries sharing all three are one agreement | 39 agreements from 99 entries |

## Decision rules

1. A record is included only if the report states a fee amount or an explicit
   formula. Generic related-party disclosures without remuneration are excluded.
2. Where a clause is reported in several consecutive years, each year is a
   separate record; the agreement-level record is coded once.
3. Where the notes table and the related-party main text describe the same
   agreement, the entry is kept once and `channel` records where the
   economically relevant terms appear.
4. Fee-to-revenue ratios divide the fee by the operating revenue of the same
   firm-year from `panel_annual_2015_2025_v2.csv`; they are not ratios to the
   revenue of the subject type. `pct_same_type` is a different quantity: the
   share of same-type transactions as stated in the report, available for five
   entries. A ratio is left empty when the denominator is missing rather than
   imputed.
5. Termination dates are recorded as disclosed. A clause without a stated end
   date is coded as open-ended, not as perpetual.
6. Coding was performed by reading the original reports. Ambiguous cases were
   resolved by re-reading the full description of the transaction. Coding was
   carried out by a single coder; no inter-coder statistic is reported.

## Chinese values in the data files

Text fields (`counterparty`, `operator`, `note`, `pricing`, and `scope` where the
subject is named) keep the wording of the disclosed report. Categorical fields
use a small controlled vocabulary, glossed below so that the CSVs can be read
without Chinese.

| Field | Value | English |
|---|---|---|
| `channel` | 附注表 | notes table (related-party section of the notes) |
| | 关联交易正文 | related-party main text (material-contracts narrative) |
| `nature` | 景区 / 酒店 / 旅行社 / 港口 / 其他 | scenic area / hotel / travel agency / port / other |
| `scope` (coded categories) | 经营管理权托管 | operating-rights entrustment |
| | 饭店 | hotel property |
| | 其他资产托管 | other asset entrustment |
| | 旅行社 | travel agency |
| | 股权托管 | equity entrustment |
| `class_main`, `top_class` | T1_制度性不适用 | institutionally not applicable: the standard was not yet in force |
| | T2_结构性零 | structural zero: the firm has no such item |
| | T3_未单独列示 | not presented separately on the face of the statement |
| | T4_采集缺口 | collection gap: a standard item that was not captured |
| | T5_整份报表缺失 | whole statement missing for that firm-year |
| `sample`, `scope` (rq1, rq2) | A级 / B级 / C级 | A level / B level / C level |
| | 全样本 | full sample |
| | 完整样本-…, 完整-… | complete-case sample (all five components present) |
| | 亏损年-… | loss firm-years |
| `spec` (`h2_results.csv`) | `A级|net_margin|负担流量` | A level, net margin, deduction-flow specification |
| | `…|承诺存量` | capital-commitment stock specification |
| | `…|周转口径` | turnover basis |
| | `…|去掉年份效应` | without year fixed effects |
| | `…|剔除2022年` | dropping 2022 |
| | `…|剔除300144/000430` | dropping the two leverage points |
| `test` (`h2_robust.csv`) | period_全期 | period split, whole window |
| `dimension` (`rq3_descriptive.csv`) | 覆盖 / 酬金·公司×性质 / 酬金占营收 / 期限 / 分成条款 / 曲江个案 | coverage / fee by firm and subject type / fee-to-revenue / term / sharing clauses / Qujiang case |
| `metric` (`rq3_descriptive.csv`) | 记录数 / 报告数 / 公司数 / 协议数 | record, report, firm and agreement counts |
| | 合计元 / 中位数元 | total and median, RMB |
| | 中位数% / 均值% / 最大% / 最小% / 中位年数 | median, mean, max, min (percent); median term in years |
| | 占合并营收% | share of consolidated operating revenue |
| `note` (`overlap_check.csv`) | 应为 0 | should be zero |
| | ≈1 表示恒等式，不能作解释性证据 | about 1 indicates an accounting identity, not explanatory evidence |
| `note` (`stats_manifest.csv`) | JPG 图片表页，文本化需 OCR + 人工复核 | image-only page; text extraction needs OCR and manual review |

The parsers match Chinese statement labels because the reports are Chinese:
`parse_fin.py`, `parse_cashflow.py`, `finalize_contract4.py`, `code_mgmt.py` and
`collect_w1.py` therefore contain Chinese regular expressions and keyword lists.
Those strings are patterns to be matched, not prose, and must not be translated.
