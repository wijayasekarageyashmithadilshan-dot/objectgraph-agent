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
