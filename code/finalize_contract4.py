#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clause table v4: values are read by header column position, fixing the scope / nature /
pricing contamination in v3.

Root cause in v3 (exposed when 15 records were manually checked):
  in multi-column tables the header cells are split into two cells ('principal / contracting
  party name' + 'name', 'entrusted / contracted asset type' + 'type', 'entrusted income /
  contracted income basis' + 'pricing basis'), so the real column order of such a table is
  0/2/4/6/7/8/9, while v3 hard-coded 0/1/2:
    operator -> empty string,
    asset type -> the operator name (e.g. 'Guangzhou GZL International Travel Service'),
    pricing basis -> the principal name or half a sentence.
  On top of that, nature_of(cp, scope) judged by the counterparty name with a loose
  ('tourism', 'scenic area') mapping, so a name such as 'Yunnan Tourism Co., Ltd.' turned a
  whole batch of subjects into scenic areas.

The four changes in v4:
  1) Header-driven columns - each table (rec=0) locates its columns from the header text; when a
     header cell is split, the two neighbouring cells are concatenated before matching, and the
     script distinguishes 'take the first cell' from 'take the last cell' (amount columns usually
     land in the last cell of a split).
  2) Subject cleaning - scope keeps the asset-type text only, stripping date residue, page-number
     residue and spaces between Chinese characters; the original value is kept in scope_raw.
  3) nature is judged from the cleaned scope only; the loose 'tourism -> scenic area' mapping is gone.
  4) Name normalisation - counterparty / operator lose the line-break spaces between Chinese
     characters, which makes grouping reliable.

