# -*- coding: utf-8 -*-
"""Build the English submission manuscript as .docx.

Reads manuscript/00-08 and writes manuscript/manuscript_v1.docx.
Elsevier TMP style: A4, Times New Roman 12 pt, 1.5 spacing, continuous line
numbers, page numbers, tables and figures after the references.

Usage: python code/build_docx_en.py
"""
import io
import json
import os
import re

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(ROOT, "manuscript")
FIG = os.path.join(ROOT, "figures")
OUT = os.path.join(SEC, "manuscript_v1.docx")

BODY = 12
SMALL = 10
TINY = 8

FIG_FILES = [
    ("Figure 1", "en_fig1_mechanism.png", 16.0),
    ("Figure 2", "en_fig2_quadrant.png", 16.0),
    ("Figure 3", "en_fig3_waterfall.png", 16.0),
    ("Figure 4", "en_fig4_firm_scatter.png", 11.0),
    ("Figure 5", "en_fig5_fee_channel.png", 11.0),
    ("Figure 6", "en_fig6_forest.png", 11.0),
]

TABLE_WIDTHS = {
    1: [3.2, 1.0, 1.3, 1.6, 2.0, 1.1, 3.0, 1.4, 1.4],
    2: [6.2, 3.2, 3.2, 3.2],
    3: [5.6, 2.7, 2.7, 2.7, 1.8],
    4: [0.8, 4.1, 3.8, 1.8, 1.7, 1.6, 2.2],
    5: [5.4, 3.5, 3.5, 3.4],
    6: [6.2, 3.2, 3.2, 3.2],
}


# ---------------------------------------------------------------- low level
def font(run, size=BODY, bold=False, italic=False, name="Times New Roman"):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), name)


def page_numbers(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Page ")
    font(run, 9)
    for instr in ("PAGE", "NUMPAGES"):
        fld = OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"), instr)
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = "1"
        r.append(t)
        fld.append(r)
        p._p.append(fld)
        if instr == "PAGE":
            sep = p.add_run(" of ")
            font(sep, 9)


def line_numbers(section):
    sectPr = section._sectPr
    ln = OxmlElement("w:lnNumType")
    ln.set(qn("w:countBy"), "1")
    ln.set(qn("w:restart"), "continuous")
    ln.set(qn("w:distance"), "284")
    sectPr.append(ln)


def shade(cell, hex_fill="F2F2F2"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def cell_margins(table, top=40, bottom=40, left=60, right=60):
    tblPr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement("w:" + side)
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


def three_line(table, n_rows):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        if edge == "top":
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "12")
        elif edge == "bottom":
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), "12")
        else:
            el.set(qn("w:val"), "nil")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)
    for cell in table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        b = OxmlElement("w:tcBorders")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:color"), "000000")
        b.append(bottom)
        tcPr.append(b)


def keep(paragraph, nxt=True):
    paragraph.paragraph_format.keep_with_next = nxt
    paragraph.paragraph_format.keep_together = True


# ---------------------------------------------------------------- math
GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ",
    "epsilon": "ε", "theta": "θ", "lambda": "λ", "mu": "μ", "pi": "π",
    "sigma": "σ", "Sigma": "Σ", "phi": "φ", "omega": "ω", "times": "×",
    "cdot": "·", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥",
    "approx": "≈", "neq": "≠", "pm": "±", "sum": "Σ", "ln": "ln",
    "log": "log", "max": "max", "min": "min", "in": "∈",
}


