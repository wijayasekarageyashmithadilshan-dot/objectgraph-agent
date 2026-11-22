# Experiment 1 (pilot): step by step on your laptop

You need Python 3.10+, git, an API key for the provider in prereg/plan.yaml (currently Vercel AI Gateway, `AI_GATEWAY_API_KEY`) and, for the C++/Java projects, Docker Desktop.

## 0. Set up (once)
```bash
pip install -r requirements.txt anthropic pyyaml
bash scripts/fetch_devbench.sh
export AI_GATEWAY_API_KEY=...           # terminal only; never in code, files or chat
```

## 1. Check the scorer (Phase 0, free)
DevBench's own answer code must pass all of its tests, and empty code must pass none.
```bash
python scripts/check_scorer.py --projects python/stocktrends python/lice python/TextCNN
```
For C++/Java, build DevBench's image once (it takes a while; on Apple Silicon it runs under emulation):
```bash
docker build --platform linux/amd64 -t devbench:complete DevBench/docker/complete
python scripts/check_scorer.py --projects cpp/xlsx2csv java/idcenter
```
Every project you run must show `usable YES`. If one shows NO, send me the output before going further.

## 2. Freeze the rules (Phase 0)
Open `prereg/plan.yaml`, set the exact model ID and today's date, then:
```bash
git add -A && git commit -m "pilot pre-registration" && git tag prereg-v1   # later amendments: prereg-v1.1, prereg-v1.2, ...
```
Do not edit `prereg/plan.yaml` after this. If you must, say so in the paper.

## 3. Run (Phase 2), one project at a time
```bash
python scripts/run_pilot.py --project python/stocktrends     # 5 teams x 3 runs, the cheapest; start here
python scripts/run_pilot.py --project python/lice            # the "don't split" test
python scripts/run_pilot.py --project python/TextCNN
python scripts/run_pilot.py --project cpp/xlsx2csv           # needs the Docker image
python scripts/run_pilot.py --project java/idcenter
```
Each run prints its pass rate, tokens and messages. Identical teams (for example your team = Infomap on xlsx2csv) are answered from the cache at no cost.
To test the setup for free first: `--provider fake --runs 0` (scores will be 0).

## 4. Measure and decide (Phases 3–4)
```bash
python scripts/analyse_pilot.py
```
This writes `results/pilot_summary.md`, a chart and the GO / NO-GO verdict, using the rules frozen in step 2.

## 5. Send me the results
```bash
zip -r pilot_results.zip results runs cache prereg
```
Upload `pilot_results.zip` here. I'll check it, analyse it, and put the results into the ICML draft.

## What every run leaves behind
`runs/pilot/<project>/<team>/run<N>/` contains:
- `report.html`, with steps 1–6 drawn as pictures;
- `code/`, the agents' code;
- `summary.json` and `score.json`.

`cache/` holds every Claude reply. Anyone can replay the whole pilot with `--offline`.

## No strong laptop? Use the cloud (free)
- **Google Colab** (`pilot_colab.ipynb`) runs the Python projects: stocktrends, lice and TextCNN. Upload the zip, then run the cells in order. Colab has no Docker, so it can't score C++ or Java.
- **GitHub Codespaces** runs everything, including C++/Java with Docker:
  1. Open the repo on GitHub (it is already public).
  2. Add `AI_GATEWAY_API_KEY` as a Codespaces secret.
  3. Click Code → Codespaces → Create.

  The `.devcontainer/` folder installs Python, Docker and DevBench automatically. Then follow steps 1–5 above in its terminal (including the `docker build`). Delete the codespace when you finish, so it stops using your free hours.
