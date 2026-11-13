# -*- coding: utf-8 -*-
"""
RQ2 decomposition of the decoupling chain (accounting-identity basis, descriptive only, no regressions)

Criteria (fixed, do not change):
  1. Everything is scaled by operating revenue (this batch has no reliable total-asset series).
  2. Five-part identity (holds for every firm-year, tolerance 1e-9):
        net_margin = adj_margin - minority - int_burden - impair - da_int
     where
        net_margin  = net profit attributable to parent / operating revenue   (= net_margin in h2_panel)
        adj_margin  = (net profit + |interest expense| + |asset impairment| + |credit impairment|
                      + D&A) / operating revenue
                      -- operating margin before capital charges, i.e. the 'unconverted / operating
                      layer' residual of RQ2
        minority    = (net profit - net profit attributable to parent) / operating revenue
                      -- claims of outside (minority) holders
        int_burden  = |interest expense| / operating revenue      -- financing squeeze
        impair      = (|asset impairment| + |credit impairment|) / operating revenue
                      -- impairment squeeze
        da_int      = D&A / operating revenue                     -- depreciation and amortisation
                      (mind the denominator effect; not a burden intensity)
  3. D&A is taken from the cash-flow supplementary schedule (cashflow_panel) where available,
     otherwise from am_ia + am_lt in the income statement.
  4. When minority is negative (minority holders absorbing losses) the sign is kept as reported,
     never taken in absolute value.
  5. No winsorisation on output: this is an identity decomposition and trimming would break the
     additivity.
"""
import os
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)

TOL = 1e-9
BRANCHES = ["minority", "int_burden", "impair", "da_int"]


def load():
    h2 = pd.read_csv(D("data", "h2_panel.csv"), dtype={"code": str})
    fin = pd.read_csv(D("data", "fin_panel.csv"), dtype={"code": str})
    cf = pd.read_csv(D("data", "cashflow_panel.csv"), dtype={"code": str})
    # cashflow_panel includes interim reports, so the same (code,year) appears twice; this decomposition uses annual reports only, otherwise the merge doubles
    cf = cf[cf["kind"] == "A"].drop_duplicates(["code", "year"], keep="last")
    m = h2.merge(
        fin[["code", "year", "net_profit", "np_parent", "int_exp", "asset_imp",
             "credit_imp", "am_ia", "am_lt", "revenue"]].rename(columns={"revenue": "rev_fin"}),
        on=["code", "year"], how="left")
    m = m.merge(cf[["code", "year", "dep_fa", "am_ia_cf", "am_lt_cf"]],
                on=["code", "year"], how="left")
    return m


def build(m):
    rows = []
    for _, r in m.iterrows():
        rev = r["revenue"]
        if not np.isfinite(rev) or rev <= 0:
            continue
        np_tot = r["net_profit"]
        np_par = r["np_parent"]
        if not np.isfinite(np_tot):
            continue
        # Fall back to net profit when the parent-attributable figure is missing (flagged)
        flag = []
        if not np.isfinite(np_par):
            np_par = np_tot
            flag.append("np_parent_missing")
        int_amt = abs(r["int_exp"]) if np.isfinite(r["int_exp"]) else np.nan
        imp_amt = 0.0
        got_imp = False
        for c in ("asset_imp", "credit_imp"):
            if np.isfinite(r[c]):
                imp_amt += abs(r[c])
                got_imp = True
        if not got_imp:
            imp_amt = np.nan
        # Depreciation and amortisation: cash-flow statement first
        da = np.nan
        if np.isfinite(r.get("dep_fa", np.nan)):
            da = abs(r["dep_fa"])
            if np.isfinite(r.get("am_ia_cf", np.nan)):
                da += abs(r["am_ia_cf"])
            if np.isfinite(r.get("am_lt_cf", np.nan)):
                da += abs(r["am_lt_cf"])
            flag.append("da_from_cf")
        elif np.isfinite(r.get("am_ia", np.nan)):
            da = abs(r["am_ia"]) + (abs(r["am_lt"]) if np.isfinite(r.get("am_lt", np.nan)) else 0.0)
            flag.append("da_from_is")
        if not np.isfinite(da):
            da = 0.0
            flag.append("da_missing")
        if not np.isfinite(int_amt):
            int_amt = 0.0
            flag.append("int_missing")
        if not np.isfinite(imp_amt):
            imp_amt = 0.0
            flag.append("impair_missing")
        adj = (np_tot + int_amt + imp_amt + da) / rev
        rec = dict(code=r["code"], year=int(r["year"]), tier=r["tier"],
                   revenue=rev, net_margin=np_par / rev,
                   adj_margin=adj,
                   minority=(np_tot - np_par) / rev,
                   int_burden=int_amt / rev,
                   impair=imp_amt / rev,
                   da_int=da / rev,
                   flag=";".join(flag))
        rec["check"] = (rec["adj_margin"] - rec["minority"] - rec["int_burden"]
                        - rec["impair"] - rec["da_int"] - rec["net_margin"])
        # When one component is missing it is set to 0; the identity still closes but adj absorbs it -> it must be flagged, and the summary must be stratified
        rec["complete"] = not any(f in flag for f in
                                  ("int_missing", "impair_missing", "da_missing",
                                   "np_parent_missing"))
        rows.append(rec)
    d = pd.DataFrame(rows)
    bad = d[d["check"].abs() > 1e-9]
    if len(bad):
        raise SystemExit("identity does not close for %d rows:\n%s" % (len(bad), bad.head().to_string()))
    return d


