# -*- coding: utf-8 -*-
"""Missing-value typology and sensitivity to missing-data handling (reviewer point 4: how are
missing values handled?).

Part 1: group the 28 fields of data/fin_miss.csv into five classes by the nature of the missingness
and write the typology table.
Part 2: apply defensible filling rules (zero only for items that did not exist institutionally and
for structural zeros), re-estimate the H2 main test and compare with the baseline (n=115), to see
whether the conclusion is driven by the treatment of missing data.

Five classes (criteria below, all verifiable against the data; the labels are kept in Chinese
because they are values in data/miss_typology.csv):
  T1 institutionally not applicable  not required by the standards before 2019: rou / lease_liab
                   (CAS 21 revision, effective 2019); credit_imp (new financial instruments standard,
                   effective 2019; the line 'credit impairment loss' did not exist before)
  T2 structural zero   the statement has no such line because there is no such item: bond (no bonds),
                   gw (no goodwill), asset_imp / credit_imp (no impairment line in the income statement)
  T3 not presented separately   reported in a combined line on the face of the statement, to be taken
                   from the notes or supplementary information: dep_fa (depreciation sits in the
                   cash-flow supplementary schedule), cash_staff (cash paid to employees), staff_pay,
                   ip / cip / ia (intangibles reported in combined lines)
  T4 collection gap   a standard statement item that should have been captured but was not:
                   revenue / total_revenue / net_profit / np_parent / ar / other_ar / inventory /
                   fa / int_exp / am_ia / am_lt / fin_exp / int_inc
  T5 whole statement missing   the entire statement of a single year was not obtained:
                   firm-years with n_miss >= 13

Outputs: data/miss_typology.csv (field level), data/miss_rowclass.csv (firm-year level),
         data/h2_miss_sensitivity.csv (re-estimation results)
Exit code: 0 normal; 1 missing input
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"

T1_PRE2019 = {"rou", "lease_liab", "credit_imp"}
T2_ZERO = {"bond", "gw", "asset_imp"}
T3_MERGED = {"dep_fa", "cash_staff", "staff_pay", "ip", "cip", "ia"}
T4_GAP = {"revenue", "total_revenue", "net_profit", "np_parent", "ar", "other_ar",
          "inventory", "fa", "int_exp", "am_ia", "am_lt", "fin_exp", "int_inc"}
WHOLE_REPORT_NMISS = 13


def cls_of(field: str, year: str) -> str:
    if field in T1_PRE2019:
        return "T1_制度性不适用" if year < "2019" else "T3_未单独列示"
    if field in T2_ZERO:
        return "T2_结构性零"
    if field in T3_MERGED:
        return "T3_未单独列示"
    if field in T4_GAP:
        return "T4_采集缺口"
    return "T4_采集缺口"


def fields(r) -> list[str]:
    return [x.strip() for x in r["miss"].replace("|", ";").split(";") if x.strip()]


def part1() -> tuple[list[dict], list[dict]]:
    rows = list(csv.DictReader(open(D / "fin_miss.csv", encoding="utf-8-sig")))
    n = len(rows)
    fld = defaultdict(lambda: Counter())
    for r in rows:
        for f in set(fields(r)):
            fld[f][cls_of(f, r["year"])] += 1
    field_rows = []
    for f in sorted(fld, key=lambda x: -sum(fld[x].values())):
        cc = fld[f]
        tot = sum(cc.values())
        field_rows.append(dict(field=f, n_missing=tot, pct=round(tot / n * 100, 1),
                               pre2019=sum(1 for r in rows if r["year"] < "2019" and f in fields(r)),
                               post2019=sum(1 for r in rows if r["year"] >= "2019" and f in fields(r)),
                               class_main=cc.most_common(1)[0][0],
                               class_mix=";".join(f"{k}:{v}" for k, v in cc.most_common())))

    row_rows = []
    for r in rows:
        fs = fields(r)
        cls = Counter(cls_of(f, r["year"]) for f in fs)
        if int(r["n_miss"]) >= WHOLE_REPORT_NMISS:
            top = "T5_整份报表缺失"
        elif not fs:
            top = "完整"
        else:
            top = cls.most_common(1)[0][0]
        row_rows.append(dict(code=r["code"], year=r["year"], n_miss=r["n_miss"],
                             top_class=top, detail=";".join(sorted(fs))))
    return field_rows, row_rows


def load(name):
    return list(csv.DictReader(open(D / name, encoding="utf-8-sig")))


def fnum(x):
    try:
        s = (x or "").strip()
        return float(s) if s else None
    except ValueError:
        return None


TIER = {
    "600054": "A", "000888": "A", "002033": "A", "603199": "A", "603099": "A",
    "603136": "A", "000430": "A", "600593": "A", "000978": "A", "600749": "A",
    "002159": "A", "300859": "A", "300144": "A", "600706": "A", "600576": "A",
    "002059": "A", "002627": "A",
}


def build(impute: bool) -> list[dict]:
    """Rebuild net_margin / da_int / int_burden / impair / capex_int.
    With impute=True, T1 and T2 fields are treated as zero (institutionally absent / no such item)."""
    fin = load("fin_panel.csv")
    cf = {(r["code"], r["year"], r["kind"]): r for r in load("cashflow_panel.csv")}
    out = []
    for r in fin:
        code, year = r["code"], r["year"]
        rev = fnum(r["revenue"]) or fnum(r["total_revenue"])
        if not rev:
            continue
        c = cf.get((code, year, "A"), {})
        np_ = fnum(r["np_parent"])
        if np_ is None:
            np_ = fnum(r["net_profit"])

        def g(k, src=r):
            v = fnum(src.get(k))
            if v is None and impute and k in T2_ZERO:
                return 0.0
            if v is None and impute and k == "credit_imp" and year < "2019":
                return 0.0
            return v

        dep, am_ia, am_lt = fnum(c.get("dep_fa")), fnum(c.get("am_ia_cf")), fnum(c.get("am_lt_cf"))
        parts = [x for x in (dep, am_ia, am_lt) if x is not None]
        da = sum(parts) if parts else None

        a_imp, c_imp = g("asset_imp"), g("credit_imp")
        if a_imp is None and c_imp is None:
            imp = None
        else:
            imp = abs(a_imp or 0.0) + abs(c_imp or 0.0)

        int_exp = g("int_exp")
        capex = fnum(c.get("capex"))
        out.append(dict(
            code=code, year=year, tier=TIER.get(code, "?"), revenue=rev,
            net_margin=None if np_ is None else np_ / rev,
            da_int=None if da is None else da / rev,
            int_burden=None if int_exp is None else abs(int_exp) / rev,
            impair=None if imp is None else imp / rev,
            capex_int=None if capex is None else abs(capex) / rev,
        ))
    return out


def run(rows, indep, winsor=5.0):
    sub = [r for r in rows if r["tier"] == "A"
           and r["net_margin"] is not None and all(r[k] is not None for k in indep)]
    if len(sub) < 30:
        return None
    y = np.clip(np.array([r["net_margin"] for r in sub], float), -winsor, winsor)
    X = np.clip(np.array([[r[k] for k in indep] for r in sub], float), -winsor, winsor)
    firms = sorted({r["code"] for r in sub})
    years = sorted({r["year"] for r in sub})
    Dm = np.zeros((len(sub), len(firms) - 1 + len(years) - 1))
    for i, r in enumerate(sub):
        fi, yi = firms.index(r["code"]), years.index(r["year"])
        if fi > 0:
            Dm[i, fi - 1] = 1.0
        if yi > 0:
            Dm[i, len(firms) - 1 + yi - 1] = 1.0
    Xf = sm.add_constant(np.hstack([X, Dm]))
    fit = sm.OLS(y, Xf).fit(cov_type="cluster", cov_kwds={"groups": [r["code"] for r in sub]})
    res = dict(n=len(sub), firms=len(firms), r2=round(float(fit.rsquared), 4))
    for j, k in enumerate(indep):
        res[k] = round(float(fit.params[1 + j]), 4)
        res[k + "_se"] = round(float(fit.bse[1 + j]), 4)
        res[k + "_p"] = round(float(fit.pvalues[1 + j]), 4)
    return res


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for p in ("fin_miss.csv", "fin_panel.csv", "cashflow_panel.csv"):
        if not (D / p).exists():
            print("missing input:", p)
            return 1

    field_rows, row_rows = part1()
    pd.DataFrame(field_rows).to_csv(D / "miss_typology.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(row_rows).to_csv(D / "miss_rowclass.csv", index=False, encoding="utf-8-sig")

    print("[field-level typology] 225 firm-years")
    print(f"{'field':14s}{'missing':>8s}{'share':>7s}{'pre-2019':>9s}{'post-2019':>10s}  main class")
    for r in field_rows:
        print(f"{r['field']:14s}{r['n_missing']:5d}{r['pct']:6.1f}%{r['pre2019']:7d}{r['post2019']:8d}  {r['class_main']}")

    print("\n[firm-year-level typology]")
    cc = Counter(r["top_class"] for r in row_rows)
    for k, v in cc.most_common():
        print(f"  {k:16s}{v:4d}  ({v / len(row_rows) * 100:.1f}%)")

    MAIN = ["da_int", "int_burden", "impair"]
    base = run(build(False), MAIN)
    imp = run(build(True), MAIN)
    print("\n[H2 main test: sensitivity to the treatment of missing data]  net_margin ~ da_int + int_burden + impair")
    for tag, r in (("基线（缺失即剔除）", base), ("制度性/结构性补 0", imp)):
        if not r:
            print(f"  {tag}: sample too small")
            continue
        print(f"  {tag}: n={r['n']} firms={r['firms']} R2={r['r2']}")
        for k in MAIN:
            print(f"     {k:12s} {r[k]:+8.4f}  se={r[k + '_se']:7.4f}  p={r[k + '_p']:.4f}")

    out = []
    for tag, r in (("baseline_drop_missing", base), ("impute_T1_T2_zero", imp)):
        if r:
            out.append(dict(spec=tag, **r))
    if out:
        pd.DataFrame(out).to_csv(D / "h2_miss_sensitivity.csv", index=False, encoding="utf-8-sig")
        print("\nwrote data/miss_typology.csv, data/miss_rowclass.csv, data/h2_miss_sensitivity.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
