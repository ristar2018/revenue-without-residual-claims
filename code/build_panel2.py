#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_panel2.py - annual panel of the 24 listed tourism firms (vendor datacenter, values in yuan)"""
import csv
import datetime
import time

import requests

OUT = "data/panel_annual_2015_2025_v2.csv"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

SAMPLE = [
    # A level: direct operators of scenic areas / destinations (core sample)
    ("600054", "黄山旅游", "A"),
    ("000888", "峨眉山A", "A"),
    ("002033", "丽江股份", "A"),
    ("603199", "九华旅游", "A"),
    ("603099", "长白山", "A"),
    ("603136", "天目湖", "A"),
    ("000430", "张家界", "A"),
    ("600593", "大连圣亚", "A"),
    ("000978", "桂林旅游", "A"),
    ("600749", "西藏旅游", "A"),
    ("002159", "三特索道", "A"),
    ("300859", "西域旅游", "A"),
    ("300144", "宋城演艺", "A"),
    ("600706", "曲江文旅", "A"),
    ("600576", "祥源文旅", "A"),
    ("002059", "云南旅游", "A"),
    ("002627", "三峡旅游", "A"),
    # B level: destination complexes (segment data only)
    ("000069", "华侨城A", "B"),
    ("600138", "中青旅", "B"),
    ("600358", "国旅联合", "B"),
    ("000863", "三湘印象", "B"),
    # C level: demand-side comparators (no scenic-area capital expenditure)
    ("000524", "岭南控股", "C"),
    ("002707", "众信旅游", "C"),
    ("000721", "西安饮食", "C"),
]

FIELDS = ["code", "name", "tier", "year", "revenue", "net_profit",
          "roe", "rev_yoy", "np_yoy", "gross_margin", "unit",
          "revenue_src", "fetched_at"]


def fetch(code):
    u = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    p = {"reportName": "RPT_LICO_FN_CPD", "columns": "ALL",
         "filter": '(SECURITY_CODE="%s")' % code,
         "pageNumber": 1, "pageSize": 200,
         "sortColumns": "REPORTDATE", "sortTypes": -1}
    r = requests.get(u, params=p, headers=UA, timeout=40)
    if r.status_code in (403, 429):
        time.sleep(8)
        r = requests.get(u, params=p, headers=UA, timeout=40)
    j = r.json()
    return ((j.get("result") or {}).get("data")) or []


def main():
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    rows = []
    for code, name, tier in SAMPLE:
        for r in fetch(code):
            d = (r.get("REPORTDATE") or "")[:10]
            if not d.endswith("12-31"):
                continue
            y = int(d[:4])
            if y < 2015 or y > 2025:
                continue
            rows.append({
                "code": code, "name": name, "tier": tier, "year": y,
                "revenue": r.get("TOTAL_OPERATE_INCOME"),
                "net_profit": r.get("PARENT_NETPROFIT"),
                "roe": r.get("WEIGHTAVG_ROE"),
                "rev_yoy": r.get("YSTZ"),
                "np_yoy": r.get("SJLTZ"),
                "gross_margin": r.get("XSMLL"),
                "unit": "CNY",
                "revenue_src": "em_datacenter",
                "fetched_at": now,
            })
        time.sleep(0.8)

    rows.sort(key=lambda x: (x["code"], x["year"]))
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    cells = len(SAMPLE) * 11
    print("wrote %d rows -> %s (theoretical %d cells, filled %.1f%%)"
          % (len(rows), OUT, cells, 100.0 * len(rows) / cells))


if __name__ == "__main__":
    main()
