#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract the key consolidated statement items from -layout annual report text and build a
firm-year financial panel.

Purpose:
  - H2 capital burden: interest-bearing debt / financial expenses / interest expense / long-term
    assets / depreciation and amortisation
  - RQ2 cost squeeze: asset impairment / credit impairment / employee benefits payable / cash paid
    to employees
  - value capture: accounts receivable (including scenic-area management fees receivable), other
    receivables, revenue deductions

Extraction rules (important - do not change to 'search the whole text'):
  - accept only lines that start with the item name and are followed by a two-decimal amount
    (balance-sheet / income-statement layout)
  - take the FIRST occurrence of an item (consolidated statements precede the parent-only
    statements; notes come later)
  - convert everything to yuan; when the statement is presented in ten-thousand yuan ('unit:
    ten-thousand yuan' in the header) multiply by 1e4
  - items that cannot be extracted are left empty and counted as missing, never filled with 0

Outputs:
  data/fin_panel.csv   code,year,<items...>,unit_scale,src_page
  data/fin_miss.csv    list of missing items per file (used for acceptance checks)
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT = os.path.join(ROOT, "data", "text")
OUT = os.path.join(ROOT, "data", "fin_panel.csv")
MISS = os.path.join(ROOT, "data", "fin_miss.csv")

NUM = r"(-?[\d,]+\.\d{2})"

# key -> (regex label, whether repeated matches are allowed and the first one is taken)
ITEMS = {
    "revenue":        r"营业收入",
    "total_revenue":  r"营业总收入",
    "net_profit":     r"净利润",
    "np_parent":      r"归属于母公司(?:股东|所有者)的净利润",
    "ar":            r"应收账款",
    "other_ar":      r"其他应收款",
    "inventory":     r"存货",
    "fa":            r"固定资产",
    "cip":           r"在建工程",
    "ia":            r"无形资产",
    "ip":            r"投资性房地产",
    "rou":           r"使用权资产",
    "gw":            r"商誉",
    "st_loan":       r"短期借款",
    "lt_loan":       r"长期借款",
    "bond":          r"应付债券",
    "ncl_due1y":     r"一年内到期的非流动负债",
    "lease_liab":    r"租赁负债",
    "fin_exp":       r"财务费用",
    "int_exp":       r"其中[：:]?\s*利息费用|利息支出",
    "int_inc":       r"利息收入",
    "asset_imp":     r"资产减值损失",
    "credit_imp":    r"信用减值损失",
    "dep_fa":        r"固定资产折旧(?:、油气资产折耗、生产性生物资产折旧)?",
    "am_ia":         r"无形资产摊销",
    "am_lt":         r"长期待摊费用摊销",
    "staff_pay":     r"应付职工薪酬",
    "cash_staff":    r"支付给职工以及为职工支付的现金",
}

UNIT_HINT = re.compile(r"单位[：:]\s*(元|千元|万元|百万元)")


def to_float(s):
    try:
        return float(s.replace(",", ""))
    except Exception:
        return None


MONEY_LINE = re.compile(r"^\s*-?[\d,]+\.\d{2}(?:\s{2,}-?[\d,]+\.\d{2})*\s*$")
BIGMONEY = re.compile(r"-?\d{1,3}(?:,\d{3})+\.\d{2}|-?\d{6,}\.\d{2}")


def reflow(pages):
    """Join 'label wrapped over lines + amount on a line of its own' back into logical lines.

    Under -layout there are two failure modes:
      a) label and amount on the same line (normal table row)
      b) the label is split over 2-3 lines and the amount occupies a line of its own
    Rule: a line containing an 'accounting-grade amount' (>= 100,000 with thousands separators, or
    >= 6 integer digits) is treated as complete and emitted together with the accumulated label;
    otherwise it accumulates into the label and resets at a full stop or when it grows too long.
    """
    rows = []
    pend = ""
    for pi, p in enumerate(pages):
        for ln in p.split("\n"):
            s = ln.strip()
            if not s:
                continue
            if MONEY_LINE.match(ln) or BIGMONEY.search(s):
                rows.append((pi + 1, (pend + " " + s).strip()))
                pend = ""
                continue
            if len(s) <= 20 and not s.endswith(("。", "，", "、", "；", "：", ":", ",", ";"))                     and len(pend) + len(s) <= 40:
                pend = pend + s
            else:
                pend = ""
    return rows


def parse(path):
    text = open(path, encoding="utf-8", errors="ignore").read()
    pages = text.split("\f")
    scale = 1.0
    m = UNIT_HINT.search("".join(pages[:40]))
    if m:
        scale = {"元": 1.0, "千元": 1e3, "万元": 1e4, "百万元": 1e6}[m.group(1)]
    got, where = {}, {}
    rows = reflow(pages)
    # Read only inside the consolidated statements (after the first 'consolidated balance sheet'): the ten-thousand-yuan tables in the
    # MD&A section pollute the global first match (000430 FY2020 was read as -11083.01 ten-thousand yuan).
    fin_from = min((pi for pi, ln in rows if "合并资产负债表" in ln), default=0)
    for k, lab in ITEMS.items():
        pat = re.compile(r"(?:" + lab + r")(?:[（(][^）)]{0,40}[）)])?\s*" + NUM)
        cand = [r for r in rows if r[0] >= fin_from] or rows
        for pi, ln in cand:
            mm = pat.search(ln)
            if not (mm and mm.start() <= 45):
                continue
            pre = ln[max(0, mm.start() - 14):mm.start()]
            if k == "net_profit" and "归属" in pre:
                continue          # Skip 'net profit attributable to the parent', to avoid mixing up the two definitions
            if "万元" in ln or "亿元" in ln:
                continue          # Narrative sentence ('... net profit -11,083.01 ten-thousand yuan'), not a table row
            if len(re.findall(r"-?\d[\d,]*\.\d{2}", ln)) < 2:
                continue          # A table row has at least two numeric columns (current / prior)
            if True:
                v = to_float(mm.group(1))
                if v is not None:
                    got[k] = v * scale
                    where[k] = pi
                break
    return got, where, scale


def main():
    files = sorted(f for f in os.listdir(TXT) if re.match(r"^\d{6}_\d{4}A\.txt$", f))
    if len(sys.argv) > 1:
        files = [f for f in files if f[:6] in sys.argv[1:]]
    keys = list(ITEMS)
    rows, miss = [], []
    for f in files:
        code, year = f[:6], int(f[7:11])
        got, where, scale = parse(os.path.join(TXT, f))
        row = {"code": code, "year": year, "unit_scale": scale}
        row.update({k: ("" if k not in got else f"{got[k]:.2f}") for k in keys})
        rows.append(row)
        lost = [k for k in keys if k not in got]
        if lost:
            miss.append({"code": code, "year": year, "miss": ";".join(lost),
                         "n_miss": len(lost)})
    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["code", "year", "unit_scale"] + keys)
        w.writeheader()
        w.writerows(rows)
    with open(MISS, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["code", "year", "miss", "n_miss"])
        w.writeheader()
        w.writerows(miss)
    print(f"[ok] {len(rows)} files -> {OUT}")
    tot = len(rows) * len(keys)
    filled = sum(1 for r in rows for k in keys if r[k] != "")
    print(f"fill rate {filled}/{tot} = {filled/tot:.1%}")
    per = {}
    for k in keys:
        c = sum(1 for r in rows if r[k] != "")
        per[k] = c
    for k, c in sorted(per.items(), key=lambda kv: kv[1]):
        print(f"  {k:12s} {c}/{len(rows)}")
    sc = {}
    for r in rows:
        sc[r["unit_scale"]] = sc.get(r["unit_scale"], 0) + 1
    print("unit multiplier distribution:", sc)


if __name__ == "__main__":
    main()
