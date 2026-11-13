#!/usr/bin/env bash
# Convert data/raw_pdf/*.pdf to -layout text and write it to data/text/.
#
# Why pdftotext rather than PyMuPDF:
#   find_tables() splits the thousands separators ("812 540 052 84") and the numbers cannot
#   be cast to float; pdftotext -layout keeps them intact ("812,540,052.84").
# Why not drive it from python subprocess:
#   a python subprocess that creates a pipe is refused by the sandbox in background jobs
#   (PermissionError WinError 5), so this is a plain bash loop calling the binary.
set -euo pipefail
cd "$(dirname "$0")/.."

PT="/d/texlive/2026/bin/windows/pdftotext.exe"
[ -x "$PT" ] || PT="pdftotext"

mkdir -p data/text
n=0
for f in data/raw_pdf/*.pdf; do
  b=$(basename "$f" .pdf)
  "$PT" -layout -enc UTF-8 "$f" "data/text/$b.txt"
  n=$((n + 1))
done
echo "[done] $n files -> data/text/"
