# Deviations from the pre-registered pilot (reported in the paper)

| Date | Change | Why | Effect on conditions |
|---|---|---|---|
| 2026-11-22 | Scorer creates the test venv with `virtualenv` when `venv` has no pip | Colab's Python 3.13 lacks `ensurepip`; scoring crashed before any test ran | None (infrastructure) |
| 2026-11-22 | Python fragments of one file are merged by syntax: base classes before subclasses; a class written by several agents is rebuilt method by method, each method taken from the agent assigned that duty. Verified with zero model calls by `scripts/check_harness.py` (DevBench's answer code split per team and merged reaches the unsplit score for every condition: stocktrends 9/9, lice 31/31) | First smoke run (stocktrends, G7, run 0) scored 0/9. DevBench's class diagram draws `Instrument --> Renko` while the code has `Renko(Instrument)`, so subclass agents ran first and plain concatenation placed subclasses before their base class | Same rule for every multi-agent condition (G4, GC, G6, G7); single-agent output (G2) is unchanged |
| 2026-11-22 | TextCNN excluded from the pilot unless its scorer check becomes usable | `check_scorer.py`: DevBench's own answer passes 5/13 on Colab, so the pre-registered `usable_task` rule fails | Applies to all conditions |
| 2026-11-22 | Bare `duty: Class.method` lines are turned into comments (`# duty: ...` / `// duty: ...`) before merging | The smoke run's code wrote the requested traceability marker without `#`; in Python that line is an annotation that raises NameError at import, so 0 tests could run. The prompt is unchanged (cache keys unchanged) | Same rule for every condition |
| 2026-11-23 | Second model (DeepSeek V4.1 Flash) re-run with hidden reasoning switched off | Attempt 1 returned empty answers in 37 of 45 calls: the model used the full 8,000-token output budget for hidden reasoning, so no code was produced and no condition could be scored | Applies to every condition of the second model; attempt 1 kept as invalid |

## 2026-11-23 — MQ vectorised (no change in numbers)
`criterion.mq` now computes the group-to-group weights as Bᵀ W B with a
one-hot membership matrix B instead of a Python loop over group pairs. The
formula is unchanged; a randomised check (k = 1, 3, 7, 40 on a 40-node graph)
matches the old function to floating-point precision and all tests pass. The
change was needed because the 81-setting weight grid on RealBench (up to 115
duties) took over 10 minutes.

## 2026-11-23 — RealBench structural analysis (exploratory, zero model calls)
Added `objectgraph/realbench.py`, `scripts/run_realbench_structural.py` and
`docs/realbench_mapping.md`. This is an exploratory structural analysis, not
part of the sealed plan; any agent runs on RealBench will be registered in a
new plan amendment and tag before the first model call.

## 2026-11-23 — Experiment 2 harness fixed before any model call (plan amendment v1.8)
Zero-call checks on the 12 listed RealBench projects (reference tests; reference code
split per team, merged and scored with `--provider fake`) found and fixed:
- **Design reading:** file paths from `tree.txt` (duplicate file names were merged),
  an owner for every file, class names qualified by full path. The selection rule was
  re-applied unchanged; the task list in plan v1.8 is its output (17 projects).
- **Block parsing (all experiments):** a code block now ends only at a fence on its own
  line, so ``` inside a docstring no longer cuts a file short. Paths in backticks accepted.
- **Merge v2 (Experiment 2 only; the pilot keeps v1 so its cached runs reproduce):**
  units in source order, then sorted so names used at import time (base classes,
  decorators, annotations, defaults, module statements) are defined first; class members
  keep their own indentation (re-indenting changed multi-line strings); property getter
  and setter stay together; a top-level function comes from the agent that owns it.
- **Scoring:** RealBench's tests run with pytest in a separate environment
  (`scripts/realbench_test_requirements.txt`, pins from the reference check: mcp 1.8.1,
  pydantic < 2.11). Empty source files (bare `__init__.py`) are kept, since they hold no code.
After the fixes, every condition reproduces the reference score on every usable task.

## 2026-11-23 — Merge v2 fix after the first 7 paid Experiment 2 runs (one task)
The first paid runs (pab1it0_adx-mcp-server, 7 runs, then the OpenRouter credit ran out)
showed a merge fault the reference-code harness could not reveal, because RealBench's own
code never puts a multi-line `from x import (...)` in two fragments: imports were
de-duplicated line by line, which broke parenthesised imports (G4 run 0: IndentationError).
Merge v2 now (a) de-duplicates whole import statements, (b) puts `from __future__` imports
and the module docstring first, and (c) ignores a fragment whose author owns nothing in
that file (a stub of another agent's file), unless it is the only source of some class or
function. The rule is the same for every condition. The harness check still reproduces the
reference on every condition and task. The 7 runs are re-merged from the cached replies
(no new calls); only G4 run 0 changes (0 -> 4 of 25 tests). The remaining zero scores are
genuine (e.g. G7/GC: the agent owning server.py imported main.py while main.py imports
server.py, a circular import created by the two agents' own code).

## 2026-11-23 — Experiment 2 moved to the Vercel AI Gateway (plan amendment v1.9)
OpenRouter refused further calls (402, credit exhausted) after 9 runs (adx-mcp-server 7,
gattino 2). The same dated model is served by the Vercel AI Gateway, so Experiment 2 is run
there in full, the 9 runs included; the OpenRouter runs are archived in
results/experiment_2_openrouter_partial/ and not analysed. Nothing else changes.

## 2026-11-23 — Experiment 2b registered (plan amendment v1.10)
A stronger open-weight model (Nemotron 3 Ultra, OpenRouter free endpoint) reruns G2, G4 and
G7 once on the 9 usable Experiment 2 tasks. Registered after seeing Experiment 2, before any
call with this model. Code changes for the free endpoint: no automatic SDK retries for `:free`
models (each attempt counts against the daily quota) and a clean stop at the daily limit;
`run_realbench.py --block` selects the plan block; `analyse_exp2.py --conditions` analyses a
subset of conditions with the same registered tests.

## 2026-11-23 — Experiment 2b moved to NVIDIA's API (plan amendment v1.11)
Same model (Nemotron 3 Ultra) served directly by NVIDIA, which removes the free OpenRouter
endpoint's daily limit; Experiment 2b therefore runs all five conditions once. Only two
one-line connectivity checks were made with this model before registration.

## 2026-11-23 — Experiment 2b moved from Colab to GitHub Actions (infrastructure only)
The first Colab attempt of Experiment 2b could not be kept running for the several hours
the large model needs (the browser session must stay open). Experiment 2b is therefore run
on GitHub Actions (`.github/workflows/exp2b.yml`), one job per task, with the same plan,
model, prompts, scorer pins and analysis. No result of the Colab attempt was looked at; it
is discarded and the Actions run is the registered run. Each job first re-runs RealBench's
reference tests and stops before any model call unless they pass exactly as many tests as in
Experiment 2, so the test environment cannot differ silently.
