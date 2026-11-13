"""Assemble the English manuscript from section files.

Usage: python code/assemble_en.py
Writes manuscript/manuscript_v1.md
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / "manuscript"
FILES = [
    "00_title_abstract.md",
    "01_introduction.md",
    "02_theory.md",
    "03_data_methods.md",
    "04_results.md",
    "05_discussion.md",
    "06_references.md",
    "07_back_matter.md",
    "08_tables_figures.md",
]

def main() -> None:
    parts = []
    for name in FILES:
        text = (SEC / name).read_text(encoding="utf-8").strip()
        parts.append(text)
    out = "\n\n".join(parts) + "\n"
    (SEC / "manuscript_v1.md").write_text(out, encoding="utf-8")
    words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-−.%]*", out))
    print(f"wrote manuscript_v1.md chars={len(out)} approx_words={words}")

if __name__ == "__main__":
    main()
