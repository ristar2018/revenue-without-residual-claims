#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert the annual reports in data/raw_pdf to -layout plain text (table columns aligned) in
bulk, for regular-expression extraction.

Why not PyMuPDF's find_tables:
  in this batch of PDFs the thousands separators are split inside cells ('812 540 052 84' plus
  ', , .'), so the numbers returned by table.extract() cannot be cast to float directly;
  pdftotext -layout keeps the column alignment and the number stays intact as
  '812,540,052.84'.

Output: data/text/{code}_{year}.txt, pages separated by \f (as in pdftotext)
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "data", "raw_pdf")
OUT = os.path.join(ROOT, "data", "text")
PT = r"D:\texlive\2026\bin\windows\pdftotext.exe"
os.makedirs(OUT, exist_ok=True)


def main():
    files = sorted(f for f in os.listdir(PDF) if re.match(r"^\d{6}_\d{4}A\.pdf$", f))
    todo = [f for f in files if not os.path.exists(os.path.join(OUT, f[:-4] + ".txt"))]
    print(f"{len(files)} files in total, {len(todo)} to convert")
    ok = fail = 0
    for n, f in enumerate(todo, 1):
        src = os.path.join(PDF, f)
        dst = os.path.join(OUT, f[:-4] + ".txt")
        r = subprocess.run([PT, "-layout", "-enc", "UTF-8", src, dst],
                           capture_output=True)
        size = os.path.getsize(dst) if os.path.exists(dst) else 0
        if r.returncode == 0 and size > 5000:
            ok += 1
        else:
            fail += 1
            print(f"[FAIL] {f} rc={r.returncode} size={size} {r.stderr[:80]}", file=sys.stderr)
        if n % 20 == 0:
            print(f"  {n}/{len(todo)} ok={ok} fail={fail}")
    print(f"[done] ok={ok} fail={fail} -> {OUT}")


if __name__ == "__main__":
    main()
