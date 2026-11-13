#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RQ3 core step: turn the 'entrusted management' tables in annual and interim report notes
into a structured clause table that can be used in regressions.

Why a separate script instead of reusing extract_mgmt.py:
  extract_mgmt only returns 'hit pages + snippets' for locating material;
  here we need one row per arrangement with fields (principal, operator, subject matter,
  term, fee, sharing, right to self-operate), and we must distinguish two empty states
  that mean different things: a header row exists but the data rows are blank, i.e. an
  arrangement exists but no amount was recognised this period; the whole section reads
  'not applicable', i.e. the company has no such arrangement.

The two empty states are kept apart through `section_state`; 'not applicable' is never
recoded as a missing value.
Outputs:
  data/contract_terms.csv   one row per arrangement (auto-extracted + manual-review flag)
  data/contract_raw.csv     one raw text block per report (for manual re-reading; evidence kept)

Usage:
  python code/code_mgmt.py            # full run
  python code/code_mgmt.py 600706     # one firm
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT = os.path.join(ROOT, "data", "text")

# Paired anchors from table header to the closing note (standard notes-table structure)
BLOCKS = [
    ("受托管理", "本公司受托管理/承包情况表", "关联托管/承包情况说明"),
    ("委托管理", "本公司委托管理/出包情况表", "关联管理/出包情况说明"),
]

DATE = re.compile(r"(20\d\d)\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})?\s*日?")
MONEY = re.compile(r"-?\d{1,3}(?:,\d{3})*\.\d{2}|-?\d{6,}")
PCT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")

# Sharing ladder: 'years 1-5 100%', '1-5 years: 100%'
LADDER = re.compile(r"(第?\s*\d+\s*[-–—~至]\s*\d+\s*年)[^\d%]{0,12}(\d{2,3}(?:\.\d+)?)\s*%")

FIELDS = ["code", "year", "kind", "item", "section_state", "counterparty", "operator",
          "scope", "includes_commercial", "start_date", "end_date", "fee_amount",
          "fee_unit", "fee_pct_rev", "share_ladder", "share_current",
          "can_self_operate", "rev_recog_basis", "src_page", "art_code",
          "confidence", "raw_block"]


def page_of(text, idx):
    return text.count("\f", 0, idx) + 1


def norm(s):
    return re.sub(r"[ \t\u3000]+", " ", s)


def clean_name(s):
    s = re.sub(r"[\s\d,.\-()（）]+$", "", s.strip())
    return s.strip()


def parse_block(seg):
    """Extract the fields that can be filled automatically from a table block; leave the rest empty for manual coding."""
    seg = norm(seg)
    dates = ["-".join([d[0], f"{int(d[1]):02d}", f"{int(d[2]):02d}" if d[2] else "01"])
             for d in DATE.findall(seg)]
    money = MONEY.findall(seg)
    ladder = LADDER.findall(seg)
    out = {
        "start_date": dates[0] if dates else "",
        "end_date": dates[1] if len(dates) > 1 else "",
        "share_ladder": "; ".join(f"{a.strip()}:{b}%" for a, b in ladder),
        "share_current": "",
        "fee_amount": "",
        "fee_unit": "",
        "counterparty": "",
        "operator": "",
        "scope": "",
        "includes_commercial": "",
        "can_self_operate": "",
        "rev_recog_basis": "",
    }
    if money:
        v = money[-1].replace(",", "")
        try:
            out["fee_amount"] = f"{float(v):.2f}"
            out["fee_unit"] = "元"
        except ValueError:
            pass
    # Yuan vs ten-thousand yuan: the unit sits on a header line of its own, 'unit: yuan'
    m = re.search(r"单位[：:]\s*(万元|元)", seg)
    if m:
        out["fee_unit"] = m.group(1)
    # Target type (entrusted / commissioned asset-type column)
    m = re.search(r"(景区|索道|酒店|餐饮|旅行社|旅游服务|商业|物业|车辆|公园)[^\s]{0,12}", seg)
    if m:
        out["scope"] = m.group(0)
    if re.search(r"商铺|商业街|商业物业|购物|零售|店面", seg):
        out["includes_commercial"] = "1"
    if re.search(r"不适用|无", seg):
        pass
    return out


def analyse(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    text = raw.replace("\f", "\n\f\n")
    fn = os.path.basename(path)
    code, year, kind = fn[:6], int(fn[7:11]), ("H1" if fn[11:13] == "H1" else "A")
    items, raws = [], []
    for tag, head, tail in BLOCKS:
        i = text.find(head)
        if i < 0:
            items.append(dict(code=code, year=year, kind=kind, item=tag, section_state="no_section"))
            continue
        j = text.find(tail, i + len(head))
        seg = text[i + len(head): j if j > 0 else i + 1500]
        has_data = bool(DATE.search(seg)) or bool(MONEY.search(seg))
        state = "has_data" if has_data else ("na" if "不适用" in seg else "empty_table")
        f = parse_block(seg) if has_data else {}
        row = dict(code=code, year=year, kind=kind, item=tag, section_state=state,
                   src_page=page_of(text, i), art_code="", confidence="auto")
        row.update({k: f.get(k, "") for k in
                    ("counterparty", "operator", "scope", "includes_commercial", "start_date",
                     "end_date", "fee_amount", "fee_unit", "fee_pct_rev", "share_ladder",
                     "share_current", "can_self_operate", "rev_recog_basis")})
        row["raw_block"] = re.sub(r"\s+", " ", seg)[:900]
        items.append(row)
    return items


def main():
    only = set(sys.argv[1:])
    files = sorted(f for f in os.listdir(TXT) if re.match(r"^\d{6}_\d{4}(A|H1)\.txt$", f))
    allrows = []
    for n, fn in enumerate(files, 1):
        if only and fn[:6] not in only:
            continue
        rows = analyse(os.path.join(TXT, fn))
        allrows.extend(rows)
        if n % 20 == 0:
            print(f"[{n}/{len(files)}] ...")
    out = os.path.join(ROOT, "data", "contract_terms.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(allrows)
    import collections
    c = collections.Counter((r["item"], r["section_state"]) for r in allrows)
    print(f"\n[done] {len(allrows)} rows -> {out}")
    for k, v in sorted(c.items()):
        print(f"  {k[0]:6s} {k[1]:12s} {v}")


if __name__ == "__main__":
    main()
