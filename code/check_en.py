"""Consistency checks for the English manuscript draft.

Usage: python code/check_en.py
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / "manuscript"
FILES = [
    "00_title_abstract.md",
    "01_introduction.md",
    "02_theory.md",
    "03_data_methods.md",
    "04_results.md",
    "05_discussion.md",
]

def words(text: str) -> int:
    return len(text.split())

def main() -> int:
    problems = []
    texts = {name: (SEC / name).read_text(encoding="utf-8") for name in FILES}
    body = "\n\n".join(texts.values())

    abstract = texts["00_title_abstract.md"].split("## Abstract")[1].split("**Keywords")[0]
    n_abs = words(abstract)
    print(f"abstract words: {n_abs}")
    if n_abs > 250:
        problems.append(f"abstract exceeds 250 words ({n_abs})")

    for name in FILES[1:]:
        print(f"{name}: {words(texts[name])} words")

    # arithmetic checks
    checks = {
        "40/240 = 16.7%": abs(40 / 240 * 100 - 16.7) < 0.05,
        "27/170 = 15.9%": abs(27 / 170 * 100 - 15.9) < 0.05,
        "7/40 = 17.5%": abs(7 / 40 * 100 - 17.5) < 0.05,
        "6/30 = 20.0%": abs(6 / 30 * 100 - 20.0) < 0.05,
        "68/240 = 28.3%": abs(68 / 240 * 100 - 28.3) < 0.05,
        "45/170 = 26.5%": abs(45 / 170 * 100 - 26.5) < 0.05,
        "12/40 = 30.0%": abs(12 / 40 * 100 - 30.0) < 0.05,
        "11/30 = 36.7%": abs(11 / 30 * 100 - 36.7) < 0.05,
        "level quadrants A sum to 170": 68 + 27 + 22 + 53 == 170,
        "level quadrants full sum to 240": 98 + 40 + 28 + 74 == 240,
        "growth quadrants A sum to 170": 50 + 45 + 19 + 56 == 170,
        "growth quadrants full sum to 240": 70 + 68 + 27 + 75 == 240,
        "45-24+6 = 27 level A": 45 - 24 + 6 == 27,
        "68-35+7 = 40 level full": 68 - 35 + 7 == 40,
        "7.69 - 23.65 = -15.96": abs(7.69 - 23.65 + 15.96) < 0.005,
        "2.98+2.06+7.00+11.61 = 23.65": abs(2.98 + 2.06 + 7.00 + 11.61 - 23.65) < 0.005,
        "12.97+19.85+39.14+9.65 = 81.61": abs(12.97 + 19.85 + 39.14 + 9.65 - 81.61) < 0.005,
        "52.22+29.39 = 81.61": abs(52.22 + 29.39 - 81.61) < 0.005,
        "24+20-3 = 41": 24 + 20 - 3 == 41,
        "14+41 = 55": 14 + 41 == 55,
        "156-41 = 115": 156 - 41 == 115,
        "170-115 = 55": 170 - 115 == 55,
        "43.2-28.4 interaction 1.66": abs(4.18 + 3.83 + 1.66 - 9.67) < 0.02,
    }
    for label, ok in checks.items():
        print(("OK  " if ok else "FAIL"), label)
        if not ok:
            problems.append(label)

    # citation coverage
    refs = (SEC / "06_references.md").read_text(encoding="utf-8")
    keys = set()
    for m in re.finditer(r"\(([^()]{3,160}?(?:19|20)\d\d[a-z]?(?:,[^()]*?)?)\)", body):
        for part in m.group(1).split(";"):
            mm = re.match(r"\s*([A-Z][A-Za-z&.\- ]+?),?\s*(?:et al\.)?,?\s*((?:19|20)\d\d)", part)
            if mm:
                keys.add((mm.group(1).strip(), mm.group(2)))
    ref_keys = set()
    for line in refs.split("\n"):
        m = re.match(r"([A-Z][^(]+?)\((\d{4})\)", line.strip())
        if m:
            first = m.group(1).split(",")[0].strip().rstrip(".")
            ref_keys.add((first, m.group(2)))
    alias = {
        "IASB": "International Accounting Standards Board",
        "International Accounting Standards Board": "International Accounting Standards Board",
        "Ministry of Finance of China": "Ministry of Finance of China",
    }
    missing = []
    for key in sorted(keys):
        surname = key[0].split(" & ")[0].strip()
        surname = alias.get(surname, surname)
        if (surname, key[1]) not in ref_keys:
            missing.append(key)
    print(f"in-text keys: {len(keys)}; unmatched: {missing}")
    if missing:
        problems.append(f"unmatched citations: {missing}")

    # banned / AI-ish wording in body
    for kw in ["delve", "moreover", "furthermore", "it is worth noting", "in conclusion", "tapestry"]:
        if kw in body.lower():
            problems.append(f"banned phrase: {kw}")

    # American spellings in body (references excluded)
    for w in sorted(set(re.findall(r"\b\w+(?:ization|izing|ized|ize)\b", body))):
        if w == "size":
            continue
        problems.append(f"possible US spelling: {w}")

    print("\nPROBLEMS:" if problems else "\nALL CHECKS PASSED")
    for p in problems:
        print(" -", p)
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
