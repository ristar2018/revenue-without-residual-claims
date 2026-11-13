# -*- coding: utf-8 -*-
"""Build the LaTeX submission package from the English markdown sources.

Outputs (all under manuscript/tex/):
  manuscript.tex   full manuscript (elsarticle, review mode, line numbers)
  highlights.tex   standalone highlights file
  cover_letter.tex standalone cover letter

The markdown sources remain the single source of truth; this script only
re-typesets them. Run after assemble_en.py / check_en.py.
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "manuscript")
OUT = os.path.join(ROOT, "manuscript")
os.makedirs(OUT, exist_ok=True)

MATH_RE = re.compile(r"(\\\(.*?\\\)|\\\[.*?\\\])", re.S)


def esc_text(s):
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$")]:
        s = s.replace(a, b)
    s = s.replace("\u2212", r"\ensuremath{-}")
    s = s.replace("\u00b2", r"\ensuremath{^2}")
    s = s.replace("\u00b1", r"\ensuremath{\pm}")
    s = s.replace("\u00d7", r"\ensuremath{\times}")
    s = s.replace("\u2265", r"\ensuremath{\geq}")
    s = s.replace("\u2264", r"\ensuremath{\leq}")
    s = s.replace("\u2013", "--").replace("\u2014", "---")
    s = s.replace("\u2018", "`").replace("\u2019", "'")
    s = s.replace("\u201c", "``").replace("\u201d", "''")
    s = s.replace("\u2026", r"\ldots{}")
    return s


def inline(s):
    """Convert inline markdown + \\( \\) math into LaTeX."""
    parts = MATH_RE.split(s)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            p = p.replace("\\(", "$").replace("\\)", "$")
            out.append(p)
        else:
            p = esc_text(p)
            p = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", p)
            p = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"\\emph{\1}", p)
            out.append(p)
    return "".join(out)


def cell(s):
    """Table cell: keep <br> as line break, significance stars as superscript."""
    s = s.strip()
    s = s.replace("<br>", r"\newline ")
    s = inline(s)
    s = re.sub(r"(\d)\*\*\*", r"\1$^{***}$", s)
    s = re.sub(r"(\d)\*\*", r"\1$^{**}$", s)
    s = re.sub(r"(\d)\*", r"\1$^{*}$", s)
    return s


# ---------------------------------------------------------------- body text
def blocks(text):
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    out, buf = [], []
    for line in lines:
        if line.strip() == "":
            if buf:
                out.append("\n".join(buf))
                buf = []
        else:
            buf.append(line.rstrip())
    if buf:
        out.append("\n".join(buf))
    return out


def body_units(path):
    """Render one section file as a list of (tex, raw) units, one per paragraph."""
    text = io.open(path, encoding="utf-8").read()
    res = []
    for blk in blocks(text):
        first = blk.split("\n")[0]
        if first.startswith("#"):
            m = re.match(r"^(#+)\s+(.*)$", first)
            level = len(m.group(1))
            title = re.sub(r"^\d+(\.\d+)*\.?\s*", "", m.group(2)).strip()
            cmd = {1: "section", 2: "section", 3: "subsection", 4: "subsubsection"}[level]
            res.append(("\\%s{%s}" % (cmd, inline(title)), "", os.path.basename(path)))
            rest = "\n".join(blk.split("\n")[1:]).strip()
            if rest:
                res.append((inline(rest), rest, os.path.basename(path)))
            continue
        if blk.lstrip().startswith("\\["):
            res.append((blk.strip(), "", os.path.basename(path)))
            continue
        if blk.lstrip().startswith("- "):
            items = [inline(re.sub(r"^-\s+", "", l)) for l in blk.split("\n") if l.strip().startswith("- ")]
            res.append(("\\begin{itemize}\n\\item " + "\n\\item ".join(items) + "\n\\end{itemize}", "",
                        os.path.basename(path)))
            continue
        res.append((inline(blk.replace("\n", " ")), blk, os.path.basename(path)))
    return res


def body_tex(path):
    return "\n\n".join(u[0] for u in body_units(path))


def scan_mentions(raw):
    """(kind, number) pairs for 'Table 3', 'Tables 1 and 2', 'Figures 3--4'."""
    found = []
    for m in re.finditer(r"\b(Tables?|Figures?)\s+", raw):
        kind = "table" if m.group(1).lower().startswith("table") else "fig"
        tail = raw[m.end():m.end() + 40]
        mm = re.match(r"(\d+)((?:\s*(?:,|and|&|--|-|to)\s*\d+)*)", tail)
        if not mm:
            continue
        for n in re.findall(r"\d+", mm.group(0)):
            found.append((kind, int(n)))
    return found


def place_floats(units, blocks_by_kind):
    """Insert each float after the paragraph that first discusses it.

    A float is anchored where it is first cited in the Results section; only
    floats never cited there fall back to their first citation anywhere in the
    text. At most one float is attached to a paragraph, so that several floats
    introduced by the same sentence spread over the following paragraphs instead
    of piling up on one page.
    """
    first_any, first_res = {}, {}
    for i, (_, raw, fname) in enumerate(units):
        if not raw:
            continue
        for kind, n in scan_mentions(raw):
            first_any.setdefault((kind, n), i)
            if fname.startswith("04_"):
                first_res.setdefault((kind, n), i)

    plan = {}
    for kind, blocks in blocks_by_kind.items():
        nums = sorted(int(k) for k in blocks)
        for n in nums:
            a = first_res.get((kind, n))
            where = "results"
            if a is None:
                a = first_any.get((kind, n))
                where = "text"
            if a is None:
                a = len(units) - 1
                where = "end of body"
            plan.setdefault(a, []).append(blocks[str(n)])
            print("  %-5s %d -> unit %d (%s)" % (kind, n, a, where))

    out, carry = [], []
    for i, (t, raw, _) in enumerate(units):
        out.append(t)
        carry.extend(plan.get(i, []))
        if carry and raw:
            out.append(carry.pop(0))
    out.extend(carry)
    return out


# ---------------------------------------------------------------- references
def refs_tex():
    text = io.open(os.path.join(SRC, "06_references.md"), encoding="utf-8").read()
    entries = [l.strip() for l in text.replace("\r\n", "\n").split("\n")
               if l.strip() and not l.startswith("#")]
    body = []
    for e in entries:
        e = inline(e)
        e = re.sub(r"https://doi\.org/(\S+)$", r"\\url{https://doi.org/\1}", e)
        body.append("\\refitem{%s}" % e)
    return "\n".join(body), len(entries)


# ---------------------------------------------------------------- tables
def md_table(rows):
    """rows: markdown table lines. Returns (spec, header cells, body rows)."""
    head = [c for c in rows[0].strip().strip("|").split("|")]
    align = [c.strip() for c in rows[1].strip().strip("|").split("|")]
    spec = []
    for a in align:
        spec.append("r" if a.endswith(":") else "l")
    body = [[c for c in r.strip().strip("|").split("|")] for r in rows[2:]]
    return "".join(spec), head, body


def gen_table(num, caption, spec, head, body, notes, header_map=None, size="footnotesize"):
    head = [cell(h) for h in head]
    if header_map:
        head = [header_map.get(i, h) for i, h in enumerate(head)]
    lines = ["\\begin{table}[!htbp]", "\\centering"]
    if str(num).upper().startswith("A"):
        lines.append("\\renewcommand{\\thetable}{%s}" % num)
    lines += ["\\caption{%s}\\label{tab:%s}" % (inline(caption), num),
              "\\begin{minipage}{\\textwidth}", "\\centering", "\\%s" % size,
              "\\begin{adjustbox}{max width=\\textwidth}",
              "\\begin{tabular}{@{}%s@{}}" % spec,
              "\\toprule", " & ".join(head) + " \\\\", "\\midrule"]
    for r in body:
        lines.append(" & ".join(cell(c) for c in r) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{adjustbox}",
              "\\par\\medskip", "\\raggedright",
              "\\noindent\\textit{Notes.} %s" % inline(notes),
              "\\end{minipage}", "\\end{table}"]
    return "\n".join(lines)


T4 = r"""\begin{table}[!htbp]
\centering
\caption{Five Qujiang agreements in the 2024 half-year report.}\label{tab:4}
\begin{minipage}{\textwidth}
\footnotesize
\begin{tabularx}{\textwidth}{@{}r >{\raggedright\arraybackslash}X >{\raggedright\arraybackslash}X r r r >{\raggedright\arraybackslash}p{2.0cm}@{}}
\toprule
No. & Principal & Subject & \shortstack{Fee recognised\\(RMB 10,000)} & \shortstack{Same-type\\share (\%)} & \shortstack{Revenue\\share (\%)} & Term \\
\midrule
1 & Xi'an Qujiang New District Social Undertaking Asset Management Centre & Tang Paradise & 2,541.41 & 5.23 & 3.30 & 2011-01-01\newline to 2030-12-31 \\
2 & Xi'an Qujiang New District Social Undertaking Asset Management Centre & Qujiang Pool and Tang City Wall Ruins Park & 2,359.51 & 4.86 & 3.06 & 2010-11-01\newline to 2030-10-31 \\
3 & Xi'an Qujiang New District Social Undertaking Asset Management Centre & Big Wild Goose Pagoda, Datang Never Night City (including Kaiyuan Square and Yintai Square) and Ci'en Temple Ruins Park & 511.27 & 1.05 & 0.66 & 2010-11-01\newline to 2030-10-31 \\
4 & Xi'an Qujiang Daminggong Ruins Area Protection and Reconstruction Office & Qujiang Daminggong Ruins Park & 6,798.50 & 14.00 & 8.83 & 2010-10-01\newline to 2030-09-30 \\
5 & Xi'an City Wall Development Management Co., Ltd. & Xi'an City Wall Scenic Area & 3,751.59 & 7.73 & 4.87 & 2018-10-01\newline to 2023-12-31 \\
\midrule
-- & Total & Five agreements & 15,962.28 & -- & 20.72 & -- \\
\bottomrule
\end{tabularx}
\par\medskip
\noindent\textit{Notes.} Amounts are recognised in the 2024 half-year and are not annualised. `Share of same-type transactions' reproduces the original disclosure; its denominator is same-type transaction value, not revenue. `Share of consolidated revenue' uses consolidated operating revenue of RMB 770,241,193.31 for the period. The five agreements total RMB 159.6228 million, or 20.72\% of half-year consolidated operating revenue. Agreement 5 is reported as disclosed: its stated term ended on 31 December 2023, yet RMB 3.7516 million was recognised under it in the 2024 half-year. The report discloses no renewal or extension, so the amount is retained as reported and the timing is flagged rather than explained.
\end{minipage}
\end{table}"""

T5 = r"""\begin{table}[!htbp]
\centering
\caption{Three cost burdens and profitability (A-level firms, firm and year fixed effects, firm-clustered standard errors).}\label{tab:5}
\begin{minipage}{\textwidth}
\centering
\footnotesize
\textbf{Panel A.} Main specification.
\par\smallskip
\begin{tabular}{@{}lcc@{}}
\toprule
Independent variable & \shortstack{(1)\\Parent-attributable\\net margin} & \shortstack{(2)\\Operating cash-flow\\margin} \\
\midrule
Depreciation and amortisation/revenue & \shortstack{+1.318$^{**}$\\ (0.496)} & \shortstack{+1.947$^{***}$\\ (0.682)} \\
Interest burden & \shortstack{$-3.772^{*}$\\ (1.901)} & \shortstack{$-1.474$\\ (1.803)} \\
Impairment/revenue & \shortstack{$-1.413^{*}$\\ (0.647)} & \shortstack{$-0.967^{**}$\\ (0.395)} \\
$n$ & 115 & 115 \\
$R^{2}$ (within) & 0.646 & 0.591 \\
\bottomrule
\end{tabular}
\par\medskip
\textbf{Panel B.} Committed-stock specification (dependent variable: parent-attributable net margin).
\par\smallskip
\begin{tabular}{@{}lc@{}}
\toprule
Independent variable & \shortstack{Coefficient\\(standard error)} \\
\midrule
Interest-bearing debt/revenue & \shortstack{$-0.125^{*}$\\ (0.074)} \\
Long-term assets/revenue & \shortstack{+0.055\\ (0.039)} \\
Impairment/revenue & \shortstack{$-1.098$\\ (0.723)} \\
$n$ & 120 \\
$R^{2}$ (within) & 0.579 \\
\bottomrule
\end{tabular}
\par\medskip
\textbf{Panel C.} Turnover specification (dependent variable: parent-attributable net margin).
\par\smallskip
\begin{tabular}{@{}lc@{}}
\toprule
Independent variable & \shortstack{Coefficient\\(standard error)} \\
\midrule
Revenue/long-term assets & \shortstack{$-0.027$\\ (0.037)} \\
Interest burden & \shortstack{$-1.170$\\ (1.823)} \\
Impairment/revenue & \shortstack{$-1.371^{*}$\\ (0.781)} \\
$n$ & 115 \\
$R^{2}$ (within) & 0.573 \\
\bottomrule
\end{tabular}
\par\medskip
\raggedright
\noindent\textit{Notes.} Firm-clustered robust standard errors in parentheses, with the small-sample correction for 17 clusters. Because 17 clusters is few, three reference distributions are reported for column (1) in the text: the conventional normal, $t$ with 16 degrees of freedom, and a wild cluster bootstrap-$t$ with 999 Rademacher draws and the null imposed. Stars mark significance at the most conservative of the three: ** at the 5\% level and * at the 10\% level. In column (2) and in Panels B and C, stars follow the conventional normal reference and are descriptive only. A third column using the difference between parent-attributable net margin and operating cash-flow margin, reported in earlier drafts, is withdrawn: that difference is constructed from the same four deduction lines that enter the regressors, so its coefficients partly reproduce an accounting identity rather than an independent association. All variables are scaled by operating revenue and winsorised at $\pm$5\%. In Panel B, the long-term asset measure is not comparable before and after the new lease standard took effect in 2021; its coefficient is not interpreted economically.
\end{minipage}
\end{table}"""


def tables_blocks():
    text = io.open(os.path.join(SRC, "08_tables_figures.md"), encoding="utf-8").read()
    text = text.replace("\r\n", "\n")
    chunks = re.split(r"\n## ", "\n" + text)
    out, out_app = {}, []
    for ch in chunks:
        title = ch.split("\n")[0].strip()
        if not (title.startswith("Table") or title.startswith("Appendix Table")):
            continue
        lines = ch.split("\n")
        cap = ""
        notes = ""
        tbl = []
        for l in lines:
            if l.startswith("**Table") or re.match(r"^\*\*Panel", l):
                if l.startswith("**Table") and not cap:
                    cap = re.sub(r"^\*\*Table[^.]*\.\*\*\s*", "", l).strip()
                continue
            if l.startswith("*Notes.*"):
                notes = re.sub(r"^\*Notes\.\*\s*", "", l).strip()
                continue
            if l.strip().startswith("|"):
                tbl.append(l)
        if not cap or not tbl:
            continue
        if title.startswith("Table 4"):
            out["4"] = T4
            continue
        if title.startswith("Table 5"):
            out["5"] = T5
            continue
        # group table rows into consecutive blocks (Table A2 has one)
        spec, head, body = md_table(tbl)
        num = re.sub(r"^(Appendix\s+)?Table\s+", "", title)
        blk = gen_table(num, cap, spec, head, body, notes)
        if str(num).upper().startswith("A"):
            out_app.append(blk)
        else:
            out[str(num)] = blk
    return out, "\n\n".join(out_app)


FIGS = [
    ("en_fig1_mechanism.pdf", 0.95, "Value creation at the destination and value capture at the contract and reporting boundaries. Visitor flows enter the operating company; revenue is assigned under entrusted-management agreements; operating returns pass through four deduction layers before reaching shareholders. Dashed lines mark the contract boundary and the reporting boundary."),
    ("en_fig2_quadrant.pdf", 0.95, "Quadrants of revenue and profit changes, with A-level scatter. (a) Blue: 17 A-level firms ($n$ = 170 observations); grey: full sample ($n$ = 240). Quadrants are defined by the signs of the two level changes. (b) Scatter of revenue growth against the change in parent-attributable net profit scaled by prior-year revenue, on symmetric logarithmic axes; the sign of the vertical axis is that of the level change, so the upper-left region contains the divergent observations."),
    ("en_fig3_waterfall.pdf", 0.95, "Two-period waterfall of parent-attributable net margin (13 firms present in both subperiods). (a) 2015--2019 ($n$ = 46). (b) 2020--2024 ($n$ = 51). Minority interest of $-1.48$ appears as $+1.48$ because a subsidiary loss shared by minority shareholders is added back to the parent."),
    ("en_fig4_firm_scatter.pdf", 0.80, "Firm-level operating-layer margin and parent-attributable net margin (17 A-level firms; 2015--2024 means). The dashed line marks equality; point size indicates the number of observed years (5--10). Points below the line indicate that the deduction layer absorbed part of the operating return."),
    ("en_fig5_fee_channel.pdf", 0.80, "Fee-to-revenue ratios under two disclosure channels, on a logarithmic scale. The lower panel shows 78 annual notes-table records (median 0.0101\\%); the upper panel shows the five Qujiang main-text clauses (20.72\\% in aggregate)."),
    ("en_fig6_forest.pdf", 0.80, "Marginal associations of three cost burdens with profitability (A-level firms, controlling for firm and year effects). Each row corresponds to one regressor in a separate equation. Coefficients, intervals and the $p$-values printed at the right follow the conventional normal reference; filled markers denote $p<0.05$ under that reference. Because the panel has 17 clusters, inference in the text and in Table 5 uses the wild cluster bootstrap, under which interest burden is not significant at the 5\\% level."),
]


def figures_blocks():
    out = {}
    for i, (fn, w, cap) in enumerate(FIGS, start=1):
        out[str(i)] = ("\\begin{figure}[!htbp]\n\\centering\n"
                       "\\includegraphics[width=%.2f\\textwidth]{../figures/%s}\n"
                       "\\caption{%s}\\label{fig:%d}\n\\end{figure}" % (w, fn, cap, i))
    return out


PREAMBLE = r"""\documentclass[review,3p,times]{elsarticle}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage{threeparttable}
\usepackage{adjustbox}
\usepackage{lineno}
\usepackage{setspace}
\usepackage{placeins}
\usepackage{caption}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\graphicspath{{../figures/}}
\captionsetup{font=small,labelfont=bf,labelsep=period,justification=raggedright,singlelinecheck=false}
\renewcommand{\arraystretch}{1.15}
\emergencystretch=2em
% float placement: keep tables and figures close to their first citation
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.7}
\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.75}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{4}
% float pages: start at the top margin instead of centring the floats
\makeatletter
\setlength{\@fptop}{0pt}
\setlength{\@fpsep}{16pt plus 2pt}
\setlength{\@fpbot}{0pt plus 1fil}
\makeatother
\journal{Tourism Management Perspectives}
\def\refitem#1{\noindent\hangindent=1.5em\hangafter=1 #1\par\medskip}
\begin{document}
"""

META = json.load(io.open(os.path.join(SRC, "authors.json"), encoding="utf-8"))


def front_matter():
    """Author block, affiliations and abstract opener, all from authors.json."""
    out = [r"\begin{frontmatter}",
           r"\title{Revenue without residual claims: Contract design and the revenue--profit",
           r"divergence in China's listed tourism firms}"]
    for a in META["authors"]:
        cor = r"\corref{cor1}" if a.get("corresponding") else ""
        out.append(r"\author[%s]{%s%s}" % (a["aff"], a["name"], cor))
        if a.get("email"):
            out.append(r"\ead{%s}" % a["email"])
    for af in META["affiliations"]:
        out.append(r"\affiliation[%s]{organization={%s}," % (af["label"], af["organization"]))
        out.append(r"  city={%s}, postcode={%s}, country={%s}}"
                   % (af["city"], af["postcode"], af["country"]))
    out.append(r"\cortext[cor1]{%s}" % META.get("corresponding_note", "Corresponding author."))
    out.append(r"\begin{abstract}")
    return "\n".join(out) + "\n"

KEYWORDS = r"""\end{abstract}
\begin{keyword}
value capture \sep revenue rights \sep cost obligations \sep tourism firms \sep contract disclosure \sep China
\end{keyword}
\end{frontmatter}
\linenumbers
"""

SKIP_BACK = {"highlights", "graphical abstract"}


def back_matter():
    """Declarations from 07_back_matter.md; Highlights and the graphical-abstract note stay out."""
    text = io.open(os.path.join(SRC, "07_back_matter.md"), encoding="utf-8").read().replace("\r\n", "\n")
    out = []
    for block in text.split("\n# "):
        block = block.lstrip("# ").strip("\n")
        if not block:
            continue
        head, _, rest = block.partition("\n")
        if head.strip().lower() in SKIP_BACK:
            continue
        out.append(r"\section*{%s}" % inline(head.strip()))
        for para in [p.strip() for p in rest.split("\n\n") if p.strip()]:
            out.append(inline(para))
    return "\n\n".join(out) + "\n"


def main():
    title_abstract = io.open(os.path.join(SRC, "00_title_abstract.md"), encoding="utf-8").read().replace("\r\n", "\n")
    abs_body = title_abstract.split("## Abstract")[1]
    abstract = abs_body.split("**Keywords:**")[0].strip()

    units = []
    for fn in ["01_introduction.md", "02_theory.md", "03_data_methods.md",
               "04_results.md", "05_discussion.md"]:
        units.extend(body_units(os.path.join(SRC, fn)))

    tbl_blocks, tab_a2 = tables_blocks()
    fig_blocks = figures_blocks()
    body = place_floats(units, {"table": tbl_blocks, "fig": fig_blocks})

    refs, nrefs = refs_tex()

    doc = [PREAMBLE, front_matter(), inline(abstract.replace("\n", " ")), KEYWORDS,
           "\n\n".join(body), "\\FloatBarrier", back_matter(),
           "\\section*{References}", refs,
           "\\clearpage\n\\section*{Appendix A. Supplementary table}", tab_a2,
           "\\end{document}\n"]
    tex = "\n\n".join(doc)
    io.open(os.path.join(OUT, "manuscript.tex"), "w", encoding="utf-8", newline="\n").write(tex)

    # highlights
    hl = io.open(os.path.join(SRC, "07_back_matter.md"), encoding="utf-8").read().replace("\r\n", "\n")
    hsec = hl.split("# Highlights")[1].split("#")[0]
    items = [l[2:].strip() for l in hsec.split("\n") if l.strip().startswith("- ")]
    htex = ("\\documentclass[11pt]{article}\n"
            "\\usepackage[margin=2.5cm]{geometry}\n"
            "\\usepackage[utf8]{inputenc}\n\\usepackage[T1]{fontenc}\n"
            "\\usepackage{newtxtext}\n"
            "\\usepackage{enumitem}\n"
            "\\begin{document}\n\\thispagestyle{empty}\n"
            "\\section*{Highlights}\n\\begin{itemize}[leftmargin=*,itemsep=6pt]\n"
            + "\n".join("\\item " + inline(i) for i in items)
            + "\n\\end{itemize}\n\\end{document}\n")
    io.open(os.path.join(OUT, "highlights.tex"), "w", encoding="utf-8", newline="\n").write(htex)

    # cover letter
    cl = io.open(os.path.join(SRC, "cover_letter.md"), encoding="utf-8").read().replace("\r\n", "\n")
    cl_body = []
    for blk in blocks(cl):
        if blk.startswith("# "):
            continue
        lines = blk.split("\n")
        if lines[0].startswith("Yuan Zhao"):
            cl_body.append(" \\\\\n".join(inline(l) for l in lines))
            continue
        if lines[0].startswith("**To:**") or lines[0].startswith("**Journal:**") or lines[0].startswith("**Manuscript:**"):
            cl_body.append(" \\\\\n".join(inline(l) for l in lines))
            continue
        cl_body.append(inline(blk.replace("\n", " ")))
    cltex = ("\\documentclass[11pt]{article}\n\\usepackage[margin=2.0cm]{geometry}\n"
             "\\usepackage[utf8]{inputenc}\n\\usepackage[T1]{fontenc}\n\\usepackage{newtxtext}\n"
             "\\usepackage{setspace}\n\\setstretch{1.08}\n\\setlength{\\parskip}{5pt}\n"
             "\\begin{document}\n\\thispagestyle{empty}\n"
             + "\n\n".join(cl_body) + "\n\\end{document}\n")
    io.open(os.path.join(OUT, "cover_letter.tex"), "w", encoding="utf-8", newline="\n").write(cltex)

    print("manuscript.tex written; references:", nrefs)


if __name__ == "__main__":
    main()
