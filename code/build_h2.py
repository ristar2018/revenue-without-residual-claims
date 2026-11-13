"""H2 (capital burden weakens profit conversion) panel: variable construction + two-way fixed-effects regressions.

Data sources (all on disk, no network):
  data/fin_panel.csv            24 firms x FY2020-2024 consolidated statement items (yuan)
  data/cashflow_panel.csv       cash-flow-statement basis: cfo / capex / dep_fa / am_ia_cf / am_lt_cf
  data/panel_annual_2015_2025_v2.csv  vendor revenue / parent net profit / ROE (tier assignment and year alignment)

Variables (all scaled by operating revenue so that scale effects do not dominate):
  net_margin  = np_parent / revenue          net margin (profit conversion)
  cfo_margin  = cfo / revenue                cash conversion
  da_int      = (dep_fa + am_ia_cf + am_lt_cf) / revenue   depreciation and amortisation burden
  int_burden  = int_exp / revenue            interest burden
  debt_stock  = (st_loan + lt_loan + bond + ncl_due1y) / revenue   interest-bearing debt intensity
  long_assets = (fa + ia + cip + rou) / revenue                    long-term asset intensity
  impair      = (|asset_imp| + |credit_imp|) / revenue             impairment burden
  capex_int   = capex / revenue              capital expenditure intensity
  profit_gap  = net_margin - cfo_margin      divergence between book profit and cash

Regressions (LSDV: firm fixed effects + year fixed effects, firm-clustered robust SEs):
  (1) net_margin ~ da_int + int_burden + impair   -- H2 main test
  (2) cfo_margin ~ da_int + int_burden + impair   -- cash-basis comparison
  (3) net_margin ~ debt_stock + long_assets + impair -- capital-commitment stock
Sample: mainly the 17 A-level firms x 5 years; the full 24-firm sample is used for robustness.

Scaling warning: every denominator is operating revenue, so observations with revenue near
zero are inflated; the first part of the output prints quantiles, observations with
|ratio| > 5 are counted separately and winsorised to 5 in the winsorised regressions.
"""
import csv
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
OUT_PANEL = os.path.join(D, "h2_panel.csv")
OUT_RES = os.path.join(D, "h2_results.csv")

TIER = {
    "600054": "A", "000888": "A", "002033": "A", "603199": "A", "603099": "A",
    "603136": "A", "000430": "A", "600593": "A", "000978": "A", "600749": "A",
    "002159": "A", "300859": "A", "300144": "A", "600706": "A", "600576": "A",
    "002059": "A", "002627": "A",
    "000069": "B", "600138": "B", "600358": "B", "000863": "B",
    "000524": "C", "002707": "C", "000721": "C",
}


def load(name):
    p = os.path.join(D, name)
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def f(x):
    try:
        s = (x or "").strip()
        return float(s) if s else None
    except ValueError:
        return None


