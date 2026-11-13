# -*- coding: utf-8 -*-
"""Graphical abstract for TMP: 130 x 50 mm, 8 pt minimum.

Three-step mechanism plus one headline number. Writes
figures/en_graphical_abstract.pdf and .png (600 dpi for the raster copy).
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

MM = 1 / 25.4
W, H = 130 * MM, 50 * MM
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "pdf.fonttype": 42,
    "axes.linewidth": 0.6,
})

BLUE = "#2E6DA4"
ORANGE = "#C8641E"
GREEN = "#2F7D4F"
GREY = "#4D4D4D"

fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 130)
ax.set_ylim(0, 50)
ax.axis("off")


def box(x, y, w, h, edge, title, body):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0,rounding_size=1.6",
                                linewidth=0.9, edgecolor=edge, facecolor="white"))
    ax.text(x + w / 2, y + h - 5.2, title, ha="center", va="top",
            fontsize=8, color=edge, fontweight="bold")
    ax.text(x + w / 2, y + h - 12.0, body, ha="center", va="top",
            fontsize=7.2, color=GREY, linespacing=1.55)


def arrow(x0, x1, y):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>",
                                 mutation_scale=8, linewidth=0.9, color=GREY))


box(2, 14, 36, 30, BLUE, "Destination demand",
    "visitors enter\nopen-access or\ncapped-price sites")
box(47, 14, 36, 30, ORANGE, "Operator revenue",
    "fixed fee plus a\nnarrow share of\nincremental receipts")
box(92, 14, 36, 30, GREEN, "Reported profit",
    "asset costs, interest,\nimpairment and minority\nclaims stay with the firm")

arrow(38.5, 46.2, 29)
arrow(83.5, 91.2, 29)

ax.text(65, 9.4, "16.7% of 240 firm-years: revenue up, profit down",
        ha="center", va="center", fontsize=8, color="black")
ax.text(65, 4.2, "99 disclosed clauses: the contract allocates revenue, not the residual claim",
        ha="center", va="center", fontsize=7.2, color=GREY, style="italic")

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figs")
pdf = os.path.join(out, "en_graphical_abstract.pdf")
fig.savefig(pdf, format="pdf")
fig.savefig(pdf.replace(".pdf", ".png"), dpi=600, format="png")
print("saved", pdf, os.path.getsize(pdf) // 1024, "KB")
