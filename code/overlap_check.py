# -*- coding: utf-8 -*-
"""Mechanical-overlap diagnostics (reviewer point 3: is the framework only an accounting re-arrangement?).

Three checks, all computed from existing data, no new collection:
  (1) identity closure: is net_margin exactly adj_margin minus the four deduction lines (residual
      magnitude)? If so, 'explaining the gap with the four lines' is an identity and cannot serve as
      causal or explanatory evidence.
  (2) R2 of regressing gap on the four lines (should be about 1) and the correlation of gap with each
      single line - showing that 'divergence' and 'burden' are not two independent objects but two
      readings of the same set of numbers.
  (3) variance inflation factors and the correlation matrix of the three regressors in the main test -
      showing that the main test is not pseudo-significant through collinearity.

Output: data/overlap_check.csv
Exit code: 0 normal; 1 missing input
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEC = ROOT / "data" / "rq2_decomp.csv"
H2 = ROOT / "data" / "h2_panel.csv"
OUT = ROOT / "data" / "overlap_check.csv"

FOUR = ["minority", "int_burden", "impair", "da_int"]


def vif(X: np.ndarray) -> list[float]:
    out = []
    for j in range(X.shape[1]):
        y = X[:, j]
        Z = np.column_stack([np.ones(len(X)), np.delete(X, j, axis=1)])
        b, *_ = np.linalg.lstsq(Z, y, rcond=None)
        r = y - Z @ b
        r2 = 1.0 - float(r @ r) / float(((y - y.mean()) ** 2).sum())
        out.append(1.0 / max(1e-12, 1.0 - r2))
    return out


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for p in (DEC, H2):
        if not p.exists():
            print("missing input:", p)
            return 1

    d = pd.read_csv(DEC, dtype={"code": str, "year": str})
    for c in ["net_margin", "adj_margin"] + FOUR:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    comp = d[d.complete.astype(str).str.lower() == "true"].copy()
    comp["resid"] = comp.net_margin - (comp.adj_margin - comp[FOUR].sum(axis=1))
    rows = []

    print(f"[identity] complete cases n={len(comp)} (whole table {len(d)})")
    print(f"  residual |max|={comp.resid.abs().max():.3e}  mean={comp.resid.mean():+.3e}  "
          f"|残差|>1e-9 的条数={int((comp.resid.abs() > 1e-9).sum())}")
    rows.append(dict(check="identity_residual_max_abs", value=float(comp.resid.abs().max()),
                     n=len(comp), note="net_margin - (adj_margin - four burdens)"))
    rows.append(dict(check="identity_residual_gt_1e-9", value=int((comp.resid.abs() > 1e-9).sum()),
                     n=len(comp), note="应为 0"))

    # regress gap on the four deduction lines
    gap = comp.net_margin - comp.adj_margin
    X = comp[FOUR].to_numpy(float)
    Z = np.column_stack([np.ones(len(X)), X])
    b, *_ = np.linalg.lstsq(Z, gap.to_numpy(float), rcond=None)
    r = gap.to_numpy(float) - Z @ b
    r2 = 1.0 - float(r @ r) / float(((gap - gap.mean()) ** 2).sum())
    print(f"\n[overlap] gap = net_margin - adj_margin regressed on the four deduction lines: R2={r2:.6f}")
    rows.append(dict(check="gap_on_four_R2", value=round(r2, 6), n=len(comp),
                     note="≈1 表示恒等式，不能作解释性证据"))

    print("  correlation of gap with each single deduction line:")
    for c in FOUR:
        cc = float(np.corrcoef(gap, comp[c])[0, 1])
        print(f"    {c:12s} r={cc:+.3f}")
        rows.append(dict(check=f"corr_gap_{c}", value=round(cc, 4), n=len(comp), note="Pearson"))

    # collinearity in the main test
    h = pd.read_csv(H2, dtype={"code": str, "year": str})
    h = h[h.tier == "A"].copy()
    for c in ["net_margin", "da_int", "int_burden", "impair"]:
        h[c] = pd.to_numeric(h[c], errors="coerce")
    s = h.dropna(subset=["net_margin", "da_int", "int_burden", "impair"])
    M = s[["da_int", "int_burden", "impair"]].to_numpy(float)
    print(f"\n[collinearity] main test n={len(s)}  VIF:")
    for c, v in zip(["da_int", "int_burden", "impair"], vif(M)):
        print(f"    {c:12s} VIF={v:.2f}")
        rows.append(dict(check=f"vif_{c}", value=round(float(v), 3), n=len(s), note="raw regressors"))
    C = np.corrcoef(M.T)
    print("  correlation matrix:")
    print("            " + "".join(f"{c:>12s}" for c in ["da_int", "int_burden", "impair"]))
    for i, c in enumerate(["da_int", "int_burden", "impair"]):
        print(f"    {c:12s}" + "".join(f"{C[i, j]:+12.3f}" for j in range(3)))
        for j, c2 in enumerate(["da_int", "int_burden", "impair"]):
            rows.append(dict(check=f"corr_{c}_{c2}", value=round(float(C[i, j]), 4), n=len(s), note="Pearson"))

    pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8-sig")
    print("\nwrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