def main():
    fin = load("fin_panel.csv")
    cf = {(r["code"], r["year"], r["kind"]): r for r in load("cashflow_panel.csv")}
    em = {(r["code"], r["year"]): r for r in load("panel_annual_2015_2025_v2.csv")}

    rows = []
    for r in fin:
        code, year = r["code"], r["year"]
        rev = f(r["revenue"]) or f(r["total_revenue"])
        if not rev:
            continue
        c = cf.get((code, year, "A"), {})
        np_ = f(r["np_parent"])
        if np_ is None:
            np_ = f(r["net_profit"])
        da = sum(v for v in (f(c.get("dep_fa")), f(c.get("am_ia_cf")), f(c.get("am_lt_cf"))) if v is not None)
        debt = sum(v for v in (f(r["st_loan"]), f(r["lt_loan"]), f(r["bond"]), f(r["ncl_due1y"])) if v is not None)
        la = sum(v for v in (f(r["fa"]), f(r["ia"]), f(r["cip"]), f(r["rou"])) if v is not None)
        imp = sum(abs(v) for v in (f(r["asset_imp"]), f(r["credit_imp"])) if v is not None)

        def ratio(x):
            return "" if x is None else f"{x:.6f}"

        rows.append({
            "code": code, "year": year, "tier": TIER.get(code, "?"),
            "revenue": f"{rev:.2f}",
            "net_margin": ratio(None if np_ is None else np_ / rev),
            "cfo_margin": ratio(None if f(c.get("cfo")) is None else f(c.get("cfo")) / rev),
            "da_int": ratio(da / rev if da else None),
            "int_burden": ratio(None if f(r["int_exp"]) is None else abs(f(r["int_exp"])) / rev),
            "debt_stock": ratio(debt / rev if debt else None),
            "long_assets": ratio(la / rev if la else None),
            "impair": ratio(imp / rev if imp else None),
            "capex_int": ratio(None if f(c.get("capex")) is None else abs(f(c.get("capex"))) / rev),
            "turnover": ratio(rev / la if la else None),
            "cfo": c.get("cfo", ""),
            "roa_proxy": ratio(None if np_ is None else np_ / (la or rev)),
        })

    assert len(rows) >= 200, f"expected more than 200 firm-years (2015-2024), got {len(rows)}"
    for r in rows:
        r["profit_gap"] = ("" if r["net_margin"] == "" or r["cfo_margin"] == ""
                           else f"{float(r['net_margin']) - float(r['cfo_margin']):.6f}")

    keys = ["code", "year", "tier", "revenue", "net_margin", "cfo_margin", "profit_gap",
            "da_int", "int_burden", "debt_stock", "long_assets", "turnover", "impair", "capex_int", "roa_proxy", "cfo"]
    with open(OUT_PANEL, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"[ok] {len(rows)} rows -> {OUT_PANEL}")

    # Distribution and outlier counts
    def col(k):
        return [float(r[k]) for r in rows if r[k] != ""]

    print("\n[quantiles] variable | n | p10 | median | p90 | count |x|>5")
    for k in ("net_margin", "cfo_margin", "da_int", "int_burden", "debt_stock",
              "long_assets", "impair", "capex_int", "profit_gap"):
        v = sorted(col(k))
        n = len(v)
        q = lambda p: v[min(n - 1, int(p * (n - 1)))]
        big = sum(1 for x in v if abs(x) > 5)
        print(f"  {k:12s} {n:3d} {q(.1):9.4f} {q(.5):9.4f} {q(.9):9.4f}   {big}")

    # ---- regressions ----
    try:
        import numpy as np
        import statsmodels.api as sm
    except Exception as e:  # pragma: no cover
        print(f"[skip] numpy/statsmodels not available: {e}")
        return

    def run(dep, indep, sample, label, winsor=5.0, year_fe=True):
        sub = [r for r in rows if sample(r)]
        sub = [r for r in sub if r[dep] != "" and all(r[k] != "" for k in indep)]
        if len(sub) < 30:
            print(f"  [{label}] n={len(sub)} too small, skipped")
            return None
        y = np.array([float(r[dep]) for r in sub])
        X = np.array([[float(r[k]) for k in indep] for r in sub])
        if winsor:
            X = np.clip(X, -winsor, winsor)
            y = np.clip(y, -winsor, winsor)
        firms = sorted({r["code"] for r in sub})
        years = sorted({r["year"] for r in sub})
        ny = len(years) - 1 if year_fe else 0
        Dm = np.zeros((len(sub), len(firms) - 1 + ny))
        for i, r in enumerate(sub):
            fi = firms.index(r["code"])
            yi = years.index(r["year"])
            if fi > 0:
                Dm[i, fi - 1] = 1.0
            if year_fe and yi > 0:
                Dm[i, len(firms) - 1 + yi - 1] = 1.0
        Xf = sm.add_constant(np.hstack([X, Dm]))
        groups = [r["code"] for r in sub]
        fit = sm.OLS(y, Xf).fit(cov_type="cluster", cov_kwds={"groups": groups})
        out = []
        for j, k in enumerate(indep):
            out.append({
                "spec": label, "n": len(sub), "dep": dep, "var": k,
                "coef": f"{fit.params[1 + j]:.6f}",
                "se": f"{fit.bse[1 + j]:.6f}",
                "t": f"{fit.tvalues[1 + j]:.3f}",
                "p": f"{fit.pvalues[1 + j]:.4f}",
                "r2_within_proxy": f"{fit.rsquared:.4f}",
            })
        print(f"\n  [{label}] n={len(sub)} firms={len(firms)} R2={fit.rsquared:.3f}")
        for o in out:
            print(f"    {o['var']:12s} {float(o['coef']):+9.4f}  se={float(o['se']):7.4f}  t={o['t']:>7s}  p={o['p']}")
        return out

    isA = lambda r: r["tier"] == "A"
    allf = lambda r: True

    # Variance decomposition: DA intensity is a 'sticky' item; if within-firm variation is far below between-firm variation, the within estimator is unreliable
    print("\n[variance decomposition] variable | between sd | within sd | within/between")
    for k in ("da_int", "int_burden", "debt_stock", "long_assets", "impair", "capex_int"):
        bt, wi = [], []
        for code in {r["code"] for r in rows}:
            sub = [float(r[k]) for r in rows if r["code"] == code and r[k] != ""]
            if len(sub) >= 2:
                m = sum(sub) / len(sub)
                bt.append(m)
                wi.extend(x - m for x in sub)
        if not bt:
            continue
        def sd(v):
            m = sum(v) / len(v)
            return (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5
        print(f"  {k:12s} {sd(bt):8.4f} {sd(wi):8.4f}   {sd(wi) / sd(bt):.2f}")

    res = []
    for sample, sname in ((isA, "A级"), (allf, "全样本")):
        for dep in ("net_margin", "cfo_margin"):
            res += (run(dep, ["da_int", "int_burden", "impair"], sample, f"{sname}|{dep}|负担流量") or [])
        res += (run("net_margin", ["debt_stock", "long_assets", "impair"], sample,
                    f"{sname}|net_margin|承诺存量") or [])
        res += (run("profit_gap", ["da_int", "int_burden"], sample, f"{sname}|profit_gap") or [])
        res += (run("net_margin", ["turnover", "int_burden", "impair"], sample,
                    f"{sname}|net_margin|周转口径") or [])

    # Robustness: how the main test behaves under three perturbations (year effects dropped / pandemic years dropped / two leverage points dropped)
    print("\n[robustness] A level: net_margin ~ da_int + int_burden + impair")
    for tag, sample, yfe in (
        ("去掉年份效应", isA, False),
        ("剔除2022年", lambda r: isA(r) and r["year"] != "2022", True),
        ("剔除300144/000430", lambda r: isA(r) and r["code"] not in ("300144", "000430"), True),
    ):
        res += (run("net_margin", ["da_int", "int_burden", "impair"], sample,
                    f"A级|net_margin|{tag}", year_fe=yfe) or [])

    if res:
        with open(OUT_RES, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
            w.writeheader()
            w.writerows(res)
        print(f"\n[ok] {len(res)} coefficients -> {OUT_RES}")


if __name__ == "__main__":
    main()
