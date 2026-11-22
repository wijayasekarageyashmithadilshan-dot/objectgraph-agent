#!/usr/bin/env bash
# One command: fetch the data, test the code, regenerate every table and figure.
set -euo pipefail
pip install -r requirements.txt
bash scripts/fetch_devbench.sh
python -m pytest -q tests
python scripts/run_structural.py --devbench DevBench --out results
python scripts/run_reference_tests.py --devbench DevBench --out results   # optional, ~10 min
python scripts/make_paper_assets.py --results results --paper paper   # numbers, tables, figures for the paper
(cd paper && latexmk -pdf -interaction=nonstopmode main.tex ieee_access.tex)   # ICML + IEEE Access PDFs
python scripts/make_ieee_docx.py --template paper/Access-Template-2024.docx --out paper/ObjectGraph-Agent_IEEE-Access.docx   # IEEE Access Word manuscript
