#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge the entrusted-management agreements disclosed in the related-party-transaction
narrative into clause table v4, adding a `channel` column that records the source.

Background: the notes-table section "entrusted management / contracting" contains no
scenic-area targets at all (only hotels, travel agencies, entrusted operation of assets,
equity or operating rights, and ports). Scenic-area operating rights appear only in the
tables embedded in the narrative section "material contracts and their performance ->
other material contracts"; Qujiang Cultural Tourism's 2024 interim report, pp. 36-37, is
such a table (vertical layout, no notes-table structure).

The script does three things:
1. tags the 94 existing notes-table records with `channel` = the value 附注表 (notes table);
2. appends Qujiang's five narrative agreements with `channel` = the value 关联交易正文
   (related-party narrative), where `pct_same_type` holds the disclosed share of same-type
   transaction amount (%). Note that this is NOT a share of operating revenue - do not use
   it as a denominator;
3. backs the original v4 up as contract_terms_v4_annex.csv (kept if already present), so
   that the 94/99 split remains traceable.

Narrative source: data/text/600706_2024H1.txt lines 1916-2085 (PDF pp. 36-37);
PDF at data/raw_pdf/600706_2024H1.pdf, art_code=AN202408231639423764.
Amount unit: yuan (the source prints ten-thousand yuan, multiplied by 10000).

