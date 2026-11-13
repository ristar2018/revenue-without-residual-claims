#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W1 collection: full announcement index for the 24 firms + annual report PDFs for the 17 A-level firms.

Outputs (all with provenance, rerunnable):
  data/ann_raw/{code}.json      raw announcement list per firm (unprocessed)
  data/ann_index.csv            consolidated index: code, notice_date, art_code, title
  data/pdf_manifest.csv         download ledger (sha256 / byte size / screening outcome)
  data/raw_pdf/*.pdf            original PDFs

Usage:
  python code/collect_w1.py index              # announcement index only
  python code/collect_w1.py index --code 600706
  python code/collect_w1.py grab               # A-level annual reports, 2020-2024
  python code/collect_w1.py grab --code 600706 --years 2020 2021
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "ann_raw")
PDFDIR = os.path.join(DATA, "raw_pdf")
for d in (DATA, RAW, PDFDIR):
    os.makedirs(d, exist_ok=True)

# 24-firm sample (matches section 1.2 of the 02 protocol)
SAMPLE = [
    ("600054", "黄山旅游", "A"), ("000888", "峨眉山A", "A"), ("002033", "丽江股份", "A"),
    ("603199", "九华旅游", "A"), ("603099", "长白山", "A"), ("603136", "天目湖", "A"),
    ("000430", "张家界", "A"), ("600593", "大连圣亚", "A"), ("000978", "桂林旅游", "A"),
    ("600749", "西藏旅游", "A"), ("002159", "三特索道", "A"), ("300859", "西域旅游", "A"),
    ("300144", "宋城演艺", "A"), ("600706", "曲江文旅", "A"), ("600576", "祥源文旅", "A"),
    ("002059", "云南旅游", "A"), ("002627", "三峡旅游", "A"),
    ("000069", "华侨城A", "B"), ("600138", "中青旅", "B"), ("600358", "国旅联合", "B"),
    ("000863", "三湘印象", "B"),
    ("000524", "岭南控股", "C"), ("002707", "众信旅游", "C"), ("000721", "西安饮食", "C"),
]

INDEX_COLS = ["code", "name", "tier", "notice_date", "art_code", "title"]
MANIFEST_COLS = ["code", "name", "year", "kind", "title", "art_code", "notice_date", "url",
                 "path", "bytes", "sha256", "content_type", "pdf_magic", "status", "fetched_at"]


def cmd_index(a):
    targets = [s for s in SAMPLE if not a.code or s[0] == a.code]
    rows = []
    for code, name, tier in targets:
        cache = os.path.join(RAW, f"{code}.json")
        if os.path.exists(cache) and not a.force:
            with open(cache, encoding="utf-8") as f:
                items = json.load(f)
            print(f"[cache] {code} {name} {len(items)}")
        else:
            items = C.all_anns(code)
            with open(cache, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False)
            print(f"[fetch] {code} {name} {len(items)}")
        for it in items:
            rows.append({"code": code, "name": name, "tier": tier,
                         "notice_date": it.get("notice_date", ""),
                         "art_code": it.get("art_code", ""),
                         "title": it.get("title", "")})
        time.sleep(1.0)

    out = os.path.join(DATA, "ann_index.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nann_index.csv: {len(rows)} rows / {len({r['code'] for r in rows})} firms -> {out}")


def norm_title(t):
    """Strip company-name prefixes such as 'Qujiang Cultural Tourism:' and keep the document title only."""
    t = (t or "").strip()
    for sep in (":", "："):
        if sep in t:
            head, tail = t.split(sep, 1)
            if len(head) <= 12:          # The prefix is the short name, not part of the title body
                return tail.strip()
    return t


_SUFFIX = ("（修订版）", "(修订版)", "修订版", "--上传版", "-上传版",
           "（更新后）", "(更新后)", "全文")


def pick_report(items, year, kind="A"):
    """Pick the body text of one year's report. kind=A annual report / H1 interim report.

    Vendor titles look like 'Qujiang Cultural Tourism: Qujiang Cultural Tourism 2024 Annual
    Report', so the short name repeats and the title cannot be anchored at the start. Suffixes
    such as 'full text', '(revised)' and '--upload version' are stripped before matching. When a
    revised version and the original are both listed for the same year, take the later notice
    date, i.e. the revision.
    """
    kw = f"{year}年年度报告" if kind == "A" else f"{year}年半年度报告"
    tail = "年度报告" if kind == "A" else "半年度报告"
    reject = ("摘要", "英文", "问询", "回复", "专项", "说明", "更正", "已取消",
              "关于", "提示", "公告", "审计", "意见", "工作", "社会责任", "内控",
              "业绩预告", "业绩快报", "预告")
    cands = []
    for i in items:
        nt = norm_title(i.get("title")).replace("_", "").replace(" ", "")
        if kw in nt:
            j = dict(i)
            j["ntitle"] = nt
            cands.append(j)

    def base(t):
        changed = True
        while changed:
            changed = False
            for s in _SUFFIX:
                if t.endswith(s):
                    t = t[: -len(s)]
                    changed = True
        return t

    body = [c for c in cands
            if base(c["ntitle"]).endswith(tail)
            and not any(b in c["ntitle"] for b in reject)]
    if not body:
        body = [c for c in cands if base(c["ntitle"]).endswith(tail)]
    body.sort(key=lambda x: x.get("notice_date", ""), reverse=True)
    return body, cands


def pick_annual(items, year):
    """Legacy wrapper: pick the annual report body.

    Vendor titles look like 'Qujiang Cultural Tourism: Qujiang Cultural Tourism 2024 Annual
    Report', so the short name repeats and the title cannot be anchored at the start. Suffixes
    such as 'full text', '(revised)' and '--upload version' are stripped before matching. When a
    revised version and the original are both listed for the same year, take the later notice
    date, i.e. the revision.
    """
    key = f"{year}年年度报告"
    reject = ("摘要", "英文", "问询", "回复", "专项", "说明", "更正", "已取消",
              "关于", "提示", "公告", "审计", "意见", "工作", "社会责任", "内控")
    cands = []
    for i in items:
        nt = norm_title(i.get("title")).replace("_", "").replace(" ", "")
        if key in nt:
            j = dict(i)
            j["ntitle"] = nt
            cands.append(j)

    def base(t):
        changed = True
        while changed:
            changed = False
            for s in _SUFFIX:
                if t.endswith(s):
                    t = t[: -len(s)]
                    changed = True
        return t

    body = [c for c in cands
            if base(c["ntitle"]).endswith("年度报告")
            and not any(b in c["ntitle"] for b in reject)]
    if not body:
        body = [c for c in cands if base(c["ntitle"]).endswith("年度报告")]
    body.sort(key=lambda x: x.get("notice_date", ""), reverse=True)
    return body, cands


def get_pdf_bytes(art_code):
    import urllib.request
    url = f"https://pdf.dfcfw.com/pdf/H2_{art_code}_1.pdf"
    req = urllib.request.Request(url, headers=C.UA)
    r = urllib.request.urlopen(req, timeout=90)
    return url, r.read(), r.headers.get("Content-Type", "")


def cmd_grab(a):
    years = a.years or list(range(2020, 2025))
    targets = [s for s in SAMPLE if (not a.code or s[0] == a.code) and (not a.tier or s[2] in a.tier)]
    mpath = os.path.join(DATA, "pdf_manifest.csv")
    done = set()
    if os.path.exists(mpath) and not a.force:
        with open(mpath, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r.get("status") == "ok":
                    done.add((r["code"], r["year"], r.get("kind") or "A"))
    rows = []
    if os.path.exists(mpath) and not a.force:
        with open(mpath, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

    for code, name, tier in targets:
        cache = os.path.join(RAW, f"{code}.json")
        if not os.path.exists(cache):
            print(f"[skip] {code} has no announcement index, run index first")
            continue
        with open(cache, encoding="utf-8") as f:
            items = json.load(f)
        for year in years:
            if (code, year, a.kind) in done:
                continue
            body, cands = pick_report(items, year, a.kind)
            if not body:
                print(f"[miss] {code} {name} {year}: {len(cands)} candidates -> no body-text match")
                rows.append({"code": code, "name": name, "year": year, "kind": a.kind, "status": "not_found",
                             "title": ";".join(c["title"] for c in cands) or "",
                             "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                continue
            rec = body[0]
            path = os.path.join(PDFDIR, f"{code}_{year}{a.kind}.pdf")
            try:
                url, blob, ctype = get_pdf_bytes(rec["art_code"])
            except Exception as e:
                print(f"[err ] {code} {year} {type(e).__name__}: {str(e)[:70]}")
                rows.append({"code": code, "name": name, "year": year, "kind": a.kind, "title": rec["title"],
                             "art_code": rec["art_code"], "notice_date": rec["notice_date"],
                             "status": f"error:{type(e).__name__}",
                             "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                continue
            magic = blob[:5] == b"%PDF-"
            ok = ("pdf" in ctype.lower()) and magic and len(blob) > 100_000
            if ok:
                with open(path, "wb") as f:
                    f.write(blob)
            rows.append({
                "code": code, "name": name, "year": year, "kind": a.kind, "title": rec["title"],
                "art_code": rec["art_code"], "notice_date": rec["notice_date"], "url": url,
                "path": os.path.relpath(path, ROOT) if ok else "",
                "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                "content_type": ctype, "pdf_magic": magic,
                "status": "ok" if ok else "rejected",
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
            print(f"[{'ok  ' if ok else 'FAIL'}] {code} {name} {year} {len(blob)/1024:.0f}KB {rec['title'][:28]}")
            time.sleep(1.0)

    # Keep only the last record per (code, year, kind); reruns append rows with the same key and the ledger must hold one row per cell
    dedup, seen = [], set()
    for r in reversed(rows):
        k = (r.get("code"), r.get("year"), (r.get("kind") or "A"))
        if k in seen:
            continue
        seen.add(k)
        dedup.append(r)
    rows = list(reversed(dedup))

    with open(mpath, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    okn = sum(1 for r in rows if r.get("status") == "ok")
    print(f"\npdf_manifest.csv: ok={okn} / total rows={len(rows)} -> {mpath}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("index"); p1.add_argument("--code"); p1.add_argument("--force", action="store_true")
    p2 = sub.add_parser("grab"); p2.add_argument("--code"); p2.add_argument("--years", nargs="*", type=int)
    p2.add_argument("--kind", default="A", choices=["A", "H1"])
    p2.add_argument("--tier", nargs="*"); p2.add_argument("--force", action="store_true")
    a = ap.parse_args()
    {"index": cmd_index, "grab": cmd_grab}[a.cmd](a)


if __name__ == "__main__":
    main()
