"""Extract the cash-flow and depreciation items needed for H2 from the consolidated cash-flow
statements and supplementary schedules in data/text/*.txt.

Why a separate parser: dep_fa (depreciation of fixed assets) is missing for 68/120 reports in
parse_fin.py, because it appears only in the cash-flow supplementary schedule and its label is
often split over two lines by -layout. Without depreciation, the capital burden in H2 collapses
into interest and is systematically understated.

Extraction rules (fixed: first hit per report, label must follow 'consolidated cash flow statement'):
  cfo      net cash flow from operating activities
  capex    cash paid for fixed assets, intangibles and other long-term assets
  dep_fa   depreciation of fixed assets, depletion of oil and gas assets, depreciation of
           productive biological assets
  am_ia_cf amortisation of intangible assets (cash-flow basis, stored separately from the
           income-statement am_ia)
  am_lt_cf amortisation of long-term deferred expenses
  disp_fa  loss on disposal of fixed assets, intangibles and other long-term assets

Unit: yuan (as in fin_panel). Values that cannot be extracted are left empty and reported in
fin_miss, never written as zero.
"""
import csv
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT = os.path.join(ROOT, "data", "text")
OUT = os.path.join(ROOT, "data", "cashflow_panel.csv")

MONEY = re.compile(r"-?\d{1,3}(?:,\d{3})+\.\d{2}|-?\d{6,}\.\d{2}")
KEYS = [
    ("cfo", ["经营活动产生的现金流量净额"]),
    ("capex", ["购建固定资产、无形资产和其他长期资产支付的现金"]),
    ("dep_fa", ["固定资产折旧、油气资产折耗、生产性生物资产折旧", "固定资产折旧"]),
    ("am_ia_cf", ["无形资产摊销"]),
    ("am_lt_cf", ["长期待摊费用摊销"]),
    ("disp_fa", ["处置固定资产、无形资产和其他长期资产的损失"]),
]


def norm(s):
    return re.sub(r"\s+", "", s)


def load(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    return t.split("\f")


def find_after(pages, key, start):
    """Find key after the start page and return the current-period amount (the first accounting
    amount on the line, not the last).

    Under -layout a cash-flow line often carries two amounts, 'current | prior', and taking the last
    one picks up the prior period by mistake; long labels are also split over 2-3 lines ('purchase of
    fixed assets, intangible assets and other long-' + 'term assets paid in cash'), so a short line
    without digits is held as pending and concatenated before matching.
    """
    nk = norm(key)
    for pi in range(start, len(pages)):
        buf = []
        for li, ln in enumerate(pages[pi].splitlines()):
            ms = MONEY.findall(ln)
            n = norm(ln)
            if ms:
                if nk in (n + "".join(buf[-3:])):
                    return float(ms[0].replace(",", "")), pi + 1, li + 1
                buf = []
            elif n and len(n) <= 30:
                buf.append(n)
    return None, None, None


def find_window(pages, prefix, start, span=2):
    """Match on a line prefix and take the first accounting amount on that line or within `span`
    following lines (the current period).

    Built for layouts such as capex, where the label is cut apart by the amount:
      ' purchase of fixed assets, intangible assets and other' /
      ' 251,318,947.22  214,536,255.30' / 'long-term assets paid in cash'
    """
    np_ = norm(prefix)
    for pi in range(start, len(pages)):
        lines = pages[pi].splitlines()
        for li, ln in enumerate(lines):
            if np_ in norm(ln):
                for k in range(0, span + 1):
                    if li + k >= len(lines):
                        break
                    ms = MONEY.findall(lines[li + k])
                    if ms:
                        return float(ms[0].replace(",", "")), pi + 1, li + k + 1
    return None, None, None


def main():
    rows, miss = [], []
    files = sorted(f for f in os.listdir(TXT) if f.endswith(".txt"))
    for fn in files:
        code, rest = fn.split("_", 1)
        year = rest[:4]
        kind = "H1" if rest[4:6] == "H1" else "A"
        pages = load(os.path.join(TXT, fn))
        # Start of the cash-flow statement: the first page headed 'consolidated cash flow statement'; the supplementary schedule follows
        start = 0
        for pi, pg in enumerate(pages):
            if "合并现金流量表" in pg:
                start = pi
                break
        rec = {"code": code, "year": year, "kind": kind}
        got = 0
        for name, keys in KEYS:
            val = page = line = None
            for k in keys:
                val, page, line = find_after(pages, k, start)
                if val is not None:
                    break
            if val is None and name == "capex":
                val, page, line = find_window(pages, "购建固定资产", start)
            rec[name] = "" if val is None else f"{val:.2f}"
            if name in ("cfo", "capex", "dep_fa"):
                rec[f"src_{name}"] = "" if page is None else f"p{page}L{line}"
            if val is not None:
                got += 1
        rows.append(rec)
        if got < 3:
            miss.append((code, year, kind, got))

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def cov(k):
        return sum(1 for r in rows if r[k] != "")

    print(f"[ok] {len(rows)} files -> {OUT}")
    for k in ("cfo", "capex", "dep_fa", "am_ia_cf", "am_lt_cf", "disp_fa"):
        print(f"  {k:10s} {cov(k):3d}/{len(rows)}")
    if miss:
        print(f"[warn] {len(miss)} files with fewer than 3 hits: {miss[:8]}")


if __name__ == "__main__":
    main()