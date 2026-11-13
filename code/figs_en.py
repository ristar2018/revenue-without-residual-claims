# -*- coding: utf-8 -*-
"""English versions of Figures 1-6.

Reuses code/figs.py (same data, same assertions) and translates every text
object at draw time, so the numbers cannot drift from the Chinese originals.
Output: figures/en_figN_*.pdf and .png, manifest figures/fig_manifest_en.csv.

Usage: python code/figs_en.py [--only 1 2 ...]
"""
import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.text as mtext
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import figs  # noqa: E402

FIG = os.path.join(ROOT, "figures")

TR = {
    # Figure 1
    "目的地公共资源": "Public destination resources",
    "景区/公园：免费开放或票价受限\n到访人数与运营工作量上升\n门票与二次消费不归运营方":
        "Scenic areas and parks:\nopen access or capped prices\ngate and secondary spend\nstay with the principal",
    "景区运营主体": "Operating company",
    "收入 = 固定酬金 + 合同窄口径分成\n成本 C(V) 随到访量上升\n收入不随 V 同比例上升":
        "Revenue = fixed fee + narrow share\nCost C(V) rises with visitation\nRevenue does not rise proportionally",
    "上市公司报表": "Listed company statements",
    "经营层利润率 → 归母净利率\n扣减层：少数股东损益 / 利息 /\n减值 / 折旧摊销":
        "Operating margin → net margin\nDeductions: minority interest /\ninterest / impairment / depreciation",
    "客流↑": "Visitors ↑",
    "确认收入": "Revenue recognised",
    "合同边界：委托管理协议": "Contract boundary: entrusted management",
    "标的 · 酬金 · 分成 · 收款": "Subject · fee · sharing · collection",
    "附注表 94 条 ≠ 正文 5 条": "Notes table 94 ≠ main text 5",
    "同一业务两处披露，口径不可互换": "Two disclosures, non-interchangeable bases",
    "报表边界：合并范围与扣减层": "Reporting boundary:\nconsolidation and deductions",
    "经营收益到达股东前\n要过四道扣减": "Operating returns pass four\ndeduction layers before\nshareholders",
    "价值创造在目的地，价值捕获在合同与报表":
        "Value is created at the destination and captured at the contract and the statements",
    "同一客流，两端计价：一端是公共资源的使用，另一端是运营主体的合同收入":
        "One visitor flow, two prices: use of a public resource, and the operator's contractual revenue",
    # Figure 2
    "A 级（直接经营景区）": "A-level (direct scenic-area operation)",
    "全样本": "Full sample",
    "双升": "Both up",
    "营收↑\n利润↓": "Revenue ↑\nProfit ↓",
    "营收↓\n利润↑": "Revenue ↓\nProfit ↑",
    "双降": "Both down",
    "A 级（n=170）": "A-level (n=170)",
    "全样本（n=240）": "Full sample (n=240)",
    "占增速观测比重（%）": "Share of growth observations (%)",
    "(a) 四格分布（蓝 A 级 n=170，灰全样本 n=240）":
        "(a) Quadrant shares (blue A-level n=170; grey full sample n=240)",
    "营业收入增速（%）": "Revenue growth (%)",
    "归母净利变化 / 上年营收（%）": "Change in parent net profit\n/ prior-year revenue (%)",
    "(b) A 级变化散点（对称对数轴）": "(b) A-level change scatter (symmetric log axes)",
    "corr(水平)=0.552\ncorr(增速)=0.129": "corr(levels) = 0.552\ncorr(growth) = 0.129",
    # Figure 3 (fee channel)
    "中位 0.0101%（n=78）": "Median 0.0101%",
    "五条合计 20.72%": "Five clauses, 20.72%",
    "正文 5 条": "Main text (5)",
    "酬金 / 营业收入（%，对数刻度）": "Fee / operating revenue (%, log scale)",
    "附注表：6 家 78 条": "Notes table:\n6 firms, 78 records",
    # Figure 4 (forest)
    "A级|net_margin|负担流量": "A级|net_margin|负担流量",
    "归母净利率（n=115）": "Parent net margin (n=115)",
    "经营现金流利润率（n=115）": "Operating cash-flow margin (n=115)",
    "利润差（n=132）": "Profit difference (n=132)",
    "折旧摊销": "Depreciation &\namortisation",
    "利息负担": "Interest burden",
    "减值": "Impairment",
    "系数（自变量为营收占比；误差棒=95% CI）":
        "Coefficient (95% CI)",
    # Figure 5 (waterfall)
    "经营层\n利润率": "Operating\nmargin",
    "少数股东\n损益": "Minority\ninterest",
    "利息\n负担": "Interest\nburden",
    "减值\n损失": "Impairment",
    "折旧\n摊销": "Depreciation\n& amortisation",
    "归母\n净利率": "Net margin\n(parent)",
    "(%s) %s（13 家平衡样本，n=%d）": "(%s) %s (13 balanced firms, n=%d)",
    # Figure 6 (firm scatter)
    "经营层利润率（%）": "Operating-layer margin (%)",
    "归母净利率（%）": "Parent net margin (%)",
    "虚线：两率相等\n点大小：观测年数\n仅标注正文提及的 6 家":
        "Dashed: equal margins\nSize: years observed\nSix firms cited in text labelled",
    "其余 11 家见附表 A1": "Others: Table A1",
}

