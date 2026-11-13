## 3. Data and measurement

### 3.1 Sample and evidence map

The financial panel comprises 24 A-share listed tourism firms observed over 2015–2025, representing 264 firm-years (Appendix Table A1). Revenue and profit growth are calculable for 240 firm-years. The primary sources are public annual and semi-annual reports filed by the listed firms. Financial items and contract disclosures were hand-collected and cross-checked against the reported financial statements. Because 2025 is a partial-disclosure year, its observations are not treated as a complete annual reporting cohort. Their inclusion in the descriptive panel does not establish comparability with full-year observations.

Firms are classified according to disclosure completeness and statement comparability, not financial performance. The A-level group contains 17 firms with continuous disclosure and comparable statement items, comprising 187 firm-years, of which 170 have calculable growth. The B-level group contains 4 firms and 44 firm-years; the C-level group contains 3 firms and 33 firm-years. Both groups remain in the full-sample description but are not merged into the A-level statistics. This separation preserves the distinction between coverage of listed tourism firms and the narrower evidence supported by comparable accounting items.

Accounting data for the decomposition cover 2015–2024 and contain 225 firm-years. All five components are available for 165 observations. The remaining 60 have at least one missing component recorded as zero and flagged; Appendix Table A6 classifies those missing items by origin and reports the sensitivity of the estimates to zero substitution. The main decomposition uses the complete cases. Zero substitution in the flagged records is a computational convention, not evidence that the relevant firm incurred no interest, impairment, or depreciation and amortisation burden. These observations must remain distinguishable from records containing reported zeros.

A-level observations form the regression frame: 170 firm-years over 2015–2024 (17 firms × 10 years). Of these, 115 enter the estimation. Fourteen firm-years lack a usable revenue denominator in the financial-statement panel: 13 are absent from the panel (eight from 2015, when annual-report coverage is incomplete, and five belonging to firms listed after 2015), and one (002627 in 2017) reports no revenue. Of the 156 firm-years with a revenue denominator, 41 lack at least one regressor: 24 lack interest expense, 20 lack both impairment items, and three lack both interest expense and impairment items. The 115 observations are therefore a listwise-deletion sample rather than a complete A-level panel. Growth comparisons use a different window. A within-firm growth rate requires two adjacent years, so the 2015 observations cannot supply one and the growth frame runs from 2016 to 2025: 170 A-level firm-years (17 firms × 10 years) and 240 in the full panel. The growth frame and the regression frame therefore coincide in size but not in coverage. Three frames are in use — 156 firm-years with a revenue denominator (the parent of the regression sample), 165 complete decomposition cases, and 170 growth observations — and each is defined by a different availability requirement; none is a successive screening stage of another.

Divergence is classified by the signs of the two level changes, revenue and parent-attributable net profit, between adjacent years of the same firm. A percentage growth rate is reported alongside as a descriptive companion, but it is not used for classification: a rate computed on a negative prior-year value reverses sign, so a narrowing loss would enter as falling profit and a widening loss as rising profit. Section 4.1 reports both criteria and the number of cases affected.

Three analytical questions organise the evidence map. Table 1 describes the coverage and revenue–profit growth patterns of the 24-firm panel, with 264 firm-years and 240 calculable growth observations, while keeping A-level statistics separate. Table 2 locates the accounting components of the margin gap using the 165 complete decomposition cases within the 225-observation frame. Table 5 reports within-firm associations using the 115 regression observations from 17 firms. Contract evidence addresses how disclosed agreements allocate fees and obligations: it comprises 99 clauses from 32 reports issued by 7 firms, including 39 agreement-level clauses. This is a separate disclosure sample, not an additional firm-year panel.

### 3.2 The five-component identity

The decomposition expresses net margin attributable to the parent as an operating layer less four accounting deductions. For firm \(i\) in year \(t\), let \(R\), \(P\), \(M\), \(I\), \(L\) and \(D\) denote operating revenue, net profit attributable to the parent, minority interest in profit or loss, interest expense, impairment loss, and depreciation and amortisation, each observed for that firm and year. The identity is

