#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collapse contract_terms_v4.csv into two analysis tables.

A) Agreement level: one row per agreement (key = counterparty + start date + subject matter),
   with first year, last year, the annual fee series (key=year:amount) and a flag for
   disclosure across years.
B) Firm-year level: total entrusted-management fee recognised by each firm and year
   (the raw dependent variable for RQ3).

All amounts in yuan. Amounts are 'recognised this period', and interim reports cover half a
year only, so table B carries a `kind` column; interim and annual amounts must never be added.
Usage: python code/contract_summary.py [terms.csv]
"""
import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = (sys.argv[1] if len(sys.argv) > 1
       else os.path.join(ROOT, "data", "contract_terms_v4.csv"))
if not os.path.isabs(SRC):
    SRC = os.path.join(ROOT, SRC)


def norm(s):
    return "".join(s.split())


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    proto = {}
    for r in rows:
        cp = norm(r["counterparty"])
        key = (r["code"], cp[:14], r["start_date"][:7], r["scope"][:6])
        p = proto.setdefault(key, {
            "code": r["code"], "counterparty": cp, "scope": r["scope"],
            "start_date": r["start_date"], "end_date": r["end_date"],
            "nature": r["nature"], "years": [], "fees": [],
        })
        if not p["end_date"] and r["end_date"]:
            p["end_date"] = r["end_date"]
        p["years"].append(r["year"] + r["kind"])
        if r["amount_yuan"]:
            p["fees"].append((r["year"] + r["kind"], float(r["amount_yuan"])))

    out_a = []
    for (_c, _cp, _s, _sc), p in sorted(proto.items()):
        fees = sorted(p["fees"])
        out_a.append({
            "code": p["code"], "counterparty": p["counterparty"],
            "scope": p["scope"], "nature": p["nature"],
            "start_date": p["start_date"], "end_date": p["end_date"],
            "n_reports": len(set(p["years"])),
            "first_report": min(p["years"]), "last_report": max(p["years"]),
            "fee_series": ";".join(f"{k}={v:.2f}" for k, v in fees),
            "fee_mean": round(sum(v for _, v in fees) / len(fees), 2) if fees else "",
        })
    dst_a = os.path.join(ROOT, "data", "contract_protocols.csv")
    with open(dst_a, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_a[0].keys()))
        w.writeheader()
        w.writerows(out_a)

    agg = defaultdict(float)
    cnt = defaultdict(int)
    for r in rows:
        if r["amount_yuan"]:
            agg[(r["code"], r["year"], r["kind"], r["nature"])] += float(r["amount_yuan"])
            cnt[(r["code"], r["year"], r["kind"])] += 1
    out_b = []
    for (code, year, kind, nat), v in sorted(agg.items()):
        out_b.append({"code": code, "year": year, "kind": kind, "nature": nat,
                      "fee_total_yuan": round(v, 2), "n_protocols": cnt[(code, year, kind)]})
    dst_b = os.path.join(ROOT, "data", "contract_fee_panel.csv")
    with open(dst_b, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_b[0].keys()))
        w.writeheader()
        w.writerows(out_b)

    print(f"[done] agreement level {len(out_a)} rows -> {dst_a}")
    print(f"[done] firm-year level {len(out_b)} rows -> {dst_b}")
    byc = defaultdict(int)
    for r in out_a:
        byc[r["code"]] += 1
    print("  agreements per firm:", ", ".join(f"{k}={v}" for k, v in sorted(byc.items())))
    for r in out_a:
        if r["code"] in ("600706", "000888"):
            print(f"  {r['code']} {r['counterparty'][:16]} {r['start_date']} "
                  f"n={r['n_reports']} fee={r['fee_series'][:80]}")


if __name__ == "__main__":
    main()
