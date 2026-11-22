# Run your method with the Anthropic API

## On your laptop (or in Claude Code on your laptop)

Run these commands from the repo folder:

```bash
pip install -r requirements.txt anthropic
bash scripts/fetch_devbench.sh
export ANTHROPIC_API_KEY=...        # set it in your terminal; never in code or chat

# 1) See steps 1-4 first (no API calls, free):
python scripts/run_pipeline.py --project python/stocktrends --no-agents

# 2) Full run: Claude writes the domain model from the PRD, then the agent team builds the code:
python scripts/run_pipeline.py --project python/stocktrends --design extracted \
    --provider anthropic --model claude-sonnet-5-5 --run-id 0

# 3) Repeats (the pilot uses 3): --run-id 1 and --run-id 2
# 4) Same run with the gold design (upper bound): --design gold
# 5) Rebuild everything later with no API calls: add --offline
```

Open `runs/python__stocktrends/<design>/criterion/run<N>/report.html` to see every step:

1. domain model
2. duty graph
3. cohesion, coupling and team size
4. who does what
5. agent run, hand-overs and tokens
6. test score

The `cache/` folder holds every Claude reply. Keep it, because it is what makes your results reproducible.

## Which projects

Python projects are scored here directly. The two Python projects that get a team are `python/stocktrends` (its answer code passes 9/9 tests through our scorer) and `python/TextCNN` (needs internet for its model download). C++ and Java projects (`cpp/xlsx2csv`, `java/idcenter`, …) produce steps 1–5, but need DevBench's Docker images for step 6. That step comes next.

## Cost control

- `--budget` caps the total tokens per run (default 200,000).
- The tokens for every call are in `run.json`.
- Test once with a cheaper model, then pin the exact model you will report.
