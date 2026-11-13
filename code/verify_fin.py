#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-check: consolidated statement figures parsed from the PDFs against the vendor datacenter
panel (two independent channels).

Criteria:
  - when revenue / net_profit are present on both sides, |diff| <= 1 yuan counts as agreement (the
    PDFs print to the cent, a few to the yuan)
  - disagreements are listed by (code,year) with both values and the difference
  - when a year's PDF reports 'total operating revenue', the vendor TOTAL_OPERATE_INCOME is the same
    concept, so the definitions agree

Usage: python code/verify_fin.py
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "data", "fin_panel.csv")
P = os.path.join(ROOT, "data", "panel_annual_2015_2025_v2.csv")
TOL = 1.0


def load(path, keys):
    out = {}
    with open(path, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            try:
                out[(r["code"], int(r["year"]))] = {k: float(r[k]) for k in keys if r.get(k) not in ("", None)}
            except ValueError:
                continue
    return out


def main():
    fin = load(F, ["revenue", "total_revenue", "net_profit", "np_parent"])
    pan = {}
    with open(P, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            pan[(r["code"], int(r["year"]))] = {
                "revenue": float(r["revenue"]) if r.get("revenue") else None,
                "net_profit": float(r["net_profit"]) if r.get("net_profit") else None,
            }
    rows, bad = [], []
    for key, fv in sorted(fin.items()):
        pv = pan.get(key)
        if not pv:
            continue
        rec = {"code": key[0], "year": key[1]}
        for k, kf in (("revenue", "total_revenue"), ("net_profit", "np_parent")):
            a = fv.get(kf) if fv.get(kf) is not None else fv.get(k)
            b = pv.get(k)
            rec[k + "_pdf"] = "" if a is None else f"{a:.2f}"
            rec[k + "_em"] = "" if b is None else f"{b:.2f}"
            if a is not None and b is not None:
                d = a - b
                rec[k + "_diff"] = f"{d:.2f}"
                if abs(d) > TOL:
                    bad.append(dict(rec))
                break_outer = False
        rows.append(rec)
    with open(os.path.join(ROOT, "data", "fin_vs_em.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["code", "year", "revenue_pdf", "revenue_em", "revenue_diff",
                                           "net_profit_pdf", "net_profit_em", "net_profit_diff"])
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    print(f"comparable cells {n}")
    for k in ("revenue", "net_profit"):
        ok = sum(1 for r in rows if r.get(k + "_diff") not in ("", None) and abs(float(r[k + "_diff"])) <= TOL)
        has = sum(1 for r in rows if r.get(k + "_diff") not in ("", None))
        print(f"  {k}: comparable on both sides {has}, agree {ok}, disagree {has - ok}")
    if bad:
        print("\nfirst 15 disagreements:")
        for b in bad[:15]:
            print(f"  {b['code']} {b['year']} rev {b.get('revenue_pdf')} vs {b.get('revenue_em')} "
                  f"| np {b.get('net_profit_pdf')} vs {b.get('net_profit_em')}")


if __name__ == "__main__":
    main()
