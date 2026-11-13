#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract passages and tables related to operating rights / entrusted management from annual
report PDFs.

Purpose: build firm-by-year L3 note coding for RQ3 (operating-right structure determines value
capture) and H1 (coverage of operating rights). Cell-level meaning is not parsed here; hit pages
are dumped verbatim and left for manual coding.

Criteria:
  - keywords: entrusted management / operating rights / franchise / revenue sharing / management fee
  - every hit records: page, keyword, surrounding text (+/- RADIUS characters), tables on the page
  - pages with no text layer (scans) are flagged unparsed=True rather than treated as 'not present'

Outputs:
  data/mgmt_hits.csv           code,year,page,keyword,snippet,n_tables,unparsed
  data/mgmt_hits/{code}_{year}.json   per-report detail (including the tables of each page)
  data/mgmt_summary.csv        code,year,pages,n_hits,hit_pages
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime

import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "data", "raw_pdf")
OUT = os.path.join(ROOT, "data", "mgmt_hits")
DATA = os.path.join(ROOT, "data")
os.makedirs(OUT, exist_ok=True)

KW = ["委托管理", "受托管理", "经营权", "特许经营", "收入分成", "管理酬金"]
PAT = re.compile("|".join(KW))
RADIUS = 420


def norm(s):
    return re.sub(r"[ \t\u3000]+", " ", s.replace("\n", " "))


def scan(path):
    doc = pymupdf.open(path)
    pages, hits, tables = doc.page_count, [], 0
    hit_pages = set()
    for i, page in enumerate(doc):
        txt = page.get_text("text") or ""
        if len(txt.strip()) < 20:
            hits.append({"page": i + 1, "keyword": "", "snippet": "",
                         "n_tables": 0, "unparsed": True})
            continue
        tabs = []
        if PAT.search(txt):
            try:
                tabs = page.find_tables().tables
            except Exception:
                tabs = []
            tables += len(tabs)
            for m in PAT.finditer(txt):
                s = max(0, m.start() - RADIUS)
                e = min(len(txt), m.end() + RADIUS)
                hits.append({"page": i + 1, "keyword": m.group(0),
                             "snippet": norm(txt[s:e]), "n_tables": len(tabs),
                             "unparsed": False})
                hit_pages.add(i + 1)
    doc.close()
    return pages, hits, tables, sorted(hit_pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", nargs="*")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--keep", default="")
    a = ap.parse_args()

    files = sorted(f for f in os.listdir(PDF) if f.endswith(".pdf") and re.match(r"^\d{6}_\d{4}A\.pdf$", f))
    if a.code:
        files = [f for f in files if f[:6] in a.code]
    if a.limit:
        files = files[:a.limit]

    all_rows, summ = [], []
    t0 = time.time()
    for n, f in enumerate(files, 1):
        code, year = f[:6], int(f[7:11])
        try:
            pages, hits, nt, hp = scan(os.path.join(PDF, f))
        except Exception as e:
            print(f"[ERR ] {f} {type(e).__name__}: {e}", file=sys.stderr)
            continue
        with open(os.path.join(OUT, f"{code}_{year}.json"), "w", encoding="utf-8") as fh:
            json.dump({"file": f, "pages": pages, "n_tables": nt,
                       "fetched_at": datetime.now().isoformat(timespec="seconds"),
                       "hits": hits}, fh, ensure_ascii=False, indent=1)
        real = [h for h in hits if not h["unparsed"]]
        for h in real:
            all_rows.append({"code": code, "year": year, "page": h["page"],
                             "keyword": h["keyword"], "n_tables": h["n_tables"],
                             "snippet": h["snippet"]})
        summ.append({"code": code, "year": year, "pages": pages,
                     "n_hits": len(real), "hit_pages": len(hp),
                     "unparsed_pages": sum(1 for h in hits if h["unparsed"])})
        print(f"[{n}/{len(files)}] {code} {year} pages{pages} hits{len(real)} tables{nt}")

    with open(os.path.join(DATA, "mgmt_hits.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["code", "year", "page", "keyword", "n_tables", "snippet"])
        w.writeheader()
        w.writerows(all_rows)
    with open(os.path.join(DATA, "mgmt_summary.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["code", "year", "pages", "n_hits", "hit_pages", "unparsed_pages"])
        w.writeheader()
        w.writerows(summ)
    print(f"\n[done] {len(files)} files / {len(all_rows)} hits / {time.time()-t0:.0f}s")
    print("  -> data/mgmt_hits.csv, data/mgmt_summary.csv, data/mgmt_hits/*.json")


if __name__ == "__main__":
    main()