\[
\frac{P_{it}}{R_{it}}
=
\frac{P_{it}+M_{it}+I_{it}+L_{it}+D_{it}}{R_{it}}
-
\frac{M_{it}}{R_{it}}
-
\frac{I_{it}}{R_{it}}
-
\frac{L_{it}}{R_{it}}
-
\frac{D_{it}}{R_{it}}.
\]

Its operating layer is \((P_{it}+M_{it}+I_{it}+L_{it}+D_{it})/R_{it}\). Minority interest is \(M_{it}/R_{it}\); interest burden is \(I_{it}/R_{it}\); impairment burden is \(L_{it}/R_{it}\); and depreciation and amortisation intensity is \(D_{it}/R_{it}\). The common revenue denominator places the components on the same scale and permits an exact reconciliation to the margin attributable to shareholders of the parent.

It is a constructed accounting bridge after tax but before the four specified deductions. It is not a reported operating-profit subtotal and should not be interpreted as EBITDA, because income tax is not added back. Its purpose is to distinguish the margin attributable to the parent from the amounts associated with minority interests, financing, impairment, and depreciation and amortisation. These labels organise the reported accounting amounts; they do not establish which contractual or operational decisions generated them.

Depreciation and amortisation are taken first from the supplementary schedule of the cash-flow statement. Where that source is unavailable, the fallback uses the income-statement items for intangible-asset amortisation and long-term-asset depreciation. The fallback is an alternative source, not an additional amount to be added to the supplementary schedule. The source distinction matters because statement presentation can affect item comparability even when the identity reconciles.

Closure is checked row by row to a tolerance of \(10^{-9}\). Closure demonstrates arithmetic consistency, not causal attribution or completeness of disclosure. In particular, a flagged row can reconcile after zero substitution without providing a complete economic decomposition. The identity locates the accounting gap; it does not explain why its components changed.

A descriptive adjusted margin adds interest expense, impairment loss, and depreciation and amortisation back to net profit attributable to the parent, with the sum divided by operating revenue. It does not add back minority interest or income tax and is not EBITDA. Neither the identity nor its component values are winsorised. Transforming the components independently would compromise their reconciliation; winsorisation is confined to the regression variables.

### 3.3 Contract data and coding

The contract corpus contains 99 clauses extracted from 32 reports issued by 7 firms over 2016–2024: 25 annual reports and 7 semi-annual reports. Of these clauses, 39 are agreement-level. Two disclosure channels are distinguished. The notes table on entrusted management and contracting supplies 94 clauses, while the main-text section on other material contracts supplies 5. The notes table contains no scenic-area clauses; all five scenic-area clauses occur in the main text. A search confined to the notes table would therefore omit the scenic-area evidence present in this corpus.

Each clause is coded for firm, year, report type, disclosure channel, counterparty, subject, fee basis, fee amount, fee-to-revenue ratio, sharing schedule, term, termination, and collection status; Appendix Table A3 reports the coding manual, Appendix Table A4 the search and screening yield, and Appendix Table A5 the clause inventory by firm. Subject categories are scenic area, hotel, travel agency, port, and other. Fee bases are fixed, cost-based, revenue-sharing, and stepwise. Clauses were read in the original reports. Ambiguities were addressed by re-reading the full contract description and the surrounding note rather than interpreting an isolated table entry. No inter-coder reliability statistic is available.

Within the notes table, 54 clauses concern other subjects, including 50 in annual reports; 26 concern hotels, including 18 in annual reports; and 13 concern travel agencies, including 9 in annual reports. The remaining clause concerns a port. These are clause frequencies, not counts of distinct firms, assets, or economically independent agreements. The 39 agreement-level clauses must likewise be distinguished from the full set of disclosure entries.

A fee-to-revenue ratio is available for 78 clauses. Its median is 0.0101%, its mean is 0.0343%, and its maximum is 0.8646%. These statistics describe the available ratios only; unavailable ratios are not assigned zero. Because the supplied coding specification does not identify a uniform revenue denominator or annualisation convention, these ratios should not be interpreted as a fully standardised measure of firm-level revenue exposure. Replication of their construction requires the denominator and reporting period associated with each source entry.

