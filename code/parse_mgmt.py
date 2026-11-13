#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract entrusted-management / operating-right table rows, amounts and sharing rates from the
pages flagged by mgmt_hits.

Strategy:
  1) only process hit pages that extract_mgmt.py flagged with n_tables>0 (to avoid catching text
     elsewhere)
  2) page.find_tables() returns every table; keep rows in which any cell contains entrusted /
     operating rights / fee / sharing / ticket
  3) run regular expressions for amounts and percentages over the hit snippets as candidates for
     manual coding (not conclusions)

Output data/mgmt_terms.csv:
  code,year,page,row_idx,n_cells,cell0..cell4 (first five columns),fee_wan,share_pct,n_money,raw_len

Usage:
  python code/parse_mgmt.py --top 8      # only the 8 firms with most hits
  python code/parse_mgmt.py              # all
"""
import argparse
import csv
import json
import os
import re

import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "data", "raw_pdf")
HITS = os.path.join(ROOT, "data", "mgmt_hits")
OUT = os.path.join(ROOT, "data", "mgmt_terms.csv")

ROWKEY = re.compile(r"委托|受托|经营权|特许经营|酬金|分成|门票|景区")
MONEY = re.compile(r"(\d[\d,]*\.?\d*)\s*万元")
PCT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")


def clean(s):
    return re.sub(r"\s+", "", str(s or ""))


def parse_doc(code, year):
    p = os.path.join(HITS, f"{code}_{year}.json")
    if not os.path.exists(p):
        return []
    meta = json.load(open(p, encoding="utf-8"))
    pages = sorted({h["page"] for h in meta["hits"] if h.get("n_tables")})
    if not pages:
        return []
    out = []
    doc = pymupdf.open(os.path.join(PDF, f"{code}_{year}A.pdf"))
    for pg in pages:
        try:
            tabs = doc[pg - 1].find_tables().tables
        except Exception:
            continue
        for t in tabs:
            for ri, row in enumerate(t.extract()):
                cells = [clean(c) for c in row if c is not None]
                if len(cells) < 2:
                    continue
                joined = "|".join(cells)
                if not ROWKEY.search(joined):
                    continue
                money = MONEY.search(joined)
                pct = PCT.search(joined)
                out.append({
                    "code": code, "year": year, "page": pg, "row_idx": ri,
                    "n_cells": len(cells),
                    "c0": cells[0][:60], "c1": cells[1][:60] if len(cells) > 1 else "",
                    "c2": cells[2][:60] if len(cells) > 2 else "",
                    "c3": cells[3][:60] if len(cells) > 3 else "",
                    "c4": cells[4][:60] if len(cells) > 4 else "",
                    "fee_wan": money.group(1) if money else "",
                    "share_pct": pct.group(1) if pct else "",
                    "raw": joined[:300],
                })
    doc.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=0, help="only process the N firms with the most hits")
    a = ap.parse_args()

    summ = list(csv.DictReader(open(os.path.join(ROOT, "data", "mgmt_summary.csv"), encoding="utf-8-sig")))
    per = {}
    for r in summ:
        per[r["code"]] = per.get(r["code"], 0) + int(r["n_hits"])
    order = [c for c, _ in sorted(per.items(), key=lambda kv: -kv[1])]
    if a.top:
        order = order[:a.top]
    files = sorted(f for f in os.listdir(HITS) if f.endswith(".json"))
    rows = []
    for f in files:
        code, year = f[:-5].split("_")
        if code not in order:
            continue
        rows.extend(parse_doc(code, int(year)))
    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["code", "year", "page", "row_idx", "n_cells",
                                           "c0", "c1", "c2", "c3", "c4",
                                           "fee_wan", "share_pct", "raw"])
        w.writeheader()
        w.writerows(rows)
    print(f"candidate rows {len(rows)} firms {len(order)} -> {OUT}")
    withfee = [r for r in rows if r["fee_wan"]]
    withpct = [r for r in rows if r["share_pct"]]
    print(f"  with an amount {len(withfee)} / with a percentage {len(withpct)}")
    for r in withpct[:12]:
        print(f"  {r['code']} {r['year']} p{r['page']} {r['share_pct']}% | {r['c0'][:24]} | {r['c1'][:30]}")


if __name__ == "__main__":
    main()
