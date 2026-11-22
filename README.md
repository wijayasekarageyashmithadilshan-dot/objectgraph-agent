# ObjectGraph-Agent

Code and data for the paper *"When Should a Software Task Be Split Across Large Language Model Agents? Sizing Multi-Agent Teams from Domain Models"* (Yashmitha Dilshan, Informatics Institute of Technology, Colombo).

ObjectGraph-Agent turns a software design (a UML class diagram) into a graph of duties and scores cohesion and coupling. From that it decides whether the work should be split across LLM agents, how many agents to use, and which duties each agent owns. It does all of this before any code is written.

**Status (22 Nov 2026):**
- The structural results on all 22 DevBench projects are complete and reproducible.
- The agent pipeline (Claude API, five comparison teams, DevBench scoring, step-by-step reports) is built and tested with a fake model.
- The pilot runs are in progress.

## What is in this repository

| Folder / file | What it contains |
|---|---|
| `objectgraph/` | The method: UML parser, duty graph, MQ criterion, the five teams, the agent orchestrator, scoring, replay cache, reports |
| `scripts/` | One script per step: structural study, scorer check, pilot runs, analysis, paper figures, IEEE Word manuscript |
| `tests/` | Unit tests (`python -m pytest tests`) |
| `results/` | Generated results: `structural.json`, tables, figures, reference-test checks |
| `prereg/plan.yaml` | The pre-registered experiment rules, tagged `prereg-v1` before the first run |
| `paper/` | Manuscript sources: IEEE Access (Word and LaTeX) and ICML (LaTeX) |
| `cache/`, `runs/` | Added after agent runs: every Claude reply and every run's code, scores and report |
| `RUN_PILOT.md`, `pilot_colab.ipynb` | How to run the experiment (laptop, Colab or Codespaces) |
| `REPRODUCE.md` | Where every number in the paper comes from |

DevBench itself is not copied here: `scripts/fetch_devbench.sh` downloads it at the pinned commit (Apache-2.0).

## Reproduce everything

```bash
bash reproduce.sh
```

This runs four steps:

1. Installs pinned dependencies.
2. Fetches DevBench at commit `bb593c1`.
3. Runs the unit tests.
4. Regenerates every table and figure in `results/`.

The structural run takes about 45 s on 2 CPU cores. All random draws use the fixed seed `20261121`, and running it twice gives byte-identical `results/structural.json`.

## Method in one paragraph

1. Each method in the class diagram becomes a **duty**. A class with no methods becomes a single state duty.
2. Duties are linked with weighted edges:
   - same class: 1.0
   - composition, aggregation or inheritance: 0.5
   - "uses" or association: 0.25
   - a method signature that names another class: 0.5
3. Average-linkage clustering gives a team for every size k = 1..n.
4. Each team is scored with Mancoridis' MQ.
5. The chosen size is **k\* = argmax MQ(k) − λ(k−1)/(n−1)**.

## Controls computed

| Control | What it checks |
|---|---|
| 2,000 random partitions with the same group sizes | Gives a p-value for the cut weight |
| Closed-form expected random cut | Checks the sampled random baseline |
| One agent per class (GC) | Is the team better than splitting by class? |
| Louvain and Infomap | Infomap is Co-Coder's partitioner |
| λ ∈ {0, 0.05, 0.1, 0.2} | Sensitivity to the per-agent cost |
| 81-point ±50% weight grid | Sensitivity to the edge weights |

## Layout

```
objectgraph/   uml.py (Mermaid parser) · graph.py (duty graph) · criterion.py (MQ, k*, controls)
scripts/       run_structural.py · run_reference_tests.py · fetch_devbench.sh
tests/         unit tests (parser, MQ, closed form)
results/       generated: structural.json, table_*.csv, figures/mq_curves.png
```

See `REPRODUCE.md` for which script produces which number, `RUN_WITH_CLAUDE.md` for a single run, and `RUN_PILOT.md` for Experiment 1.

## License and citation
The code is released under the MIT License (`LICENSE`). See `CITATION.cff` for how to cite it.