Usage: python code/add_text_contracts.py
"""
import csv
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "contract_terms_v4.csv")
BAK = os.path.join(ROOT, "data", "contract_terms_v4_annex.csv")

ART = "AN202408231639423764"
COL = ["code", "year", "kind", "page", "rec", "counterparty", "operator", "scope",
       "scope_raw", "start_date", "end_date", "pricing", "amount_yuan", "nature",
       "note", "parse_flag", "channel", "pct_same_type"]

TEXT_ROWS = [
    {
        "code": "600706", "year": "2024", "kind": "H1", "page": "36", "rec": "1",
        "counterparty": "西安曲江新区社会事业资产管理中心（已更名为资产管理中心）",
        "operator": "西安曲江文化旅游股份有限公司",
        "scope": "大唐芙蓉园景区",
        "start_date": "2011-01-01", "end_date": "2030-12-31",
        "pricing": "基本酬金=2019年门票收益中的7,986万元（不足则按实际门票收入；此后每三个年度为周期调增）；"
                   "分成酬金超额累进：超基本酬金10%以内无分成、10–20%部分50%、20–30%部分60%、"
                   "30–40%部分70%、40–50%部分80%、50%以上无分成；门票收入由公司直接获取后差额交付委托方",
        "amount_yuan": "25414100",
        "nature": "景区",
        "note": "2020/2021/2022年度管理酬金（含税）13,407.35/13,586.97/12,943.93万元；"
                "2023-01-01至2030-12-31计取模式仍按2010年签订的《大唐芙蓉园委托经营管理协议》执行；"
                "可在景区内开展经营性活动、经营性收入归公司所有；合同约定结算",
        "parse_flag": "from_text_manual", "channel": "关联交易正文", "pct_same_type": "5.23",
    },
    {
        "code": "600706", "year": "2024", "kind": "H1", "page": "37", "rec": "1",
        "counterparty": "西安曲江新区社会事业资产管理中心",
        "operator": "西安曲江文化旅游股份有限公司",
        "scope": "曲江池遗址公园、唐城墙遗址公园",
        "start_date": "2010-11-01", "end_date": "2030-10-31",
        "pricing": "经营性收入分成：第1–5年100%归受托方、第6–10年92%、第11–15年90%、第16–20年88%",
        "amount_yuan": "23595100",
        "nature": "景区",
        "note": "受托方为上市公司本部；委托期限届满在同等条件下有优先续展权；合同约定结算",
        "parse_flag": "from_text_manual", "channel": "关联交易正文", "pct_same_type": "4.86",
    },
    {
        "code": "600706", "year": "2024", "kind": "H1", "page": "37", "rec": "2",
        "counterparty": "西安曲江新区社会事业资产管理中心",
        "operator": "大雁塔景区管理服务有限公司",
        "scope": "大雁塔景区、大唐不夜城景区（含开元广场、银泰广场等）、唐慈恩寺遗址公园",
        "start_date": "2010-11-01", "end_date": "2030-10-31",
        "pricing": "经营性收入分成：第1–5年100%归受托方、第6–10年92%、第11–15年90%、第16–20年88%",
        "amount_yuan": "5112700",
        "nature": "景区",
        "note": "受托方为公司全资子公司；表注：资产管理中心拟调整景区管理模式，双方正在协商该区域2024年管理酬金，"
                "故与上年同期存在差异；合同约定结算",
        "parse_flag": "from_text_manual", "channel": "关联交易正文", "pct_same_type": "1.05",
    },
    {
        "code": "600706", "year": "2024", "kind": "H1", "page": "37", "rec": "3",
        "counterparty": "西安曲江大明宫遗址区保护改造办公室",
        "operator": "曲江大明宫遗址公园公司",
        "scope": "曲江大明宫遗址公园",
        "start_date": "2010-10-01", "end_date": "2030-09-30",
        "pricing": "自2015年6月起年度管理酬金12,810万元（固定额）；可在景区内开展经营性活动、经营活动收入归受托方所有",
        "amount_yuan": "67985000",
        "nature": "景区",
        "note": "受托方为公司全资子公司；2024H1该子公司营业收入6,798.50万元＝全部酬金，净利润−5,941.70万元；合同约定结算",
        "parse_flag": "from_text_manual", "channel": "关联交易正文", "pct_same_type": "14.00",
    },
    {
        "code": "600706", "year": "2024", "kind": "H1", "page": "37", "rec": "4",
        "counterparty": "西安城墙开发管理有限公司",
        "operator": "西安曲江城墙旅游发展有限公司（城墙景区公司）",
        "scope": "西安城墙景区",
        "start_date": "2018-10-01", "end_date": "2023-12-31",
        "pricing": "《委托经营管理协议书》约定（原文未披露酬金计取公式）",
        "amount_yuan": "37515900",
        "nature": "景区",
        "note": "链条两层：城墙管委会授权其全资子公司城墙开发公司全面管理，城墙开发公司再委托城墙景区公司；"
                "表列结束日2023-12-31，但2024H1仍确认酬金3,751.59万元（履约延续，需另核续签）；合同约定结算",
        "parse_flag": "from_text_manual", "channel": "关联交易正文", "pct_same_type": "7.73",
    },
]


def main():
    if not os.path.exists(BAK):
        shutil.copy2(SRC, BAK)
        print(f"[backup] {os.path.basename(BAK)} (original 94-record notes-table version)")
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    for r in rows:
        r.setdefault("channel", "")
        if not r["channel"].strip():
            r["channel"] = "附注表"
        r.setdefault("pct_same_type", "")

    have = {(r["code"], r["year"], r["kind"], r["page"], r["rec"]) for r in rows}
    added = 0
    for t in TEXT_ROWS:
        key = (t["code"], t["year"], t["kind"], t["page"], t["rec"])
        if key in have:
            continue
        rows.append({k: t.get(k, "") for k in COL})
        added += 1

    with open(SRC, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COL, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    c = Counter(r["channel"] for r in rows)
    print(f"[done] {len(rows)} rows -> {SRC} ({added} added this run)")
    for k, v in c.items():
        print(f"  channel={k}: {v} records")
    tot = sum(float(r["amount_yuan"]) for r in rows if r["channel"] == "关联交易正文")
    print(f"  narrative agreements, 2024H1 fee total {tot:,.0f} yuan = {tot/1e4:,.2f} ten-thousand yuan")
    missing = [k for k in COL if rows and k not in rows[0]]
    if missing:
        print(f"[warn] missing columns {missing}", file=sys.stderr)


if __name__ == "__main__":
    main()