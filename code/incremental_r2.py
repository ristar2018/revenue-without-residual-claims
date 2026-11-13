# -*- coding: utf-8 -*-
"""Incremental information test: revenue growth vs the integrated framework (four deduction lines)

Answers reviewer point 1: does the framework do more than re-arrange accounting items, and does
it add information?
Two complementary designs:
  A continuous   g_np ~ g_rev [ + the four deduction lines ]      -- incremental explanatory power (dR2, partial F)
  B categorical  D(decoupled=1) ~ g_rev [ + the four deduction lines ] -- incremental classification (LR test, cross-validated AUC)

Criteria (consistent with rq1_stats.py / rq2_decomp.csv):
  sample   A level: 139 firm-years with both growth and the four lines available; full sample 201
  g_rev    = within-firm revenue, current / previous - 1; g_np the same with net profit
  decoupled = g_rev > 0 and g_np < 0
  winsor   +/-5 (as in the h2 regressions); 1%/99% trimming reported separately

Output: data/incremental_r2.csv (the design column separates A and B)
Exit code: 0 normal; 1 missing input
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "data" / "panel_annual_2015_2025_v2.csv"
DEC = ROOT / "data" / "rq2_decomp.csv"
OUT = ROOT / "data" / "incremental_r2.csv"

BURDENS = ["da_int", "int_burden", "impair", "minority"]


def pct_change(s: pd.Series) -> pd.Series:
    try:
        return s.pct_change(fill_method=None)
    except TypeError:
        return s.pct_change()


def fit_ols(y: np.ndarray, X: np.ndarray):
    Xc = sm.add_constant(X, has_constant="add")
    res = sm.OLS(y, Xc).fit()
    return res


def cv_auc(X: np.ndarray, y: np.ndarray, repeats: int = 20, folds: int = 5) -> tuple[float, float]:
    """Repeated stratified K-fold cross-validated AUC, returned as (mean, sd)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import RepeatedStratifiedKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if len(np.unique(y)) < 2:
        return float("nan"), float("nan")
    rskf = RepeatedStratifiedKFold(n_splits=folds, n_repeats=repeats, random_state=20261112)
    aucs = []
    for tr, te in rskf.split(X, y):
        pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
        pipe.fit(X[tr], y[tr])
        p = pipe.predict_proba(X[te])[:, 1]
        if len(np.unique(y[te])) < 2:
            continue
        aucs.append(roc_auc_score(y[te], p))
    return float(np.mean(aucs)), float(np.std(aucs))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for p in (PANEL, DEC):
        if not p.exists():
            print("missing input:", p)
            return 1

    pan = pd.read_csv(PANEL, dtype={"code": str})
    pan = pan[(pan.year >= 2015) & (pan.year <= 2025)].sort_values(["code", "year"]).copy()
    pan["g_rev"] = pan.groupby("code")["revenue"].transform(pct_change)
    pan["g_np"] = pan.groupby("code")["net_profit"].transform(pct_change)

    dec = pd.read_csv(DEC, dtype={"code": str}).sort_values(["code", "year"]).copy()
    for c in BURDENS:
        dec["d_" + c] = dec.groupby("code")[c].transform(lambda s: s.diff())

    dec = dec.rename(columns={"tier": "tier_d"})
    keep = ["code", "year", "tier_d"] + BURDENS + ["d_" + c for c in BURDENS]
    m = pan.merge(dec[keep], on=["code", "year"], how="inner")

    rows = []

    # ---------- A: continuous criterion ----------
    for label, sub in (("A级", m[m.tier_d == "A"]), ("全样本", m)):
        sub = sub.dropna(subset=["g_rev", "g_np"] + ["d_" + c for c in BURDENS]).copy()
        if len(sub) < 30:
            print(f"[A/{label}] n={len(sub)} too small, skipped")
            continue
        for trim, tag in ((5.0, "winsor5"), (None, "trim1_99")):
            s = sub.copy()
            cols = ["g_rev", "g_np"] + ["d_" + c for c in BURDENS]
            if trim:
                for c in cols:
                    s[c] = s[c].clip(-trim, trim)
            else:
                for c in cols:
                    lo, hi = s[c].quantile([0.01, 0.99])
                    s[c] = s[c].clip(lo, hi)
            y = s["g_np"].to_numpy(float)
            m1 = fit_ols(y, s[["g_rev"]].to_numpy(float))
            m2 = fit_ols(y, s[["g_rev"] + ["d_" + c for c in BURDENS]].to_numpy(float))
            m3 = fit_ols(y, s[["d_" + c for c in BURDENS]].to_numpy(float))
            ssr1, ssr2 = float(m1.ssr), float(m2.ssr)
            df2 = int(m2.df_resid)
            f = ((ssr1 - ssr2) / len(BURDENS)) / (ssr2 / df2)
            p_f = float(1.0 - stats.f.cdf(f, len(BURDENS), df2))
            rows.append(dict(
                design="A_continuous", sample=label, trim=tag, n=len(s),
                r2_revenue_only=round(float(m1.rsquared), 4),
                adj_r2_revenue_only=round(float(m1.rsquared_adj), 4),
                r2_revenue_plus_burdens=round(float(m2.rsquared), 4),
                adj_r2_revenue_plus=round(float(m2.rsquared_adj), 4),
                r2_burdens_only=round(float(m3.rsquared), 4),
                delta_r2=round(float(m2.rsquared - m1.rsquared), 4),
                delta_adj_r2=round(float(m2.rsquared_adj - m1.rsquared_adj), 4),
                partial_f_p=round(p_f, 4),
            ))
            print(f"[A/{label}/{tag}] n={len(s)}  R2(revenue)={m1.rsquared:.4f}  "
                  f"R2(revenue+deductions)={m2.rsquared:.4f}  dR2={m2.rsquared - m1.rsquared:+.4f}  "
                  f"ΔadjR2={m2.rsquared_adj - m1.rsquared_adj:+.4f}  p(F)={p_f:.4f}")

    # ---------- B: categorical criterion ----------
    for label, sub in (("A级", m[m.tier_d == "A"]), ("全样本", m)):
        sub = sub.dropna(subset=["g_rev", "g_np"] + BURDENS).copy()
        sub["D"] = ((sub.g_rev > 0) & (sub.g_np < 0)).astype(int)
        if sub.D.sum() < 10 or len(sub) - sub.D.sum() < 10:
            print(f"[B/{label}] too few groups, skipped (D=1: {sub.D.sum()})")
            continue
        y = sub["D"].to_numpy(int)
        X1 = sub[["g_rev"]].to_numpy(float)
        X2 = sub[["g_rev"] + BURDENS].to_numpy(float)
        X3 = sub[BURDENS].to_numpy(float)

        l1 = sm.Logit(y, sm.add_constant(X1)).fit(disp=0)
        l2 = sm.Logit(y, sm.add_constant(X2)).fit(disp=0)
        l3 = sm.Logit(y, sm.add_constant(X3)).fit(disp=0)
        lr = 2.0 * (l2.llf - l1.llf)
        p_lr = float(1.0 - stats.chi2.cdf(lr, len(BURDENS)))

        a1, s1 = cv_auc(X1, y)
        a2, s2 = cv_auc(X2, y)
        a3, s3 = cv_auc(X3, y)
        rows.append(dict(
            design="B_binary", sample=label, trim="none", n=len(sub),
            n_decoupled=int(y.sum()), base_rate=round(float(y.mean()), 4),
            pseudo_r2_revenue_only=round(float(l1.prsquared), 4),
            pseudo_r2_revenue_plus_burdens=round(float(l2.prsquared), 4),
            pseudo_r2_burdens_only=round(float(l3.prsquared), 4),
            lr_chi2=round(float(lr), 3), lr_p=round(p_lr, 4),
            cv_auc_revenue_only=round(a1, 4), cv_auc_revenue_plus_burdens=round(a2, 4),
            cv_auc_burdens_only=round(a3, 4),
            cv_auc_sd_rev=round(s1, 4), cv_auc_sd_both=round(s2, 4),
        ))
        print(f"[B/{label}] n={len(sub)} decoupled={int(y.sum())} ({y.mean():.1%})  "
              f"pseudoR2(revenue)={l1.prsquared:.4f} (revenue+deductions)={l2.prsquared:.4f}  "
              f"LR p={p_lr:.4f}  CV-AUC revenue={a1:.3f} revenue+deductions={a2:.3f} deductions only={a3:.3f}")

    pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8-sig")
    print("\nwrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
