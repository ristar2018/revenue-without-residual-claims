# Coding manual for contract clauses

Unit of analysis: one disclosure entry for one counterparty and one subject in
one report. Agreement-level records aggregate entries that name the same
counterparty, subject and start date.

| Field | Definition | Values |
|---|---|---|
| `code` | Six-digit exchange code of the disclosing listed firm | 24 codes |
| `year` | Reporting year | 2015-2024 |
| `kind` | Reporting period | `A` annual, `H1` semi-annual |
| `channel` | Location of the clause | `附注表` notes table, `关联交易正文` related-party main text |
| `counterparty` | Principal granting the revenue right | government, scenic-area authority, state platform, other |
| `operator` | Entity receiving the fee | listed firm or subsidiary |
| `scope` | Subject of the arrangement | scenic area, hotel, travel agency, port, other asset, equity |
| `pricing` | Basis of the fee | fixed, cost-based, revenue-based, stepwise, progressive, not disclosed |
| `amount_yuan` | Fee recognised in the period | RMB |
| `start_date`, `end_date` | Term as disclosed | ISO dates |
| `pct_same_type` | Fee divided by the revenue of the same subject type | percent |
| `note` | Verbatim or condensed clause text | free text |

## Decision rules

1. A record is included only if the report states a fee amount or an explicit
   formula. Generic related-party disclosures without remuneration are excluded.
2. Where a clause is reported in several consecutive years, each year is a
   separate record; the agreement-level record is coded once.
3. Where the notes table and the related-party main text describe the same
   agreement, the entry is kept once and `channel` records where the
   economically relevant terms appear.
4. Fee-to-revenue ratios use the revenue of the same subject type as the
   denominator. Where the denominator is not reported, the ratio is left empty
   rather than imputed.
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
| `scope` (coded categories) | 经营管理权托管 | entrusted operating and management rights |
| | 其他资产托管 | other assets entrusted for management |
| | 股权托管 | entrusted equity |
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