Term is determinable for 53 clauses. Of these, 48 have terms of five years or less; the median is 2.92 years. Five exceed five years, and the maximum is 10 years. A termination date is absent for 41 clauses. Determinable term and disclosed termination date are separate coding fields, so their availability counts need not coincide. Only seven records, covering four formula types, contain a sharing formula. The disclosed arrangements include stepwise schedules, in which the applicable fee or share changes across specified bands, and progressive schedules, in which successive portions are subject to different rates. Detailed thresholds and rates are reserved for the Results section.

Coverage supports description of disclosed contractual arrangements, not claims of representativeness. It covers seven firms and is subject to disclosure selection, possible under-reporting in the notes table, and differences between disclosure channels. Its observations are clauses, including agreement-level records, rather than firm-level measures of contractual exposure. Clause frequencies therefore cannot establish the prevalence or financial importance of particular arrangements across listed tourism firms.

### 3.4 Variables and estimation

Two dependent variables are estimated: net margin attributable to the parent and operating cash-flow margin. Net margin is net profit attributable to the parent divided by operating revenue. Operating cash-flow margin is net cash flow from operating activities divided by operating revenue. The difference between the two is used as a descriptive statistic in Section 4.4 only, and is not an estimated outcome: it is constructed from the same four deduction lines that enter the regressors, so regressing it on them would partly reproduce the accounting identity. A positive difference indicates that the reported profit margin exceeds the operating cash-flow margin; it does not, by itself, identify earnings management or poor collection. Earnings-quality research cautions that reported profit reflects accrual choices as well as underlying performance, so a divergence between the two margins cannot be read as a direct measure of either (Dechow et al., 2010). The two margins differ in accounting basis, and their numerator scopes are not necessarily equivalent.

Principal independent variables are depreciation and amortisation intensity, interest burden, and impairment burden, as defined in the identity. Auxiliary ratios are interest-bearing debt divided by operating revenue, long-term assets divided by operating revenue, and asset turnover, defined as operating revenue divided by long-term assets. Firm size, leverage, revenue growth, and state ownership are also specified as auxiliary variables. The supplied measurement information does not establish the size transformation, leverage definition, ownership coding rule, detailed debt and asset coverage, or the treatment of problematic growth bases. These definitions require documentation in the replication materials; assigning conventional definitions would introduce unsupported assumptions.

Estimation takes the form

\[
Y_{it}=\alpha_i+\lambda_t+\boldsymbol{\beta}'\mathbf{X}_{it}
+\boldsymbol{\gamma}'\mathbf{Z}_{it}+\varepsilon_{it},
\]

where \(Y_{it}\) is one of the three dependent variables, \(\mathbf{X}_{it}\) contains the principal accounting burdens, and \(\mathbf{Z}_{it}\) denotes the auxiliary variables included in a specification. Firm fixed effects, \(\alpha_i\), absorb time-invariant firm characteristics, while year fixed effects, \(\lambda_t\), absorb common year-specific variation. A characteristic that does not vary within a firm cannot receive a separately identified coefficient under firm fixed effects.

We treat the estimates as descriptive within-firm associations, not causal effects. This distinction is particularly important because the accounting burdens enter the net-margin identity itself. An association between a burden and net margin can reflect that accounting relationship alongside changes in operations, financing, or asset valuation. Fixed effects do not resolve simultaneity or time-varying omitted factors.

Standard errors are clustered at the firm level, allowing within-firm dependence across observations (Petersen, 2009). Clustering should be related to the dependence and sampling structure rather than applied mechanically (Abadie et al., 2023). There are 17 firm clusters, so reported p-values are treated as descriptive evidence rather than definitive inference. Bootstrap-based methods address related inference concerns (Cameron et al., 2008), but no bootstrap results are asserted here.

Regression variables are winsorised at ±5% under a common rule; this treatment does not extend to the accounting identity. Exact replication also requires documentation of the population used to calculate the winsorisation thresholds. Missing regression values are handled through listwise deletion, without imputation. The reported reduction is from 170 to 115 observations. The attrition record is set out in Section 3.1 so that the estimation sample is not presented without its construction.