# Agent runs: how to make LLM results reproducible

An LLM does not always give the same answer twice, even at temperature 0. So "reproducible" here means **record and replay**:

- every model call is saved the first time it runs;
- anyone can rebuild every table from the saved calls without paying for API calls;
- anyone with a key can re-run the experiment live and should get results within the reported confidence intervals.

## 1. Freeze the plan before the first run (pre-registration)
- Commit `prereg/plan.yaml` containing:
  - the task list and dev/test split by project;
  - hypotheses H1–H4 with their thresholds;
  - the conditions G1–G7 and GC;
  - the edge weights and λ;
  - the token cap and the number of runs (3);
  - the model IDs, using **dated snapshot names, not aliases**.
- Tag that commit `prereg-v1` and write its hash into the paper. Nothing in that file changes after the first test-split run.

## 2. One door for every model call
All calls go through a single function, `objectgraph/llm.py::call(messages, model, params, run_id)`:
- `key = sha256(model + params + messages + run_id)`
- If the key is in `cache/*.jsonl`, return the stored response.
- Otherwise call the provider, then append one line to the cache containing the key, the request, the response, the token usage, the returned model version and a timestamp.
- `--offline` mode raises an error on any cache miss. This is how examiners replay the runs.

`run_id` (0, 1, 2) makes the three repeats separate cache entries, so all three are kept rather than one being reused.

## 3. Same conditions for everyone
- One small orchestrator is used for every condition. Only the work split changes.
- The same prompt templates (in `prompts/`, version-controlled) and the same decoding settings are used throughout.
- There is a hard token cap per run, enforced by the orchestrator. A run that hits the cap stops and is scored as-is.
- If G4 (random team) happens to equal G7, it is redrawn with the next seed.

## 4. Scoring in a sandbox
- Generated code runs only inside DevBench's Docker images (one per language), with the network off.
- The score is the reference tests passed ÷ total. Only tasks whose reference code passes its own tests are scored (`results/reference_tests.json`).
- Each run's files, logs and messages go to `runs/<condition>/<project>/<run_id>/`. Every message carries duty IDs, which gives the traceability metric.

## 5. Analysis is a script, not a spreadsheet
`scripts/analyse_agents.py` reads `runs/` and writes:
- `results/agents.json`;
- the paper tables (pass rate, tokens, 95% bootstrap CIs);
- Wilcoxon tests with Holm correction;
- Spearman ρ for H2;
- the split/no-split confusion table for H3.

The bootstrap uses a fixed seed. `make_paper_assets.py` then turns those results into the paper's macros, which replaces each `\pending{}`.

## 6. Order of work
1. **Pilot (go/no-go):** stocktrends (Py), xlsx2csv (C++) and idcenter (Java), running G2, G4 and G7 three times each = 27 runs on one model. The go/no-go decision depends on whether G7 beats G4 on pass rate or tokens. The pilot also gives the real cost per run.
2. **Full study:** all scored DevBench tasks plus added tasks, all conditions, 3 runs each, 2 models (one API model and one open-weight model through Ollama).
3. Release the cache with the code, on GitHub or Zenodo if it is too large.

## 7. Keys and safety
- Put the API key in an environment variable (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, …). Never put it in code, logs, the cache or a chat.
- The cache stores responses, not keys.
- Use an anonymised mirror of the repository for double-blind review (for example anonymous.4open.science).
