# Experiment 1 (pilot) summary

Model: `alibaba/qwen3-coder-30b-a3b` · design: gold · runs per condition: 3

## python/stocktrends (k* = 3)

| Condition | Agents | Pass rate (mean) | Runs | Tokens (mean) | Messages | Traceability | Note |
|---|---|---|---|---|---|---|---|
| G2 single agent | 1 | 0.00 | 0.00, 0.00, 0.00 | 10,897 | 0.0 | 0% |  |
| G4 random team, same sizes | 3 | 0.00 | 0.00, 0.00, 0.00 | 32,581 | 1.0 | 0% |  |
| GC one agent per class | 4 | 0.04 | 0.11, 0.00, 0.00 | 35,155 | 3.0 | 15% |  |
| G6 Infomap team (Co-Coder-style) | 4 | 0.04 | 0.11, 0.00, 0.00 | 35,155 | 3.0 | 15% | same team as GC |
| G7 criterion team (ours) | 3 | 0.00 | 0.00, 0.00, 0.00 | 32,564 | 2.0 | 0% |  |

## Go / no-go (pre-registered rules)

- G7 >= G4 on a majority of informative multi-agent tasks (at least 2, at least one strict win): **False** (1/1; strict wins 0)
- Tasks where every team scored 0 (excluded as uninformative): none
- G7 tokens <= 1.10 x G4 on every multi-agent task: **True**
- Single agent best where k* = 1: **False**
- G7 within 0.05 of G6: 1/1 tasks

## Experiment 1b (k* = 1 tasks)

- H3a single agent uses fewer tokens than split teams on every k*=1 task: **False** (0 tasks)
- H3b single agent at least as correct on a majority of informative k*=1 tasks: **False** (0/0)

**Verdict: NO-GO (provisional: not all pilot tasks/conditions are in yet)**

_3 runs per condition show direction and cost, not statistical proof._
