#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RQ3 descriptive statistics: structure, scale, term and sharing rate of operating-right clauses.

Input:
  data/contract_terms_v4.csv          99 records (94 notes-table + 5 related-party narrative)
  data/panel_annual_2015_2025_v2.csv  firm-year revenue (yuan), used for fee-to-revenue ratios
Output:
  data/rq3_descriptive.csv            long table: dimension / group / metric / value
  data/rq3_protocols.csv              agreement level after merging the narrative agreements
                                      (merged across reports)
  screen: a one-screen summary that can be cited directly

Criteria (must be declared this way in the paper):
  1. Annual records use the full-year 'fee recognised this period'; interim reports are half-year
     figures and are NEVER added to annual figures;
  2. the fee-to-revenue ratio is computed on kind=A annual records only, with consolidated operating
     revenue of that year as the denominator; interim records are annualised (x2) and reported
     separately, never pooled into the annual distribution;
  3. the subject-matter type (nature) of notes-table records comes from the asset-type column of the
     source; 000524's 'entrusted operating and management rights' is kept verbatim and no entity is
     inferred from the counterparty name;
  4. `pct_same_type` is the disclosed 'share of same-type transaction amount', NOT a share of
     operating revenue.
"""
import csv
import os
import re
import statistics as st
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
SRC = os.path.join(D, "contract_terms_v4.csv")
PAN = os.path.join(D, "panel_annual_2015_2025_v2.csv")

BUCKETS = [(0, 5, "≤5年"), (6, 10, "6–10年"), (11, 15, "11–15年"),
           (16, 20, "16–20年"), (21, 999, ">20年")]


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def dur_years(r):
    a, b = r.get("start_date", ""), r.get("end_date", "")
    if not a or not b or len(a) < 7 or len(b) < 7:
        return None
    try:
        ya, yb = int(a[:4]), int(b[:4])
        ma, mb = int(a[5:7]), int(b[5:7])
    except ValueError:
        return None
    d = (yb - ya) + (mb - ma) / 12.0
    return d if d > 0 else None


def main():
    rs = rows(SRC)
    rev = {(r["code"], r["year"]): float(r["revenue"]) for r in rows(PAN) if r["revenue"]}
    out = []  # (dimension, group, metric, value)

    # A coverage
    out.append(("覆盖", "全部", "记录数", len(rs)))
    for ch, n in Counter(r["channel"] for r in rs).items():
        out.append(("覆盖", f"channel={ch}", "记录数", n))
    out.append(("覆盖", "全部", "公司数", len({r["code"] for r in rs})))
    out.append(("覆盖", "全部", "报告数", len({(r["code"], r["year"], r["kind"]) for r in rs})))
    for y in sorted({r["year"] for r in rs}):
        out.append(("覆盖·年", y, "记录数", sum(1 for r in rs if r["year"] == y)))

    # B amounts (by firm x nature, annual records only)
    ann = [r for r in rs if r["kind"] == "A"]
    byc = defaultdict(list)
    for r in ann:
        byc[(r["code"], r["nature"])].append(float(r["amount_yuan"]))
    for (code, nat), v in sorted(byc.items()):
        out.append(("酬金·公司×性质", f"{code}/{nat}", "n", len(v)))
        out.append(("酬金·公司×性质", f"{code}/{nat}", "合计元", round(sum(v), 2)))
        out.append(("酬金·公司×性质", f"{code}/{nat}", "中位数元", round(st.median(v), 2)))

    # C fee-to-revenue ratio (annual records)
    ratios = []
    for r in ann:
        rv = rev.get((r["code"], r["year"]))
        if not rv:
            continue
        ratios.append((float(r["amount_yuan"]) / rv, r["code"], r["year"]))
    if ratios:
        vals = [x[0] for x in ratios]
        out.append(("酬金占营收", "年度记录", "n", len(vals)))
        out.append(("酬金占营收", "年度记录", "中位数%", round(100 * st.median(vals), 4)))
        out.append(("酬金占营收", "年度记录", "均值%", round(100 * st.mean(vals), 4)))
        out.append(("酬金占营收", "年度记录", "最大%", round(100 * max(vals), 4)))
        out.append(("酬金占营收", "年度记录", "最小%", round(100 * min(vals), 4)))
        top = sorted(ratios, reverse=True)[:3]
        for v, c, y in top:
            out.append(("酬金占营收", "最高三条", f"{c} {y}", round(100 * v, 4)))

    # D term structure
    dc = Counter()
    for r in rs:
        d = dur_years(r)
        if d is None:
            dc["无法判定"] += 1
            continue
        for lo, hi, lab in BUCKETS:
            if lo <= d <= hi:
                dc[lab] += 1
                break
    for k in ["≤5年", "6–10年", "11–15年", "16–20年", ">20年", "无法判定"]:
        if dc[k]:
            out.append(("期限", k, "记录数", dc[k]))
    ds = [dur_years(r) for r in rs if dur_years(r)]
    if ds:
        out.append(("期限", "全部", "中位年数", round(st.median(ds), 2)))

    # E sharing-rate ladder
    lad = [r for r in rs if "分成" in r["pricing"] or "归受托方" in r["pricing"] or "%" in r["pricing"]]
    out.append(("分成条款", "含分成/比例表述", "记录数", len(lad)))
    lab = Counter()
    for r in lad:
        if "100%" in r["pricing"] and "88%" in r["pricing"]:
            lab["四级阶梯 100/92/90/88"] += 1
        elif "累进" in r["pricing"] or "10–20%" in r["pricing"]:
            lab["超额累进 50–80%"] += 1
        elif "8%" in r["pricing"]:
            lab["按营业收入计提 8%"] += 1
        else:
            lab["其他"] += 1
    for k, v in lab.items():
        out.append(("分成条款", k, "记录数", v))

    # F the Qujiang case
    qj = [r for r in rs if r["code"] == "600706"]
    qsum = sum(float(r["amount_yuan"]) for r in qj)
    h1rev = 770241193.31  # 'operating revenue' from the consolidated income statement of the 2024 interim report, see data/text/600706_2024H1.txt L227
    out.append(("曲江个案", "2024H1", "协议数", len(qj)))
    out.append(("曲江个案", "2024H1", "酬金合计万元", round(qsum / 1e4, 2)))
    out.append(("曲江个案", "2024H1", "占合并营收%", round(100 * qsum / h1rev, 2)))
    for r in qj:
        out.append(("曲江个案", r["scope"][:18], "酬金万元",
                    round(float(r["amount_yuan"]) / 1e4, 2)))
        out.append(("曲江个案", r["scope"][:18], "pct_same_type", r["pct_same_type"]))

    with open(os.path.join(D, "rq3_descriptive.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["dimension", "group", "metric", "value"])
        w.writerows(out)

    # agreement level (recomputed after the narrative agreements were merged; the key includes channel so that agreements with the same subject matter are not merged across sources)
    proto = {}
    for r in rs:
        cp = "".join(r["counterparty"].split())
        key = (r["code"], cp[:14], r["start_date"][:7], r["scope"][:6], r["channel"])
        p = proto.setdefault(key, {"code": r["code"], "counterparty": cp, "scope": r["scope"],
                                   "nature": r["nature"], "channel": r["channel"],
                                   "start_date": r["start_date"], "end_date": r["end_date"],
                                   "fees": [], "reports": []})
        p["reports"].append(r["year"] + r["kind"])
        if r["amount_yuan"]:
            p["fees"].append((r["year"] + r["kind"], float(r["amount_yuan"])))
    with open(os.path.join(D, "rq3_protocols.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["code", "counterparty", "scope", "nature", "channel",
                                          "start_date", "end_date", "n_reports", "fee_series"])
        w.writeheader()
        for p in sorted(proto.values(), key=lambda x: (x["code"], x["start_date"])):
            w.writerow({"code": p["code"], "counterparty": p["counterparty"], "scope": p["scope"],
                        "nature": p["nature"], "channel": p["channel"],
                        "start_date": p["start_date"], "end_date": p["end_date"],
                        "n_reports": len(set(p["reports"])),
                        "fee_series": ";".join(f"{k}={v:.2f}" for k, v in sorted(p["fees"]))})

    # screen output: one-screen summary
    print(f"[records] {len(rs)} / {len({r['code'] for r in rs})} firms / "
          f"{len({(r['code'], r['year'], r['kind']) for r in rs})} reports")
    for ch, n in Counter(r["channel"] for r in rs).items():
        print(f"  {ch}: {n} records")
    if ratios:
        vals = [x[0] for x in ratios]
        print(f"[fee/revenue] n={len(vals)} median {100*st.median(vals):.4f}% "
              f"mean {100*st.mean(vals):.4f}% max {100*max(vals):.4f}%")
        print("  top three: " + "; ".join(f"{c} {y} {100*v:.3f}%" for v, c, y in sorted(ratios, reverse=True)[:3]))
    print(f"[term] median {st.median(ds) if ds else 0:.1f} years; distribution " +
          ", ".join(f"{k}={v}" for k, v in dc.items()))
    print(f"[sharing] {len(lad)} records with sharing language; " + ", ".join(f"{k}={v}" for k, v in lab.items()))
    print(f"[Qujiang] {len(qj)} records, 2024H1 fee {qsum/1e4:,.2f} ten-thousand yuan = {100*qsum/h1rev:.2f}% of consolidated revenue")
    for r in qj:
        print(f"   {r['scope'][:24]:24s} {float(r['amount_yuan'])/1e4:10,.2f} 10k CNY  "
              f"of same type {r['pct_same_type']}%  {r['pricing'][:34]}")
    print(f"[agreements] {len(proto)} rows -> data/rq3_protocols.csv")
    print("[detail] data/rq3_descriptive.csv")


if __name__ == "__main__":
    main()