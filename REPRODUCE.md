# Where every number comes from

All numbers come from `results/structural.json` (made by `scripts/run_structural.py`) or `results/reference_tests.json` (made by `scripts/run_reference_tests.py`). Nothing is typed in by hand. DevBench is pinned to commit `bb593c1`, and the seed is `20261121`.

| Claim (as of 21 Nov 2026) | Value | Source |
|---|---|---|
| Projects with a class diagram | 22 / 22 | `structural.json` → `projects` |
| Projects that get a multi-agent team (k\* > 1, λ = 0) | 11 / 22 (Python 2, C++ 3, Java 5, JS 1) | `table_main.csv` → `k_star_duty` |
| Cut reduction vs 2,000 same-size random splits | 52–97% (all 11) | `cut_reduction_vs_random` |
| Largest p-value vs random | 0.0105 (login-registration) | `p_random` |
| Closed-form expected random cut vs sampled mean | within 0.4% | `closed_form_vs_sampled` |
| Duty-level teams that split a class | 0 / 22 | `splits_a_class` |
| Teams with higher MQ than one-agent-per-class | 8 / 11 (3 identical) | `mq_minus_one_per_class` |
| Teams identical to Infomap's partition | 4 / 11; ARI ≥ 0.75 in 9 / 11 | `structural.json` → `ari_vs_infomap` |
| k\* changed by λ ∈ {0, .05, .1, .2} | 0 / 22 | `table_lambda.csv` |
| Same k\* across the 81-point ±50% weight grid | 86% on average (79% for the 11 multi-agent projects) | `table_weights.csv` |
| Class-level graph: projects with k\* > 1 | 4 / 22 | `structural.json` → `class.k_star` |
| Python reference tests passing in full | lice 31/31, stocktrends 9/9, hone 12/12, geotext 9/9, readtime 12/12, particle-swarm-optimization 6/6 | `table_reference_tests.csv` |

## Known differences from the earlier pilot harness (3 Nov)

The pilot used different edge weights. It reported 15/22 multi-agent projects and lice = 3 agents. With this repo's pre-set defaults, lice is k\* = 1 and 11/22 projects are multi-agent. **From now on, this repo is the single source of truth.** Fix the weights before any LLM run, and report the weight-grid sensitivity alongside them.

## The paper
`scripts/make_paper_assets.py` writes `paper/generated/numbers.tex`, so every result number in `paper/main.tex` is a LaTeX macro (for example `\NMulti`, `\CutRedMin`). Tables and figures are generated the same way, and nothing in the paper is typed by hand. Red `[PENDING: …]` marks show results that do not exist yet. The paper is ready to submit only when there are none left. To use the official template, put `icml2026.sty` and `icml2026.bst` (from icml.cc) in `paper/`; `main.tex` picks them up automatically instead of the preview style.

## Two versions from one source (draft v0.2)
- `paper/main.tex` is the ICML version (anonymous; official `icml2026.sty` used when present).
- `paper/ieee_access.tex` is the IEEE Access version (named authors, statements, biographies, numbered IEEE references with DOIs via `IEEEtranN-doi.bst`). It uses the official `ieeeaccess.cls` from the IEEE Author Center when that file is in `paper/`; otherwise IEEEtran with a labelled preview header.
- The shared text is in `paper/content/` (abstract, body, appendix) and `paper/macros.tex`.
- Red `[PENDING: …]` marks results that don't exist yet. Blue `[TO ADD: …]` marks author details still to be supplied. Both must be gone before submission.

## IEEE Access Word manuscript (draft v0.3)
`scripts/make_ieee_docx.py` fills IEEE's official `Access-Template-2024.docx` (in `paper/`) with the paper, keeping its styles, title block, headers, footers and two-column layout. It uses the same generated numbers, numbers the references in citation order, and refuses to build if any reference is uncited. Export the PDF from Word (File → Save As → PDF) so the Word file and the PDF match exactly, as IEEE requires.