Input   data/contract_cells6.csv
Output  data/contract_terms_v4.csv
"""
import csv
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONEY = re.compile(r"-?\d{1,3}(?:,\d{3})+\.\d{2}|-?\d{4,}\.\d{2}")
DATE_FULL = re.compile(r"(\d{4})\s*[年/]\s*(\d{1,2})\s*[月/]\s*(\d{1,2})\s*日?")
DATE_YM = re.compile(r"(\d{4})\s*[年/]\s*(\d{1,2})\s*月")
DATE_FRAG = re.compile(r"\d{4}\s*[年/]\s*\d{1,2}\s*月?\s*\d{0,2}\s*日?")
PAGE_FRAG = re.compile(r"\b\d{2,3}\s*/\s*\d{2,3}\b")
CJK_SPACE = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])")
LOOSE_NUM = re.compile(r"(?<!\d)(\d{1,2})(?!\d)")

# Re-check the confirmed row-by-row ground truth (located by rec)
REC_FIXES = {
    ("002059", "2022", "A", "170", 1): dict(counterparty="云南世博旅游控股集团有限公司",
                                            operator="云南旅游股份有限公司",
                                            scope="其他资产托管",
                                            start="2017-07-31", end=""),
    ("002059", "2022", "H1", "117", 1): dict(counterparty="云南世博旅游控股集团有限公司",
                                             operator="云南旅游股份有限公司",
                                             scope="其他资产托管",
                                             start="2017-07-31", end=""),
    ("002059", "2022", "A", "170", 2): dict(start="2019-02-01", end=""),
    ("002059", "2022", "A", "170", 3): dict(start="2019-02-01", end=""),
}
DROP_PAGE = {("000888", "2018", "A", "138")}   # The whole page is a related-party lease table
DROP_REC = set()

# Rows that need a manual note (M07: three co-listed principals counted as one agreement)
NOTES = {
    ("002627", "2020", "A", "207", 1):
        "委托方为三家并列（宜昌交通旅游产业发展集团、宜昌国有资本投资控股集团、"
        "宜昌市夷陵国有资产经营有限公司）；按一条协议计，不拆分",
    ("002627", "2020", "H1", "153", 1):
        "委托方为三家并列；半年报同期披露，与 2020A 为同一协议",
    ("002627", "2021", "H1", "153", 1):
        "委托方为三家并列；半年报同期披露，与 2020A 为同一协议",
}

# Vertical-layout pages cut the asset-type cell into fragments (e.g. only the character 管 survives); such ultra-short scope values are back-filled with the mode of the same page.
# The threshold must be 2: among the legitimate categories 饭店 (hotel) is itself only two characters, so a threshold of 3 would treat all 26 hotel records as fragments.
SCOPE_MIN_LEN = 2
# 'the entire operating and management rights of XX company' is a way of writing entrusted operating rights, so it is merged back into the main category; nature is still judged on the original value (port)
SCOPE_MAP = [("全部经营管理权", "经营管理权托管")]

# nature is judged on the asset type alone; wording such as 'tourism' in the counterparty name is not used
NATURE = [("索道", ("索道", "客运")),
          ("港口", ("港务", "港口", "码头", "航运", "游船")),
          ("酒店", ("饭店", "酒店", "宾馆")),
          ("旅行社", ("旅行社", "旅游社")),
          ("景区", ("景区", "门票"))]


def squash(s):
    return re.sub(r"\s+", "", s)


def clean_scope(s):
    s = PAGE_FRAG.sub(" ", s)
    s = DATE_FRAG.sub(" ", s)
    s = s.replace("／", "/").replace("，", "、")
    s = CJK_SPACE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip(" /·、,，")
    s = re.sub(r"(?<![\d.])\s*/\s*\d{1,3}$", "", s)   # Trailing page-number residue
    return s.strip()


def clean_name(s):
    s = CJK_SPACE.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def nature_of(scope_clean):
    t = squash(scope_clean)
    for name, keys in NATURE:
        if any(k in t for k in keys):
            return name
    return "其他"


def find_span(cells, *keys):
    """Return the (first cell, last cell) occupied by a header field; when the header is split,
    match on two or three adjacent cells concatenated.

    Single-cell hits take priority (so that 'recognised this period' is not stolen by a longer
    window); a split hit returns the window boundaries, and the caller takes the first cell for
    text fields and the last cell for amounts (in split cells the value usually lands in the last).
    """
    sq = [squash(c) for c in cells]
    for k in keys:
        for i, c in enumerate(sq):
            if k in c:
                return i, i
    for k in keys:
        for width in (2, 3):
            for i in range(len(sq) - width + 1):
                if k in "".join(sq[i:i + width]):
                    return i, i + width - 1
    return -1, -1


def header_cols(cells):
    d = {}
    for name, keys in (("cp", ("委托方", "出包方")), ("op", ("受托方", "承包方")),
                       ("scope", ("资产类型", "资产类")), ("start", ("起始日",)),
                       ("end", ("终止日",)), ("pricing", ("定价依据", "定价依")),
                       ("amt", ("本期确认",))):
        d[name] = find_span(cells, *keys)
    if d["amt"][0] < 0:
        d["amt"] = (len(cells) - 1, len(cells) - 1)
    return d


def main():
    src = os.path.join(ROOT, "data", "contract_cells6.csv")
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    out = []
    hdr = None
    for r in rows:
        cells = [c.strip() for c in r["cells"].split(" | ")]
        if r["rec"] == "0":
            hdr = header_cols(cells)
            continue
        key4 = (r["code"], r["year"], r["kind"], r["page"])
        key5 = key4 + (int(r["rec"]),)
        if key4 in DROP_PAGE or key5 in DROP_REC:
            continue

        h = hdr or dict(cp=(0, 0), op=(1, 1), scope=(2, 2), start=(3, 3),
                        end=(4, 4), pricing=(-1, -1), amt=(len(cells) - 1, len(cells) - 1))

        def at(span, default):
            a, b = span
            if 0 <= a < len(cells):
                return cells[a]
            return cells[default] if default < len(cells) else ""

        def joined(span):
            a, b = span
            if a < 0 or a >= len(cells):
                return ""
            return " ".join(c for c in cells[a:b + 1] if c)

        flags = []
        cp = clean_name(at(h["cp"], 0))
        cp = re.sub(r"\s*(合计|关联.*)$", "", cp).strip()
        cp = re.sub(r"、+", "；", cp).strip("；")
        op = clean_name(at(h["op"], 1))
        if op != at(h["op"], 1):
            flags.append("name_cleaned")
        scope_raw = at(h["scope"], 2)
        scope = clean_scope(scope_raw)
        if scope != scope_raw:
            flags.append("scope_cleaned")
        if not scope:
            flags.append("scope_empty")
        for k, v in SCOPE_MAP:
            if k in squash(scope):
                scope = v
                flags.append("scope_mapped")
                break

        # Dates: prefer the start/end columns, fall back to scanning the whole row
        start = end = ""
        seg_start = at(h["start"], 3)
        seg_end = at(h["end"], 4)
        ms = DATE_FULL.search(seg_start)
        me = DATE_FULL.search(seg_end)
        if not ms and "年" in seg_start and "月" in seg_start and "日" in seg_start:
            # Split months such as '2019 month 01 day' with '02' in the neighbouring cell
            spare = [c for c in cells[h["start"][0] + 1:h["start"][0] + 3] if c]
            if spare:
                m2 = LOOSE_NUM.search(spare[0])
                y = re.search(r"(\d{4})", seg_start)
                dd = re.search(r"月\s*(\d{1,2})\s*日", seg_start)
                if m2 and y and dd:
                    start = "%s-%02d-%02d" % (y.group(1), int(m2.group(1)), int(dd.group(1)))
                    flags.append("date_reassembled")
        if ms and not start:
            start = "%s-%02d-%02d" % (ms.group(1), int(ms.group(2)), int(ms.group(3)))
        if me:
            end = "%s-%02d-%02d" % (me.group(1), int(me.group(2)), int(me.group(3)))
        if not start:
            body = " ".join(cells)
            ds = DATE_FULL.findall(body)
            if ds:
                start = "%s-%02d-%02d" % (ds[0][0], int(ds[0][1]), int(ds[0][2]))
                if len(ds) >= 2 and not end:
                    end = "%s-%02d-%02d" % (ds[1][0], int(ds[1][1]), int(ds[1][2]))
                flags.append("date_from_body")
            else:
                ym = DATE_YM.findall(body)
                if ym:
                    start = "%s-%02d" % (ym[0][0], int(ym[0][1]))
                    flags.append("month_only")

        # Amounts: prefer the 'recognised this period' column (last cell when the cell is split), fall back to scanning the row backwards
        amt = ""
        m = MONEY.search(at(h["amt"], len(cells) - 1))
        if m:
            amt = m.group(0).replace(",", "")
        else:
            for c in reversed(cells):
                if DATE_FULL.search(c):
                    continue
                mm = MONEY.search(c)
                if mm:
                    amt = mm.group(0).replace(",", "")
                    flags.append("amount_from_other_col")
                    break
        if not amt:
            flags.append("amount_empty")

        fix = REC_FIXES.get(key5)
        if fix:
            cp = fix.get("counterparty", cp)
            op = fix.get("operator", op)
            if fix.get("scope"):
                scope = fix["scope"]
            start = fix.get("start", start)
            end = fix.get("end", end)
            flags.append("from_review")

        pricing = clean_name(joined(h["pricing"]))
        # When the pricing-basis cell holds only a footnote number ('(1)', 'per (1)', 'per note 1'), the actual pricing sits in the notes below the table
        mark = re.sub(r"^据", "", pricing).strip()
        if re.fullmatch(r"[（(]\d+[）)]|备注\s*\d+|\d+[）)]", mark):
            pricing = "见附注"
        if not pricing:
            flags.append("pricing_empty")

        nature = nature_of(scope_raw if "scope_mapped" in flags else scope)

        out.append({
            "code": r["code"], "year": r["year"], "kind": r["kind"],
            "page": r["page"], "rec": r["rec"],
            "counterparty": cp, "operator": op,
            "scope": scope, "scope_raw": scope_raw,
            "start_date": start, "end_date": end,
            "pricing": pricing,
            "amount_yuan": amt,
            "nature": nature,
            "note": NOTES.get(key5, ""),
            "parse_flag": ";".join(flags),
        })

    # Second pass: back-fill ultra-short scope values on the same page with the mode (vertical pages cut 其他资产托管 down to the single character 管)
    by_page = {}
    for rec in out:
        by_page.setdefault((rec["code"], rec["year"], rec["kind"], rec["page"]), []).append(rec)
    for recs in by_page.values():
        good = [r["scope"] for r in recs if len(squash(r["scope"])) >= SCOPE_MIN_LEN]
        if not good:
            continue
        mode = Counter(good).most_common(1)[0][0]
        for r in recs:
            if len(squash(r["scope"])) < SCOPE_MIN_LEN:
                r["scope"] = mode
                r["nature"] = nature_of(mode)
                r["parse_flag"] = ";".join(
                    [f for f in r["parse_flag"].split(";") if f] + ["scope_from_sibling"])

    dst = os.path.join(ROOT, "data", "contract_terms_v4.csv")
    cols = ["code", "year", "kind", "page", "rec", "counterparty", "operator",
            "scope", "scope_raw", "start_date", "end_date", "pricing",
            "amount_yuan", "nature", "note", "parse_flag"]
    with open(dst, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    n = len(out)
    print(f"[done] {n} rows -> {dst}")
    print("  with an amount %d / with a start date %d / with a pricing basis %d / all three present %d" % (
        sum(1 for r in out if r["amount_yuan"]),
        sum(1 for r in out if r["start_date"]),
        sum(1 for r in out if r["pricing"]),
        sum(1 for r in out if r["amount_yuan"] and r["start_date"] and r["counterparty"])))
    print("  scope:", Counter(r["scope"] for r in out).most_common())
    print("  nature:", Counter(r["nature"] for r in out).most_common())
    print("  flag:", Counter(f for r in out for f in r["parse_flag"].split(";") if f).most_common())


if __name__ == "__main__":
    main()