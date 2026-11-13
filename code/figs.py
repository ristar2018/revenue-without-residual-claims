# -*- coding: utf-8 -*-
"""Manuscript figures 1-6 (08 section 6, list of exhibits).

Usage:
    python code/figs.py            # all
    python code/figs.py --only 2 3 # selected figures

Writes figures/figN_*.pdf (vector) and .png of the same name (300 dpi, for visual checks),
plus figures/fig_manifest.csv. Every number is recomputed from data/; the assertions inside the
script must match the load-bearing numbers in 03/07/08 and the script aborts instead of plotting
when they do not.
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
MM = 1.0 / 25.4
W1, W2 = 90.0, 174.0          # single column / double column (mm)
MIN_PT = 7.0                  # smallest font size inside a figure

# Okabe-Ito colour-blind-safe palette
C = dict(blue="#0072B2", orange="#E69F00", green="#009E73", verm="D55E00",
         purple="#CC79A7", sky="#56B4E9", yellow="#F0E442", grey="#7F7F7F")
C["verm"] = "#D55E00"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["SimSun", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "xtick.labelsize": MIN_PT,
    "ytick.labelsize": MIN_PT,
    "legend.fontsize": MIN_PT,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "figure.dpi": 150,
    "savefig.bbox": None,
    "savefig.pad_inches": 0.02,
})

MF = os.path.join(FIG, "fig_manifest.csv")


def load():
    pan = pd.read_csv(os.path.join(D, "panel_annual_2015_2025_v2.csv"), dtype={"code": str})
    pan["rg"] = pan.sort_values(["code", "year"]).groupby("code")["revenue"].pct_change(fill_method=None) * 100
    pan["ng"] = pan.sort_values(["code", "year"]).groupby("code")["net_profit"].pct_change(fill_method=None) * 100
    return pan


def save(fig, stem, w_mm, h_mm, note):
    os.makedirs(FIG, exist_ok=True)
    pdf = os.path.join(FIG, stem + ".pdf")
    png = os.path.join(FIG, stem + ".png")
    fig.savefig(pdf)
    fig.savefig(png, dpi=300)
    plt.close(fig)
    raw = open(pdf, "rb").read()
    i = raw.rfind(b"/MediaBox")
    assert i > 0, "no MediaBox in " + pdf
    seg = raw[i:i + 200].split(b"]")[0].split(b"[")[-1].split()
    pw, ph = float(seg[2]) / 72.0 * 25.4, float(seg[3]) / 72.0 * 25.4
    assert abs(pw - w_mm) < 0.8 and abs(ph - h_mm) < 1.2, (stem, pw, ph, w_mm, h_mm)
    rows = []
    if os.path.exists(MF):
        rows = [r for r in pd.read_csv(MF).to_dict("records") if r["file"] != stem]
    rows.append(dict(file=stem, width_mm=round(pw, 1), height_mm=round(ph, 1),
                     design_w_mm=w_mm, design_h_mm=h_mm, min_font_pt=MIN_PT, note=note))
    pd.DataFrame(rows).to_csv(MF, index=False, encoding="utf-8-sig")
    print("[ok] %s  measured %.1f x %.1f mm (design %.0f x %.0f)" % (stem, pw, ph, w_mm, h_mm))


def box(ax, x, y, w, h, title, body, ec, fc="#FFFFFF", fs=7.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
                                linewidth=0.9, edgecolor=ec, facecolor=fc))
    ax.text(x + w / 2, y + h - 0.035, title, ha="center", va="top", fontsize=fs + 0.5,
            color=ec, fontweight="bold")
    ax.text(x + w / 2, y + h - 0.105, body, ha="center", va="top", fontsize=fs, linespacing=1.55)


def arrow(ax, p0, p1, color="#4D4D4D", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7,
                                 linewidth=0.9, color=color, linestyle=ls,
                                 connectionstyle="arc3,rad=%s" % rad, shrinkA=1, shrinkB=1))


# ---------------------------------------------------------------- figure 1
def fig1():
    fig = plt.figure(figsize=(W2 * MM, 84 * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box(ax, 0.015, 0.40, 0.235, 0.40, "目的地公共资源",
        "景区/公园：免费开放或票价受限\n到访人数与运营工作量上升\n门票与二次消费不归运营方", C["blue"])
    box(ax, 0.335, 0.40, 0.295, 0.40, "景区运营主体",
        "收入 = 固定酬金 + 合同窄口径分成\n成本 C(V) 随到访量上升\n收入不随 V 同比例上升", C["orange"])
    box(ax, 0.715, 0.40, 0.27, 0.40, "上市公司报表",
        "经营层利润率 → 归母净利率\n扣减层：少数股东损益 / 利息 /\n减值 / 折旧摊销", C["green"])

    arrow(ax, (0.255, 0.60), (0.330, 0.60))
    ax.text(0.292, 0.625, "客流↑", ha="center", va="bottom", fontsize=7)
    arrow(ax, (0.635, 0.60), (0.710, 0.60))
    ax.text(0.672, 0.625, "确认收入", ha="center", va="bottom", fontsize=7)

    # the two boundaries
    ax.add_patch(Rectangle((0.255, 0.02), 0.42, 0.25, linewidth=0.8, edgecolor=C["verm"],
                           facecolor="#FDF0EA", linestyle="-"))
    ax.text(0.465, 0.245, "合同边界：委托管理协议", ha="center", va="top", fontsize=7.8,
            color=C["verm"])
    ax.text(0.465, 0.192, "标的 · 酬金 · 分成 · 收款", ha="center", va="top", fontsize=7)
    ax.text(0.465, 0.140, "附注表 94 条 ≠ 正文 5 条", ha="center", va="top", fontsize=7)
    ax.text(0.465, 0.082, "同一业务两处披露，口径不可互换", ha="center", va="top", fontsize=7.0,
            color="#8A3B12")
    ax.add_patch(Rectangle((0.700, 0.02), 0.285, 0.25, linewidth=0.8, edgecolor=C["purple"],
                           facecolor="#F7EDF4"))
    ax.text(0.8425, 0.245, "报表边界：合并范围与扣减层", ha="center", va="top", fontsize=7.8,
            color=C["purple"])
    ax.text(0.8425, 0.175, "经营收益到达股东前\n要过四道扣减", ha="center", va="top",
            fontsize=7, linespacing=1.7)
    arrow(ax, (0.465, 0.40), (0.465, 0.275), color=C["verm"], ls=(0, (2, 1.5)))
    arrow(ax, (0.8425, 0.40), (0.8425, 0.275), color=C["purple"], ls=(0, (2, 1.5)))

    ax.text(0.015, 0.975, "价值创造在目的地，价值捕获在合同与报表", ha="left", va="top",
            fontsize=9)
    ax.text(0.015, 0.925, "同一客流，两端计价：一端是公共资源的使用，另一端是运营主体的合同收入",
            ha="left", va="top", fontsize=7, color="#333333")
    save(fig, "fig1_mechanism", W2, 84,
         "机制示意：目的地客流→运营主体合同收入→报表扣减层；合同边界与报表边界两条虚线")


# ---------------------------------------------------------------- figure 2
def fig2(pan):
    pan = pan.sort_values(["code", "year"]).copy()
    pan["prev_rev"] = pan.groupby("code")["revenue"].shift(1)
    pan["d_rev"] = pan.revenue - pan.prev_rev
    pan["d_np"] = pan.net_profit - pan.groupby("code")["net_profit"].shift(1)
    pan["ngs"] = 100.0 * pan.d_np / pan.prev_rev
    ok = pan.dropna(subset=["rg", "d_rev", "d_np", "prev_rev"])
    ok = ok[ok.prev_rev > 0]
    tiers = [("A", "A 级（直接经营景区）"), (None, "全样本")]
    counts = {}
    for t, _ in tiers:
        s = ok if t is None else ok[ok.tier == t]
        up_up = int(((s.d_rev > 0) & (s.d_np > 0)).sum())
        up_dn = int(((s.d_rev > 0) & (s.d_np < 0)).sum())
        dn_up = int(((s.d_rev < 0) & (s.d_np > 0)).sum())
        dn_dn = int(((s.d_rev < 0) & (s.d_np < 0)).sum())
        counts[t] = (up_up, up_dn, dn_up, dn_dn, len(s))
    a = counts["A"]
    b = counts[None]
    assert a[:4] == (68, 27, 22, 53) and a[4] == 170, a
    assert b[:4] == (98, 40, 28, 74) and b[4] == 240, b

    fig = plt.figure(figsize=(W2 * MM, 68 * MM))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.45], wspace=0.34,
                          left=0.10, right=0.99, top=0.90, bottom=0.19)

    # (a) share of the four quadrants (grouped bars)
    ax = fig.add_subplot(gs[0, 0])
    labels = ["双升", "营收↑\n利润↓", "营收↓\n利润↑", "双降"]
    a_shares = [100.0 * v / counts["A"][4] for v in counts["A"][:4]]
    b_shares = [100.0 * v / counts[None][4] for v in counts[None][:4]]
    x = np.arange(4)[::-1]
    ax.barh(x + 0.19, a_shares, height=0.36, color=C["blue"], label="A 级（n=170）")
    ax.barh(x - 0.19, b_shares, height=0.36, color=C["grey"], label="全样本（n=240）")
    for i in range(4):
        ax.text(a_shares[i] + 0.6, x[i] + 0.19, "%.1f" % a_shares[i], ha="left", va="center",
                fontsize=7.0, color=C["blue"])
        ax.text(b_shares[i] + 0.6, x[i] - 0.19, "%.1f" % b_shares[i], ha="left", va="center",
                fontsize=7.0, color="#4D4D4D")
    ax.set_yticks(x)
    ax.set_yticklabels(labels, fontsize=MIN_PT)
    ax.set_xlim(0, 43)
    ax.set_xlabel("占增速观测比重（%）")
    ax.tick_params(axis="x", labelsize=MIN_PT)
    ax.tick_params(axis="y", length=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title("(a) 四格分布（蓝 A 级 n=170，灰全样本 n=240）", loc="left", fontsize=7.5, pad=4)

    # (b) symmetric-log scatter
    ax2 = fig.add_subplot(gs[0, 1])
    s = ok[ok.tier == "A"]
    ax2.axhline(0, color="#666666", linewidth=0.6, zorder=1)
    ax2.axvline(0, color="#666666", linewidth=0.6, zorder=1)
    ax2.axhspan(0, 1e5, xmin=0, xmax=1, color="#FDF0EA", zorder=0)
    ax2.set_xscale("symlog", linthresh=10)
    ax2.set_yscale("symlog", linthresh=10)
    ax2.scatter(s.rg, s.ngs, s=7, color=C["blue"], alpha=0.75, linewidths=0)
    ax2.set_xlim(-100, 500)
    ax2.set_ylim(-260, 260)
    ticks = [-200, -100, -50, -10, 0, 10, 50, 100, 200]
    ax2.set_yticks(ticks)
    ax2.set_yticklabels([str(t) for t in ticks])
    ax2.set_xticks([-100, -10, 0, 10, 100, 400])
    ax2.set_xticklabels(["-100", "-10", "0", "10", "100", "400"])
    ax2.set_xlabel("营业收入增速（%）")
    ax2.set_ylabel("归母净利变化 / 上年营收（%）")
    ax2.tick_params(labelsize=MIN_PT)
    for sp in ("top", "right"):
        ax2.spines[sp].set_visible(False)
    ax2.set_title("(b) A 级变化散点（对称对数轴）", loc="left", fontsize=7.5, pad=4)
    ax2.text(0.03, 0.96, "corr(水平)=0.552\ncorr(增速)=0.129", transform=ax2.transAxes,
             va="top", ha="left", fontsize=MIN_PT, linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#CCCCCC", linewidth=0.5))
    save(fig, "fig2_quadrant", W2, 68,
         "四格分布与 A 级增速散点；四格计数 A 50/45/19/56(n=170)、全样本 70/68/27/75(n=240)")


# ---------------------------------------------------------------- figure 3
def fig3():
    t = pd.read_csv(os.path.join(D, "contract_terms_v4.csv"), dtype={"code": str})
    pan = pd.read_csv(os.path.join(D, "panel_annual_2015_2025_v2.csv"), dtype={"code": str})
    rev = {(r["code"], int(r["year"])): float(r["revenue"]) for r in pan.to_dict("records")
           if pd.notna(r["revenue"])}
    ann = t[t.kind == "A"]
    rec = []
    for r in ann.to_dict("records"):
        rv = rev.get((r["code"], int(r["year"])))
        if rv and pd.notna(r["amount_yuan"]):
            rec.append((r["code"], int(r["year"]), 100.0 * r["amount_yuan"] / rv))
    assert len(rec) == 78, len(rec)
    med = float(np.median([x[2] for x in rec]))
    assert round(med, 4) == 0.0101, med

    # Qujiang 2024H1, five narrative agreements: fee / consolidated revenue
    h1rev = 770241193.31
    body = [2541.41, 2359.51, 511.27, 6798.50, 3751.59]
    body_pct = [100.0 * v * 1e4 / h1rev for v in body]
    assert round(sum(body_pct), 2) == 20.72, sum(body_pct)

    fig = plt.figure(figsize=(W1 * MM, 64 * MM))
    ax = fig.add_axes([0.185, 0.20, 0.80, 0.66])
    codes = sorted({x[0] for x in rec})
    for i, code in enumerate(codes):
        v = [x[2] for x in rec if x[0] == code]
        jit = (np.random.RandomState(i + 7).rand(len(v)) - 0.5) * 0.55
        ax.scatter(v, np.full(len(v), i) + jit, s=6, color=C["blue"], alpha=0.65, linewidths=0)
    ax.axvline(med, color=C["blue"], linestyle=(0, (3, 2)), linewidth=0.8)
    ax.text(1.05e-4, -1.15, "中位 0.0101%（n=78）", fontsize=MIN_PT, color=C["blue"],
            ha="left", va="center")
    yb = len(codes) + 0.8
    ax.scatter(body_pct, np.full(len(body_pct), yb), marker="D", s=15, color=C["verm"], linewidths=0)
    ax.scatter([20.72], [yb], marker="D", s=34, color="#8C2D04", linewidths=0.5,
               edgecolors="white", zorder=5)
    ax.annotate("五条合计 20.72%", xy=(20.72, yb), xytext=(0.55, yb + 0.55), fontsize=MIN_PT,
                ha="left", va="bottom", color="#8C2D04",
                arrowprops=dict(arrowstyle="-", linewidth=0.5, color="#8C2D04"))
    ax.set_xscale("log")
    ax.set_xlim(3e-5, 120)
    ax.set_ylim(-1.6, yb + 1.5)
    ax.set_yticks(list(range(len(codes))) + [yb])
    ax.set_yticklabels(codes + ["正文 5 条"], fontsize=MIN_PT)
    ax.set_xlabel("酬金 / 营业收入（%，对数刻度）")
    ax.set_xticks([1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100])
    ax.set_xticklabels(["0.0001", "0.001", "0.01", "0.1", "1", "10", "100"])
    ax.tick_params(labelsize=MIN_PT)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.text(0.03, 0.93, "附注表：6 家 78 条", transform=ax.transAxes,
            ha="left", va="top", fontsize=7.0, color="#333333")
    save(fig, "fig3_fee_channel", W1, 64,
         "两通道酬金/营收：附注表 78 个年度记录（中位 0.0101%）vs 曲江 2024H1 正文 5 条（合计 20.72%）")


# ---------------------------------------------------------------- figure 4
def fig4():
    h = pd.read_csv(os.path.join(D, "h2_results.csv"), dtype={"spec": str})
    specs = [("A级|net_margin|负担流量", "归母净利率（n=115）", C["blue"]),
             ("A级|cfo_margin|负担流量", "经营现金流利润率（n=115）", C["green"])]
    names = {"da_int": "折旧摊销", "int_burden": "利息负担", "impair": "减值"}
    order = ["da_int", "int_burden", "impair"]
    fig = plt.figure(figsize=(W1 * MM, 60 * MM))
    gs = fig.add_gridspec(2, 1, hspace=0.55, left=0.245, right=0.985, top=0.90, bottom=0.17)
    for i, (spec, title, color) in enumerate(specs):
        ax = fig.add_subplot(gs[i, 0])
        s = h[h.spec == spec].set_index("var")
        ys = np.arange(len(order))
        for j, var in enumerate(order):
            if var not in s.index:
                continue
            r = s.loc[var]
            lo, hi = r["coef"] - 1.96 * r["se"], r["coef"] + 1.96 * r["se"]
            ax.plot([lo, hi], [j, j], color=color, linewidth=1.1, solid_capstyle="butt")
            ax.plot([r["coef"]], [j], marker="o", markersize=4.0, color=color,
                    markerfacecolor=color if r["p"] < 0.05 else "white", markeredgewidth=0.9)
            ax.text(3.9, j, ("%.2f" % r["coef"]).replace("-", "\u2212") + " (%s)" % ("%.3f" % r["p"])[1:],
                    va="center", ha="left", fontsize=7.0, color="#222222")
        ax.axvline(0, color="#666666", linewidth=0.7)
        present = [v for v in order if v in s.index]
        ax.set_yticks([order.index(v) for v in present])
        ax.set_yticklabels([names[v] for v in present], fontsize=MIN_PT)
        ax.set_ylim(len(order) - 0.3, -0.7)
        ax.set_xlim(-8.0, 9.5)
        ax.set_xticks([-8, -6, -4, -2, 0, 2, 4])
        ax.tick_params(labelsize=MIN_PT)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.set_title(title, loc="left", fontsize=7.3, pad=3)
        if i < 1:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel("系数（自变量为营收占比；误差棒=95% CI）")
    save(fig, "fig4_forest", W1, 60,
         "H2 系数森林图：实心=p<0.05，空心=不显著；括号内为 p 值")


# ---------------------------------------------------------------- figure 5
def fig5():
    d = pd.read_csv(os.path.join(D, "rq2_decomp.csv"), dtype={"code": str})
    a = d[(d.tier == "A") & d.complete]
    x0, x1 = a[a.year <= 2019], a[a.year >= 2020]
    both = set(x0.code) & set(x1.code)
    x0, x1 = x0[x0.code.isin(both)], x1[x1.code.isin(both)]
    assert len(both) == 13 and len(x0) == 46 and len(x1) == 51, (len(both), len(x0), len(x1))
    g = lambda x, k: 100.0 * x[k].mean()
    comp = ["adj_margin", "minority", "int_burden", "impair", "da_int", "net_margin"]
    P = {k: (g(x0, k), g(x1, k)) for k in comp}
    assert abs(P["net_margin"][0] - 11.19) < 0.01 and abs(P["net_margin"][1] + 4.77) < 0.01, P
    assert abs(P["adj_margin"][0] - 30.60) < 0.01 and abs(P["adj_margin"][1] - 38.29) < 0.01, P

    fig = plt.figure(figsize=(W2 * MM, 72 * MM))
    gs = fig.add_gridspec(2, 1, hspace=0.55, left=0.09, right=0.985, top=0.90, bottom=0.13)
    labels = ["经营层\n利润率", "少数股东\n损益", "利息\n负担", "减值\n损失", "折旧\n摊销", "归母\n净利率"]
    for i, (period, c0, c1) in enumerate([("2015–2019", P, 0), ("2020–2024", P, 1)]):
        ax = fig.add_subplot(gs[i, 0])
        base = P["adj_margin"][c1]
        vals = [(labels[0], base, "abs")]
        run = base
        ends = [base]
        for lab, key in ((labels[1], "minority"), (labels[2], "int_burden"),
                         (labels[3], "impair"), (labels[4], "da_int")):
            step = -P[key][c1]
            vals.append((lab, step, "delta"))
            run += step
            ends.append(run)
        vals.append((labels[5], run, "abs"))
        ends.append(run)
        bottom = 0.0
        for j, (lab, v, kind) in enumerate(vals):
            if kind == "abs":
                color = C["blue"] if v >= 0 else C["verm"]
                ax.bar(j, v, bottom=0, width=0.62, color=color, edgecolor="white", linewidth=0.5)
                if v >= 0:
                    ax.text(j, v + 0.7, "%.2f" % v, ha="center", va="bottom", fontsize=MIN_PT)
                elif abs(v) >= 8:
                    ax.text(j, v / 2, "%.2f" % v, ha="center", va="center", fontsize=MIN_PT,
                            color="white")
                else:
                    ax.text(j, v - 0.7, "%.2f" % v, ha="center", va="top", fontsize=MIN_PT)
            else:
                bottom = sum(vals[m][1] for m in range(1, j)) + base
                ax.bar(j, v, bottom=bottom, width=0.62, color=C["orange"] if v < 0 else C["green"],
                       edgecolor="white", linewidth=0.5)
                off = 1.8 if abs(v) < 2 else 0.7
                ax.text(j, bottom + v + (off if v >= 0 else -off), "%+.2f" % v, ha="center",
                        va="bottom" if v >= 0 else "top", fontsize=MIN_PT)
        ax.axhline(0, color="#666666", linewidth=0.6)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=MIN_PT)
        ax.set_ylim(min(0, min(ends)) - 8.0, max(ends + [0]) + 7.0)
        ax.set_ylabel("%", fontsize=7.5)
        ax.tick_params(labelsize=MIN_PT)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.set_title("(%s) %s（13 家平衡样本，n=%d）" % ("ab"[i], period, [46, 51][i]),
                     loc="left", fontsize=7.5, pad=3)
    save(fig, "fig5_waterfall", W2, 72,
         "归母净利率瀑布：经营层利润率经少数股东/利息/减值/折旧四层扣减；13 家平衡样本 2015–2019 n=46、2020–2024 n=51")


# ---------------------------------------------------------------- figure 6
def fig6():
    bf = pd.read_csv(os.path.join(D, "rq2_by_firm.csv"), dtype={"code": str})
    assert len(bf) == 17, len(bf)
    fig = plt.figure(figsize=(W1 * MM, 74 * MM))
    ax = fig.add_axes([0.16, 0.16, 0.80, 0.76])
    lo = -50
    hi = 70
    ax.plot([lo, hi], [lo, hi], color="#999999", linewidth=0.7, linestyle=(0, (3, 2)))
    sz = 6 + 2.2 * bf.n
    ax.scatter(bf.adj_margin * 100, bf.net_margin * 100, s=sz, color=C["blue"],
               alpha=0.75, linewidths=0.6, edgecolors="white")
    lab = {"000978": (7, -3), "000430": (7, 1), "600054": (-7, -1),
           "603136": (-7, -7), "000888": (-7, -7), "600593": (7, -2)}
    lab_ha = {"000888": "right", "600054": "right", "603136": "right"}
    for _, r in bf.iterrows():
        if r.code in lab:
            dx, dy = lab[r.code]
            ax.annotate(r.code, (r.adj_margin * 100, r.net_margin * 100), textcoords="offset points",
                        xytext=(dx, dy), fontsize=7.0, color="#333333",
                        ha=lab_ha.get(r.code, "left"), va="center",
                        arrowprops=dict(arrowstyle="-", linewidth=0.4, color="#888888",
                                        shrinkA=0, shrinkB=3))
    ax.axhline(0, color="#666666", linewidth=0.6)
    ax.axvline(0, color="#666666", linewidth=0.6)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("经营层利润率（%）")
    ax.set_ylabel("归母净利率（%）")
    ax.tick_params(labelsize=MIN_PT)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.text(0.03, 0.95, "虚线：两率相等\n点大小：观测年数\n仅标注正文提及的 6 家", transform=ax.transAxes,
            va="top", ha="left", fontsize=MIN_PT, linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#CCCCCC", linewidth=0.5))
    ax.text(0.97, 0.03, "其余 11 家见附表 A1", transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.0, color="#666666")
    save(fig, "fig6_firm_scatter", W1, 74,
         "逐家经营层利润率 vs 归母净利率（17 家 A 级）；45° 线以上为净利高于经营层（少数股东分担亏损）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", type=int, default=None)
    args = ap.parse_args()
    only = set(args.only) if args.only else {1, 2, 3, 4, 5, 6}
    pan = load()
    if 1 in only:
        fig1()
    if 2 in only:
        fig2(pan)
    if 3 in only:
        fig3()
    if 4 in only:
        fig4()
    if 5 in only:
        fig5()
    if 6 in only:
        fig6()
    mf = pd.read_csv(MF) if os.path.exists(MF) else pd.DataFrame()
    print("[manifest] %s  %d figures" % (MF, len(mf)))


if __name__ == "__main__":
    main()