EXTRA = [
    ("（13 家平衡样本，n=", " (13 balanced firms, n="),
    ("）", ")"),
]

NOTES = {
    "fig1_mechanism": "Mechanism: destination flows -> operator contractual revenue -> statement deductions; "
                      "dashed lines mark the contract and reporting boundaries",
    "fig2_quadrant": "Quadrant shares by the signs of the two level changes and A-level change scatter; "
                     "counts A 68/27/22/53 (n=170), full sample 98/40/28/74 (n=240)",
    "fig3_fee_channel": "Fee/revenue by channel: 78 annual notes records (median 0.0101%) vs five Qujiang "
                        "main-text clauses in 2024H1 (20.72% in total)",
    "fig4_forest": "Forest plot of H2 coefficients: filled = p<0.05, open = not significant; p-values in parentheses",
    "fig5_waterfall": "Net-margin waterfall: operating margin less minority interest, interest, impairment and "
                      "depreciation; 13 balanced firms, 2015-2019 n=46, 2020-2024 n=51",
    "fig6_firm_scatter": "Firm-level operating margin vs parent net margin (17 A-level firms); points above the "
                         "45-degree line indicate net margin above operating margin",
}

RENUM = {
    "fig1_mechanism": "en_fig1_mechanism",
    "fig2_quadrant": "en_fig2_quadrant",
    "fig5_waterfall": "en_fig3_waterfall",
    "fig6_firm_scatter": "en_fig4_firm_scatter",
    "fig3_fee_channel": "en_fig5_fee_channel",
    "fig4_forest": "en_fig6_forest",
}

MF = os.path.join(FIG, "fig_manifest_en.csv")

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "axes.unicode_minus": True,
    "pdf.fonttype": 42,
})


def translate(s):
    if s in TR:
        return TR[s]
    out = s
    for a, b in EXTRA:
        out = out.replace(a, b)
    for a, b in TR.items():
        if a and a in out:
            out = out.replace(a, b)
    return out


_orig_set_text = mtext.Text.set_text


def set_text(self, s):
    if isinstance(s, str):
        s = translate(s)
    return _orig_set_text(self, s)


mtext.Text.set_text = set_text


def save_en(fig, stem, w_mm, h_mm, note):
    os.makedirs(FIG, exist_ok=True)
    name = RENUM[stem]
    pdf = os.path.join(FIG, name + ".pdf")
    png = os.path.join(FIG, name + ".png")
    fig.savefig(pdf)
    fig.savefig(png, dpi=300)
    plt.close(fig)
    raw = open(pdf, "rb").read()
    i = raw.rfind(b"/MediaBox")
    assert i > 0, "no MediaBox in " + pdf
    seg = raw[i:i + 200].split(b"]")[0].split(b"[")[-1].split()
    pw, ph = float(seg[2]) / 72.0 * 25.4, float(seg[3]) / 72.0 * 25.4
    assert abs(pw - w_mm) < 0.8 and abs(ph - h_mm) < 1.2, (name, pw, ph, w_mm, h_mm)
    rows = []
    if os.path.exists(MF):
        rows = [r for r in pd.read_csv(MF).to_dict("records") if r["file"] != name]
    rows.append(dict(file=name, width_mm=round(pw, 1), height_mm=round(ph, 1),
                     design_w_mm=w_mm, design_h_mm=h_mm, min_font_pt=figs.MIN_PT,
                     note=NOTES.get(stem, translate(note))))
    pd.DataFrame(rows).to_csv(MF, index=False, encoding="utf-8-sig")
    print("[ok] %s  %.1f x %.1f mm" % (name, pw, ph))


