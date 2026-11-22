# Deviations from the pre-registered pilot (reported in the paper)

| Date | Change | Why | Effect on conditions |
|---|---|---|---|
| 2026-11-22 | Scorer creates the test venv with `virtualenv` when `venv` has no pip | Colab's Python 3.13 lacks `ensurepip`; scoring crashed before any test ran | None (infrastructure) |
| 2026-11-22 | Python fragments of one file are merged by syntax: base classes before subclasses; if a class is written twice, the owner's version is kept | First smoke run (stocktrends, G7, run 0) scored 0/9. DevBench's class diagram draws `Instrument --> Renko` while the code has `Renko(Instrument)`, so subclass agents ran first and plain concatenation placed subclasses before their base class | Same rule for every multi-agent condition (G4, GC, G6, G7); single-agent output (G2) is unchanged |
| 2026-11-22 | TextCNN excluded from the pilot unless its scorer check becomes usable | `check_scorer.py`: DevBench's own answer passes 5/13 on Colab, so the pre-registered `usable_task` rule fails | Applies to all conditions |