def tex_tokens(tex):
    """Very small TeX subset -> [(text, level)] with level -1 sub, 1 sup."""
    out = []
    i = 0
    n = len(tex)

    def push(text, level):
        if text:
            out.append((text, level))

    while i < n:
        ch = tex[i]
        if ch == "\\":
            j = i + 1
            while j < n and tex[j].isalpha():
                j += 1
            cmd = tex[i + 1:j]
            if cmd == "frac":
                # \frac{A}{B} -> (A)/(B)
                def grab(k):
                    while k < n and tex[k] in " \t":
                        k += 1
                    if k < n and tex[k] == "{":
                        depth = 1
                        k += 1
                        start = k
                        while k < n and depth:
                            if tex[k] == "{":
                                depth += 1
                            elif tex[k] == "}":
                                depth -= 1
                            k += 1
                        return tex[start:k - 1], k
                    return tex[k:k + 1], k + 1
                num, k = grab(j)
                den, k = grab(k)
                push("(", 0)
                for t, lv in tex_tokens(num):
                    push(t, lv)
                push(")/(", 0)
                for t, lv in tex_tokens(den):
                    push(t, lv)
                push(")", 0)
                i = k
                continue
            if cmd in ("", " "):
                i = j
                continue
            push(GREEK.get(cmd, cmd), 0)
            i = j
            continue
        if ch in "_^":
            level = -1 if ch == "_" else 1
            j = i + 1
            if j < n and tex[j] == "{":
                depth = 1
                j += 1
                start = j
                while j < n and depth:
                    if tex[j] == "{":
                        depth += 1
                    elif tex[j] == "}":
                        depth -= 1
                    j += 1
                push(tex[start:j - 1], level)
                i = j
            else:
                push(tex[j:j + 1], level)
                i = j + 1
            continue
        if ch in "{}":
            i += 1
            continue
        if ch == "-":
            push("−", 0)
            i += 1
            continue
        push(ch, 0)
        i += 1
    return out


def add_math(paragraph, tex, size=BODY, bold=False):
    for text, level in tex_tokens(tex):
        run = paragraph.add_run(text)
        font(run, size, bold=bold)
        if level < 0:
            run.font.subscript = True
        elif level > 0:
            run.font.superscript = True
    return paragraph


INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|\\\(.+?\\\))")


def add_inline(paragraph, text, size=BODY, bold=False):
    for tok in INLINE.split(text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            r = paragraph.add_run(tok[2:-2])
            font(r, size, bold=True)
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = paragraph.add_run(tok[1:-1])
            font(r, size, bold=bold, italic=True)
        elif tok.startswith("\\(") and tok.endswith("\\)"):
            add_math(paragraph, tok[2:-2], size, bold)
        else:
            r = paragraph.add_run(tok)
            font(r, size, bold=bold)


# ---------------------------------------------------------------- markdown
def parse_blocks(path):
    text = io.open(path, encoding="utf-8").read()
    lines = text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("\\["):
            buf = [line]
            while not buf[-1].strip().endswith("\\]"):
                i += 1
                buf.append(lines[i].rstrip())
            tex = " ".join(x.strip() for x in buf)
            tex = tex.replace("\\[", "").replace("\\]", "").strip()
            blocks.append(("eq", tex))
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            blocks.append(("h%d" % len(m.group(1)), m.group(2).strip()))
            i += 1
            continue
        if line.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                raw = lines[i].strip().strip("|")
                cells = [c.strip() for c in raw.split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            blocks.append(("table", rows))
            continue
        if line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:].strip())
                i += 1
            blocks.append(("ul", items))
            continue
        buf = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|\||-\s|\\\[)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        blocks.append(("p", " ".join(buf)))
    return blocks


def scan_mentions(raw):
    """(kind, number) pairs for 'Table 3', 'Tables 1 and 2', 'Figures 3-4'."""
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


def float_items():
    """Tables 1-5, appendix Table A2 and figure captions, keyed by number."""
    blocks_ = parse_blocks(os.path.join(SEC, "08_tables_figures.md"))
    tables, figs, cur, mode = {}, {}, None, None
    for kind, val in blocks_:
        if kind == "h2":
            title = val.strip()
            m = re.match(r"^(?:Appendix\s+)?Table\s+(A?\d+)$", title)
            if m:
                cur, mode = m.group(1), "table"
                tables[cur] = []
                continue
            if title.lower().startswith("figure"):
                cur, mode = None, "fig"
                continue
        if mode == "table" and cur:
            tables[cur].append((kind, val))
        elif mode == "fig" and kind == "p" and val.startswith("**Figure"):
            m = re.match(r"^\*\*Figure\s+(\d+)\.", val)
            if m:
                figs[m.group(1)] = val
    return tables, figs


