# -*- coding: utf-8 -*-
"""RQ1 prevalence: level decoupling, the four cells of growth decoupling, A/B/C tiers, two correlations.

Data: data/panel_annual_2015_2025_v2.csv (24 firms x 11 years = 264 firm-years)

Criteria (digit-for-digit identical to the numbers already written in 01 sections 167-169 and 03
section 4.1; hard-coded as assertions):
- Level decoupling = corr(revenue level, profit level) over all valid observations (187 A-level rows).
- Growth = within-firm current / previous - 1 (pct_change), computed only for adjacent years of the
  same firm.
- The four growth cells are defined by the SIGN of growth (revenue up & profit down is the decoupled
  cell); the denominator is the observations where both growth rates are computable (A level 170 =
  187 - 17 first years; full sample 240 = 264 - 24).
- Two correlations = corr(levels) and corr(growth).

Why not the two other common constructions (they fail empirically, see the comment under
if __name__ == at the end of the file):
- sign of absolute differences: A level 27/170 = 15.9%, full sample 39/240 = 16.2%, which does not
  match the literature;
- vendor rev_yoy / np_yoy columns: corr(growth) 0.102 at A level and 0.118 in the full sample, and
  187/264 rows carry a value (first years included).

Output: data/rq1_stats.csv (one row per tier) and the four-cell distribution printed to stdout.
Exit code: 0 all assertions pass; 1 any number differs (expected and actual printed line by line).

2026-11-11 criterion fix (audit finding F-07): the 2015 row of 000524 (Lingnan Holdings, C level)
originally took pre-restatement revenue 305,819,618.85 and net profit 39,231,704.18, while the 2016
row took the 2017 annual report figures after retrospective adjustment (5,819,329,368.95 /
136,562,681.86), crossing the retrospective boundary of a business combination under common control.
The 2015 row in data/panel_annual_2015_2025_v2.csv is now the restated 5,649,685,860.22 /
139,022,117.64; the correction is recorded in the study audit log under F-07. A/B levels are
unaffected; the expected values for the full sample and C level have been updated accordingly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "data" / "panel_annual_2015_2025_v2.csv"
OUT = ROOT / "data" / "rq1_stats.csv"

EXPECT = {
    "A": dict(firms=17, obs=187, growth_n=170, decoup=45, pct=26.5, corr_level=0.552, corr_growth=0.129),
    "B": dict(firms=4, obs=44, growth_n=40, decoup=12, pct=30.0, corr_level=0.180, corr_growth=0.251),
    "C": dict(firms=3, obs=33, growth_n=30, decoup=11, pct=36.7, corr_level=0.459, corr_growth=0.129),
    "全样本": dict(firms=24, obs=264, growth_n=240, decoup=68, pct=28.3, corr_level=0.198, corr_growth=0.118),
}
CELLS = [("up_up", "营收↑利润↑"), ("up_dn", "营收↑利润↓"), ("dn_up", "营收↓利润↑"), ("dn_dn", "营收↓利润↓")]
EXPECT_CELLS_ALL = {"up_up": 70, "up_dn": 68, "dn_up": 27, "dn_dn": 75}


def pct_change(series: pd.Series) -> pd.Series:
    try:
        return series.pct_change(fill_method=None)
    except TypeError:  # pandas < 2.1
        return series.pct_change()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    df = pd.read_csv(PANEL, dtype={"code": str})
    need = {"code", "tier", "year", "revenue", "net_profit"}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(f"panel is missing columns: {sorted(missing)}")

    df = df[(df.year >= 2015) & (df.year <= 2025)].copy()
    df = df.sort_values(["code", "year"])
    df["rev"] = df.revenue / 1e4
    df["np"] = df.net_profit / 1e4
    g = df.groupby("code", group_keys=False)
    df["g_rev"] = g["rev"].apply(pct_change)
    df["g_np"] = g["np"].apply(pct_change)
    df.loc[~np.isfinite(df.g_rev), "g_rev"] = np.nan
    df.loc[~np.isfinite(df.g_np), "g_np"] = np.nan

    print(f"panel: {len(df)} rows / {df.code.nunique()} firms / {int(df.year.min())}-{int(df.year.max())}")
    assert len(df) == 264 and df.code.nunique() == 24, "panel size does not match 24 x 11"

    failures: list[str] = []
    rows: list[dict] = []

    def check(name: str, exp, act) -> None:
        ok = (abs(float(exp) - float(act)) < 1e-9) if isinstance(exp, int) else (abs(exp - act) < 5e-4)
        print(f"  [{'ok' if ok else 'FAIL'}] {name}: {act} (expected {exp})")
        if not ok:
            failures.append(f"{name}: actual {act} / expected {exp}")

    for scope in ["A", "B", "C", "全样本"]:
        s = df if scope == "全样本" else df[df.tier == scope]
        e = EXPECT[scope]
        q = s.dropna(subset=["g_rev", "g_np"])
        cells = {
            "up_up": int(((q.g_rev > 0) & (q.g_np > 0)).sum()),
            "up_dn": int(((q.g_rev > 0) & (q.g_np < 0)).sum()),
            "dn_up": int(((q.g_rev < 0) & (q.g_np > 0)).sum()),
            "dn_dn": int(((q.g_rev < 0) & (q.g_np < 0)).sum()),
        }
        lvl = s.dropna(subset=["rev", "np"])
        corr_level = round(float(lvl.rev.corr(lvl.np)), 3)
        corr_growth = round(float(q.g_rev.corr(q.g_np)), 3)
        decoup_pct = round(cells["up_dn"] / len(q) * 100, 1)

        print(f"\n[{scope}]")
        check(f"{scope} firms", e["firms"], int(s.code.nunique()))
        check(f"{scope} observations", e["obs"], len(s))
        check(f"{scope} growth observations", e["growth_n"], len(q))
        check(f"{scope} decoupled count (growth)", e["decoup"], cells["up_dn"])
        check(f"{scope} decoupled share %", e["pct"], decoup_pct)
        check(f"{scope} corr levels", e["corr_level"], corr_level)
        check(f"{scope} corr growth", e["corr_growth"], corr_growth)

        rows.append(dict(
            scope=scope, firms=int(s.code.nunique()), obs=len(s), growth_n=len(q),
            n_up_dn=cells["up_dn"], pct_up_dn=decoup_pct,
            corr_level=corr_level, corr_growth=corr_growth,
            up_up=cells["up_up"], up_dn=cells["up_dn"],
            dn_up=cells["dn_up"], dn_dn=cells["dn_dn"],
        ))

    print("\n[four-cell distribution - full sample]")
    allq = df.dropna(subset=["g_rev", "g_np"])
    for key, label in CELLS:
        n = int(({
            "up_up": (allq.g_rev > 0) & (allq.g_np > 0),
            "up_dn": (allq.g_rev > 0) & (allq.g_np < 0),
            "dn_up": (allq.g_rev < 0) & (allq.g_np > 0),
            "dn_dn": (allq.g_rev < 0) & (allq.g_np < 0),
        }[key]).sum())
        pct = round(n / len(allq) * 100, 1)
        check(f"cell {label}", EXPECT_CELLS_ALL[key], n)
        print(f"       {label}: {n} ({pct}%)")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"\nwrote {OUT.relative_to(ROOT)}")

    if failures:
        print(f"\n[FAIL] {len(failures)} checks did not match:")
        for f in failures:
            print("  -", f)
        return 1
    print("\n[PASS] every RQ1 number matches the value already written in 01/03 digit for digit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