def pool(d, sel, label):
    x = d[sel]
    out = dict(scope=label, n=len(x),
               net_margin=x["net_margin"].mean(),
               adj_margin=x["adj_margin"].mean(),
               minority=x["minority"].mean(),
               int_burden=x["int_burden"].mean(),
               impair=x["impair"].mean(),
               da_int=x["da_int"].mean())
    out["gap"] = out["net_margin"] - out["adj_margin"]
    return out


def main():
    d = build(load())
    d.to_csv(D("data", "rq2_decomp.csv"), index=False, encoding="utf-8-sig")

    # 1 pooled: tier x full period / pre-pandemic / post-pandemic
    rows = [pool(d, (d["tier"] == t) if t != "ALL" else d["code"].notna(),
                 "全样本" if t == "ALL" else "%s 级" % t)
            for t in ("A", "B", "C", "ALL")]
    rows.append(pool(d, (d["year"] <= 2019), "全样本 2015–2019"))
    rows.append(pool(d, (d["year"] <= 2019) & (d["tier"] == "A"), "A 级 2015–2019"))
    rows.append(pool(d, (d["year"] >= 2020) & (d["tier"] == "A"), "A 级 2020–2024"))
    # Complete cases (all five components present) are the main criterion; rows with missing components serve as robustness
    c = d["complete"]
    rows.append(pool(d, c, "完整样本-全部"))
    rows.append(pool(d, c & (d["tier"] == "A"), "完整样本-A 级"))
    rows.append(pool(d, c & (d["tier"] == "A") & (d["year"] <= 2019), "完整-A 级 2015–2019"))
    rows.append(pool(d, c & (d["tier"] == "A") & (d["year"] >= 2020), "完整-A 级 2020–2024"))
    s = pd.DataFrame(rows)
    s.to_csv(D("data", "rq2_summary.csv"), index=False, encoding="utf-8-sig")
    print("== pooled decomposition (profit margins, %) ==")
    show = s.copy()
    for c in ["net_margin", "adj_margin", "minority", "int_burden", "impair", "da_int", "gap"]:
        show[c] = (show[c] * 100).round(2)
    print(show.to_string(index=False))

    # 2 by firm (17 A-level firms, full-period means)
    a = d[d["tier"] == "A"]
    g = a.groupby("code").agg(n=("year", "size"),
                              net_margin=("net_margin", "mean"),
                              adj_margin=("adj_margin", "mean"),
                              minority=("minority", "mean"),
                              int_burden=("int_burden", "mean"),
                              impair=("impair", "mean"),
                              da_int=("da_int", "mean")).reset_index()
    g["gap"] = g["net_margin"] - g["adj_margin"]
    g = g.sort_values("net_margin")
    g.to_csv(D("data", "rq2_by_firm.csv"), index=False, encoding="utf-8-sig")
    print("\n== A level by firm (means, %) ==")
    gs = g.copy()
    for c in ["net_margin", "adj_margin", "minority", "int_burden", "impair", "da_int", "gap"]:
        gs[c] = (gs[c] * 100).round(2)
    print(gs.to_string(index=False))

    # 3 loss years: who creates the shortfall (summed in percentage points, not as a share, because small shortfalls blow the ratio up)
    loss = d[(d["net_margin"] < 0)].copy()
    loss["gross_ded"] = loss["int_burden"] + loss["impair"] + loss["da_int"]
    print("\n== loss firm-years %d (A level %d): mean contribution of each component (percentage points) =="
          % (len(loss), (loss["tier"] == "A").sum()))
    hdr = "  %-14s %8s %8s %8s %8s %8s"
    print(hdr % ("scope", "net", "adj", "minority", "int", "impair"))
    for lbl, sel in (("亏损年-全部", loss["code"].notna()),
                     ("亏损年-A级", loss["tier"] == "A")):
        x = loss[sel]
        print(hdr % (lbl, "%.2f" % (x["net_margin"].mean() * 100),
                     "%.2f" % (x["adj_margin"].mean() * 100),
                     "%.2f" % (x["minority"].mean() * 100),
                     "%.2f" % (x["int_burden"].mean() * 100),
                     "%.2f" % (x["impair"].mean() * 100)))
        print("    da=%.2f  gross deduction=%.2f  share with a negative operating layer=%.1f%%"
              % (x["da_int"].mean() * 100, x["gross_ded"].mean() * 100,
                 (x["adj_margin"] < 0).mean() * 100))
    # relative shares inside the gross deduction (the denominator is always positive, so the ratio is meaningful)
    tot = loss["gross_ded"].sum()
    print("  structure of the gross deduction (all loss years pooled): D&A %.1f%% / impairment %.1f%% / interest %.1f%%"
          % (loss["da_int"].sum() / tot * 100, loss["impair"].sum() / tot * 100,
             loss["int_burden"].sum() / tot * 100))
    print("  median net margin %.2f%%  median adj %.2f%%"
          % (loss["net_margin"].median() * 100, loss["adj_margin"].median() * 100))
    loss.to_csv(D("data", "rq2_loss_years.csv"), index=False, encoding="utf-8-sig")

    # 4 the largest deduction in each firm-year
    ded = d[["code", "year", "tier"] + BRANCHES].copy()
    ded["top"] = ded[BRANCHES].idxmax(axis=1)
    print("\n== most frequent largest deduction (full sample %d) ==" % len(ded))
    print(ded["top"].value_counts().to_string())
    print("\n== most frequent largest deduction (A level) ==")
    print(ded[ded["tier"] == "A"]["top"].value_counts().to_string())
    ded[["code", "year", "tier", "top"] + BRANCHES].to_csv(
        D("data", "rq2_top_sink.csv"), index=False, encoding="utf-8-sig")

    print("\n[done] rq2_decomp %d rows / summary %d rows / by_firm %d rows / loss %d rows"
          % (len(d), len(s), len(g), len(loss)))


if __name__ == "__main__":
    main()
