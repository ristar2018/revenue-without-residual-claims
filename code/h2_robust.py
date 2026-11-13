# -*- coding: utf-8 -*-
"""Inference robustness for the H2 main test (reviewer point 9: only 17 firm clusters).

The specification tested is identical to build_h2.py:
    net_margin ~ da_int + int_burden + impair
    firm fixed effects + year fixed effects (LSDV), +/-5 winsorisation at both ends, 17 A-level firms
Baseline: firm-clustered robust standard errors (CR1)

Four additional inference routes:
  (1) CR2 (Imbens-Kolesar bias-reduced linearisation) standard errors
  (2) wild cluster bootstrap-t, Rademacher weights, 999 replications, null imposed (WCR)
  (3) leave-one-firm-out (17 runs), to see whether the coefficient range and significance are driven by one firm
  (4) main specification with capex_int added (rules out the 'scale of capital expenditure' alternative)

Output: data/h2_robust.csv
Exit code: 0 normal; 1 missing input
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "data" / "h2_panel.csv"
OUT = ROOT / "data" / "h2_robust.csv"

DEP = "net_margin"
MAIN = ["da_int", "int_burden", "impair"]
SEED = 20261112
REPS = 999
WINSOR = 5.0


def load_rows(add_capex: bool = False):
    df = pd.read_csv(PANEL, dtype={"code": str, "year": str})
    df = df[df.tier == "A"].copy()
    indep = MAIN + (["capex_int"] if add_capex else [])
    need = [DEP] + indep
    df = df.dropna(subset=need)
    for c in need:
        df[c] = df[c].astype(float).clip(-WINSOR, WINSOR)
    return df, indep


def design(df: pd.DataFrame, indep: list[str]):
    """LSDV: constant + regressors + firm dummies (first firm dropped) + year dummies (first year dropped)."""
    firms = sorted(df.code.unique())
    years = sorted(df.year.unique())
    D = []
    for _, r in df.iterrows():
        fi = firms.index(r.code)
        yi = years.index(r.year)
        row = [1.0 if fi > 0 and fi - 1 == k else 0.0 for k in range(len(firms) - 1)]
        row += [1.0 if yi > 0 and yi - 1 == k else 0.0 for k in range(len(years) - 1)]
        D.append(row)
    X = np.column_stack([np.ones(len(df)), df[indep].to_numpy(float), np.array(D)])
    y = df[DEP].to_numpy(float)
    return y, X, list(df.code)


def cr1_se(X: np.ndarray, u: np.ndarray, groups: list[str], small_sample: bool = True) -> np.ndarray:
    """CR1 clustered robust standard errors; with small_sample=True the statsmodels correction
    sqrt(G/(G-1) * (n-1)/(n-k)) is applied so that the standard errors match the manuscript digit by digit."""
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    g = np.array(groups)
    for c in np.unique(g):
        m = g == c
        s = X[m].T @ u[m]
        meat += np.outer(s, s)
    V = XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.maximum(np.diag(V), 0.0))
    if small_sample:
        G, n, k = len(np.unique(g)), X.shape[0], X.shape[1]
        se = se * np.sqrt(G / (G - 1) * (n - 1) / (n - k))
    return se


def cr2_se(X: np.ndarray, u: np.ndarray, groups: list[str]) -> np.ndarray:
    """Imbens-Kolesar CR2: residuals adjusted by (I - H_gg)^{-1/2} for each cluster."""
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    g = np.array(groups)
    for c in np.unique(g):
        m = g == c
        Xg, ug = X[m], u[m]
        Hgg = Xg @ XtX_inv @ Xg.T
        ev, V = np.linalg.eigh(np.eye(len(ug)) - Hgg)
        ev = np.maximum(ev, 1e-8)
        A = V @ np.diag(ev ** -0.5) @ V.T
        s = Xg.T @ (A @ ug)
        meat += np.outer(s, s)
    Vm = XtX_inv @ meat @ XtX_inv
    return np.sqrt(np.maximum(np.diag(Vm), 0.0))


def ols(y: np.ndarray, X: np.ndarray):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b, y - X @ b


def wild_bootstrap(y, X, groups, j: int, t_obs: float, reps: int = REPS, seed: int = SEED):
    """Wild cluster bootstrap-t with the null imposed (WCR), Rademacher weights."""
    rng = np.random.default_rng(seed)
    keep = [k for k in range(X.shape[1]) if k != j]
    Xr = X[:, keep]
    br, _ = ols(y, Xr)
    ur = y - Xr @ br                       # constrained residuals
    g = np.array(groups)
    uniq = np.unique(g)
    cnt = 0
    for _ in range(reps):
        w = rng.choice([-1.0, 1.0], size=len(uniq))
        wmap = dict(zip(uniq, w))
        wv = np.array([wmap[c] for c in g])
        ystar = Xr @ br + ur * wv
        bstar, ustar = ols(ystar, X)
        se = cr1_se(X, ustar, groups)
        if se[j] <= 0:
            continue
        if abs(bstar[j] / se[j]) >= abs(t_obs):
            cnt += 1
    return cnt / reps


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not PANEL.exists():
        print("missing input:", PANEL)
        return 1

    df, indep = load_rows()
    y, X, groups = design(df, indep)
    b, u = ols(y, X)
    se1 = cr1_se(X, u, groups)
    se2 = cr2_se(X, u, groups)
    names = ["const"] + indep + ["FE"]
    out = []

    print(f"[baseline] n={len(y)}  firms={df.code.nunique()}  parameters={X.shape[1]}")
    print(f"{'variable':12s} {'coef':>9s} {'CR1 se':>8s} {'t':>7s} {'p':>7s} {'CR2 se':>8s} {'t':>7s}")
    from scipy import stats as st
    G = df.code.nunique()
    for k, v in enumerate(indep, start=1):
        t1 = b[k] / se1[k]
        t2 = b[k] / se2[k]
        dfree = G - 1
        p1 = 2 * (1 - st.norm.cdf(abs(t1)))          # manuscript convention: normal approximation
        p1t = 2 * (1 - st.t.cdf(abs(t1), dfree))     # more conservative: t(G-1)
        p2 = 2 * (1 - st.t.cdf(abs(t2), dfree))
        print(f"{v:12s} {b[k]:+9.4f} {se1[k]:8.4f} {t1:+7.3f} {p1:7.4f} "
              f"(t16 {p1t:6.4f})  {se2[k]:8.4f} {t2:+7.3f} ({p2:.4f})")
        out.append(dict(test="baseline_CR1", var=v, coef=round(b[k], 4), se=round(se1[k], 4),
                        t=round(t1, 3), p=round(p1, 4), n=len(y), G=G))
        out.append(dict(test="baseline_CR1_tG1", var=v, coef=round(b[k], 4), se=round(se1[k], 4),
                        t=round(t1, 3), p=round(p1t, 4), n=len(y), G=G))
        out.append(dict(test="CR2", var=v, coef=round(b[k], 4), se=round(se2[k], 4),
                        t=round(t2, 3), p=round(p2, 4), n=len(y), G=G))

    print("\n[wild cluster bootstrap-t] 999 replications, Rademacher weights, null imposed")
    for k, v in enumerate(indep, start=1):
        t1 = b[k] / se1[k]
        p_wb = wild_bootstrap(y, X, groups, k, t1)
        print(f"  {v:12s} t={t1:+.3f}  p_boot={p_wb:.3f}")
        out.append(dict(test="wild_cluster_bootstrap", var=v, coef=round(b[k], 4),
                        se=round(se1[k], 4), t=round(t1, 3), p=round(p_wb, 3),
                        n=len(y), G=G))

    print("\n[leave-one-firm-out] 17 runs")
    for k, v in enumerate(indep, start=1):
        ests, sig = [], 0
        for c in sorted(df.code.unique()):
            sub = df[df.code != c]
            ys, Xs, gs = design(sub, indep)
            bs, us = ols(ys, Xs)
            ses = cr1_se(Xs, us, gs)
            tt = bs[k] / ses[k]
            ests.append(bs[k])
            if abs(tt) >= 2.0:
                sig += 1
        ests = np.array(ests)
        print(f"  {v:12s} range[{ests.min():+.4f}, {ests.max():+.4f}]  "
              f"median {np.median(ests):+.4f}  same sign {int((np.sign(ests) == np.sign(b[k])).sum())}/17  "
              f"rounds with |t|>=2: {sig}/17")
        out.append(dict(test="leave_one_firm_out", var=v, coef=round(float(np.median(ests)), 4),
                        se="", t="", p=f"{sig}/17", n=len(y) - 6, G=G - 1))
        out.append(dict(test="loo_range", var=v, coef=round(float(ests.min()), 4),
                        se=round(float(ests.max()), 4), t="", p="", n=len(y), G=G))

    print("\n[with capex_int added as a control]")
    df2, indep2 = load_rows(add_capex=True)
    y2, X2, g2 = design(df2, indep2)
    b2, u2 = ols(y2, X2)
    se2b = cr1_se(X2, u2, g2)
    for k, v in enumerate(indep2, start=1):
        t2 = b2[k] / se2b[k]
        p2 = 2 * (1 - st.norm.cdf(abs(t2)))
        p2t = 2 * (1 - st.t.cdf(abs(t2), G - 1))
        print(f"  {v:12s} {b2[k]:+9.4f}  se={se2b[k]:7.4f}  t={t2:+6.3f}  "
              f"p={p2:.4f} (t16 {p2t:.4f})  (n={len(y2)})")
        out.append(dict(test="with_capex_control", var=v, coef=round(b2[k], 4), se=round(se2b[k], 4),
                        t=round(t2, 3), p=round(p2, 4), n=len(y2), G=G))

    print("\n[split samples] the new financial instruments and new leasing standards took effect in 2019, so measurement is not comparable across the break")
    for tag, lo, hi in (("2015-2018", "2015", "2018"), ("2019-2024", "2019", "2024"),
                        ("全期", "2015", "2024")):
        sub = df[(df.year >= lo) & (df.year <= hi)]
        if len(sub) < 40:
            print(f"  {tag}: n={len(sub)} too small")
            continue
        ys, Xs, gs = design(sub, indep)
        bs, us = ols(ys, Xs)
        ses = cr1_se(Xs, us, gs)
        parts = []
        for k, v in enumerate(indep, start=1):
            tk = bs[k] / ses[k]
            pk = 2 * (1 - st.norm.cdf(abs(tk)))
            parts.append(f"{v}={bs[k]:+.3f}(t={tk:+.2f},p={pk:.3f})")
            out.append(dict(test=f"period_{tag}", var=v, coef=round(bs[k], 4), se=round(ses[k], 4),
                            t=round(tk, 3), p=round(pk, 4), n=len(ys), G=sub.code.nunique()))
        print(f"  {tag}: n={len(ys)} firms={sub.code.nunique()}  " + "  ".join(parts))

    pd.DataFrame(out).to_csv(OUT, index=False, encoding="utf-8-sig")
    print("\nwrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