def emit_table(doc, items, idx):
    for kind, val in items:
        if kind == "p" and val.startswith("**Table"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.0
            add_inline(p, val, SMALL)
            keep(p)
        elif kind == "table":
            add_table(doc, val, idx)
        elif kind == "p" and val.startswith("*Notes"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(10)
            p.paragraph_format.line_spacing = 1.0
            add_inline(p, val, 8)
        elif kind == "p" and val.startswith("**Panel"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            add_inline(p, val, 9)


def emit_figure(doc, n, caption):
    label, fname, width = FIG_FILES[n - 1]
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.add_run().add_picture(os.path.join(FIG, fname), width=Cm(width))
    keep(p)
    c = doc.add_paragraph()
    c.paragraph_format.space_before = Pt(0)
    c.paragraph_format.space_after = Pt(12)
    c.paragraph_format.line_spacing = 1.0
    add_inline(c, caption, 10)


def body_para(doc, text, size=BODY, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
              space_after=6, indent=None):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.5
    if indent:
        pf.first_line_indent = Cm(indent)
    add_inline(p, text, size)
    return p


def heading(doc, text, level):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(14 if level == 2 else 10)
    pf.space_after = Pt(6 if level == 2 else 4)
    pf.line_spacing = 1.5
    r = p.add_run(text)
    font(r, BODY, bold=True, italic=(level == 3))
    keep(p)
    return p


# ---------------------------------------------------------------- tables
def add_table(doc, rows, idx):
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    table = doc.add_table(rows=len(rows), cols=ncol)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = TABLE_WIDTHS.get(idx, [16.0 / ncol] * ncol)
    if len(widths) != ncol:
        widths = [16.0 / ncol] * ncol
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    table._tbl.tblPr.append(layout)
    for j, w in enumerate(widths):
        table.columns[j].width = Cm(w)
    size = TINY if idx in (1, 3, 4, 5) else 9
    for r_i, row in enumerate(rows):
        for c_i, val in enumerate(row):
            cell = table.cell(r_i, c_i)
            cell.width = Cm(widths[c_i])
            parts = val.split("<br>")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            if c_i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif r_i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for k, part in enumerate(parts):
                if k:
                    p.add_run().add_break()
                add_inline(p, part, size, bold=(r_i == 0))
            if r_i == 0:
                shade(cell)
    three_line(table, len(rows))
    cell_margins(table)
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    head = table.rows[0]._tr.get_or_add_trPr()
    head.append(OxmlElement("w:tblHeader"))
    return table


# ---------------------------------------------------------------- document
def main():
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(BODY)
    sec = doc.sections[0]
    sec.page_height = Cm(29.7)
    sec.page_width = Cm(21.0)
    for attr in ("top_margin", "bottom_margin"):
        setattr(sec, attr, Cm(2.54))
    sec.left_margin = Cm(2.54)
    sec.right_margin = Cm(2.54)
    line_numbers(sec)
    page_numbers(sec)

    # ---- title page
    blocks = parse_blocks(os.path.join(SEC, "00_title_abstract.md"))
    title = blocks[0][1]
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(60)
    p.paragraph_format.space_after = Pt(24)
    r = p.add_run(title)
    font(r, 16, bold=True)

    meta = json.load(io.open(os.path.join(SEC, "authors.json"), encoding="utf-8"))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    for i, a in enumerate(meta["authors"]):
        if i:
            font(p.add_run(", "), 12)
        font(p.add_run(a["name"]), 12)
        r = p.add_run(a["aff"] + ("*" if a.get("corresponding") else ""))
        font(r, 12)
        r.font.superscript = True

    for af in meta["affiliations"]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(af["label"])
        font(r, 10, italic=True)
        r.font.superscript = True
        font(p.add_run(" %s, %s, %s, %s" % (af["organization"], af["city"], af["postcode"], af["country"])),
             10, italic=True)

    cor = next(a for a in meta["authors"] if a.get("corresponding"))
    for line, size, italic in (
        ("", 10, False),
        ("* Corresponding author. E-mail: %s" % cor["email"], 10, False),
        ("", 10, False),
        ("Manuscript prepared for Tourism Management Perspectives (Elsevier)", 10, True),
        ("Main text 9,407 words; abstract 225 words; 5 tables (plus an appendix table); 6 figures; 47 references", 10, False),
    ):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        if line:
            font(p.add_run(line), size, italic=italic)

    doc.add_page_break()

    # ---- abstract
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run("Abstract")
    font(r, BODY, bold=True)
    for kind, val in blocks[1:]:
        if kind == "p" and val.startswith("**Keywords:**"):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.5
            add_inline(p, val)
        elif kind == "p":
            body_para(doc, val)

    hp = io.open(os.path.join(SEC, "07_back_matter.md"), encoding="utf-8").read()
    items = [ln[2:].strip() for ln in hp.split("\n") if ln.startswith("- ")]
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run("Highlights")
    font(r, BODY, bold=True)
    for it in items:
        bp = doc.add_paragraph(style="List Bullet")
        bp.paragraph_format.space_after = Pt(4)
        bp.paragraph_format.line_spacing = 1.15
        add_inline(bp, it, 11)

    doc.add_page_break()

    # ---- body
    body_blocks = []
    for name in ("01_introduction.md", "02_theory.md", "03_data_methods.md",
                 "04_results.md", "05_discussion.md"):
        for kind, val in parse_blocks(os.path.join(SEC, name)):
            body_blocks.append((name, kind, val))

    tmap, fmap = float_items()
    first_any, first_res = {}, {}
    for i, (name, kind, val) in enumerate(body_blocks):
        if kind != "p":
            continue
        for fk, n in scan_mentions(val):
            first_any.setdefault((fk, n), i)
            if name.startswith("04_"):
                first_res.setdefault((fk, n), i)

    plan = {}
    for fk, nums in (("table", [int(k) for k in tmap if k.isdigit()]),
                     ("fig", [int(k) for k in fmap])):
        for n in sorted(nums):
            a = first_res.get((fk, n), first_any.get((fk, n), len(body_blocks) - 1))
            plan.setdefault(a, []).append((fk, n))
            print("  %-5s %d -> body block %d" % (fk, n, a))

    first = True
    carry = []
    for i, (name, kind, val) in enumerate(body_blocks):
        if kind == "h2":
            heading(doc, val, 2)
            first = False
        elif kind == "h3":
            heading(doc, val, 3)
        elif kind == "p":
            body_para(doc, val)
            carry.extend(plan.get(i, []))
            if carry:
                fk, n = carry.pop(0)
                if fk == "table":
                    emit_table(doc, tmap[str(n)], n)
                else:
                    emit_figure(doc, n, fmap[str(n)])
        elif kind == "eq":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            tex = val
            if "frac{P_{it}}{R_{it}}" in tex:
                tex = ("P_{it}/R_{it} = [(P_{it} + M_{it} + I_{it} + D_{it})/R_{it}]"
                       " - M_{it}/R_{it} - I_{it}/R_{it} - L_{it}/R_{it} - D_{it}/R_{it}")
            add_math(p, tex, BODY)

    # ---- references
    doc.add_page_break()
    heading(doc, "References", 2)
    refs = io.open(os.path.join(SEC, "06_references.md"), encoding="utf-8").read()
    for line in refs.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^-\s+", "", line)
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Cm(0.75)
        pf.first_line_indent = Cm(-0.75)
        pf.space_after = Pt(6)
        pf.line_spacing = 1.15
        add_inline(p, line, 11)

    # ---- declarations (from 07_back_matter.md)
    doc.add_page_break()
    bm = io.open(os.path.join(SEC, "07_back_matter.md"), encoding="utf-8").read().replace("\r\n", "\n")
    for block in bm.split("\n# "):
        block = block.lstrip("# ").strip("\n")
        if not block:
            continue
        head, _, rest = block.partition("\n")
        if head.strip().lower() in ("highlights", "graphical abstract"):
            continue
        heading(doc, head.strip(), 2)
        for para in [x.strip() for x in rest.split("\n\n") if x.strip()]:
            body_para(doc, para)

    # ---- appendix table
    doc.add_page_break()
    heading(doc, "Appendix A. Supplementary table", 2)
    emit_table(doc, tmap["A2"], 6)

    doc.save(OUT)
    print("wrote", OUT, round(os.path.getsize(OUT) / 1024, 1), "KB")


if __name__ == "__main__":
    main()