figs.save = save_en


def fig1_en():
    """Figure 1 with English line breaks that fit the fixed box widths."""
    C = figs.C
    fig = plt.figure(figsize=(figs.W2 * figs.MM, 84 * figs.MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    figs.box(ax, 0.015, 0.40, 0.235, 0.40, "Public destination resources",
             "Scenic areas and parks:\nopen access or capped prices\ngate and secondary spend\nstay with the principal",
             C["blue"])
    figs.box(ax, 0.335, 0.40, 0.295, 0.40, "Operating company",
             "Revenue = fixed fee + narrow share\ncost C(V) rises with visitation\nrevenue does not rise with V",
             C["orange"])
    figs.box(ax, 0.715, 0.40, 0.27, 0.40, "Listed company statements",
             "operating margin to net margin\ndeductions: minority interest /\ninterest / impairment /\ndepreciation",
             C["green"])

    figs.arrow(ax, (0.255, 0.60), (0.330, 0.60))
    ax.text(0.292, 0.625, "Visitors up", ha="center", va="bottom", fontsize=7)
    figs.arrow(ax, (0.635, 0.60), (0.710, 0.60))
    ax.text(0.668, 0.625, "Revenue", ha="center", va="bottom", fontsize=7)

    ax.add_patch(plt.Rectangle((0.255, 0.02), 0.42, 0.25, linewidth=0.8,
                               edgecolor=C["verm"], facecolor="#FDF0EA", linestyle="-"))
    ax.text(0.465, 0.245, "Contract boundary: entrusted management", ha="center", va="top",
            fontsize=7.8, color=C["verm"])
    ax.text(0.465, 0.192, "subject, fee, sharing, collection", ha="center", va="top", fontsize=7)
    ax.text(0.465, 0.140, "notes table 94 versus main text 5", ha="center", va="top", fontsize=7)
    ax.text(0.465, 0.082, "two disclosures, non-interchangeable bases", ha="center", va="top",
            fontsize=7.0, color="#8A3B12")

    ax.add_patch(plt.Rectangle((0.700, 0.02), 0.285, 0.25, linewidth=0.8,
                               edgecolor=C["purple"], facecolor="#F7EDF4"))
    ax.text(0.8425, 0.245, "Reporting boundary", ha="center", va="top", fontsize=7.8,
            color=C["purple"])
    ax.text(0.8425, 0.185, "consolidation and deductions\noperating returns pass four\ndeduction layers",
            ha="center", va="top", fontsize=7, linespacing=1.7)

    figs.arrow(ax, (0.465, 0.40), (0.465, 0.275), color=C["verm"], ls=(0, (2, 1.5)))
    figs.arrow(ax, (0.8425, 0.40), (0.8425, 0.275), color=C["purple"], ls=(0, (2, 1.5)))

    ax.text(0.015, 0.975, "Value is created at the destination and captured at the contract and the statements",
            ha="left", va="top", fontsize=9)
    ax.text(0.015, 0.925, "One visitor flow, two prices: use of a public resource, and the operator's contractual revenue",
            ha="left", va="top", fontsize=7, color="#333333")
    figs.save(fig, "fig1_mechanism", figs.W2, 84,
              "Mechanism: destination flows to operator contractual revenue to statement deductions; "
              "dashed lines mark the contract and reporting boundaries")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", type=int, default=None)
    args = ap.parse_args()
    only = set(args.only) if args.only else {1, 2, 3, 4, 5, 6}
    pan = figs.load()
    if 1 in only:
        fig1_en()
    if 2 in only:
        figs.fig2(pan)
    if 3 in only:
        figs.fig3()
    if 4 in only:
        figs.fig4()
    if 5 in only:
        figs.fig5()
    if 6 in only:
        figs.fig6()
    print("[manifest] %s" % MF)


if __name__ == "__main__":
    main()
