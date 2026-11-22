# Experiment 1 (pilot) summary

Model: `alibaba/qwen3-coder-30b-a3b` · design: gold · runs per condition: 3

## python/lice (k* = 1)

| Condition | Agents | Pass rate (mean) | Runs | Tokens (mean) | Messages | Traceability | Note |
|---|---|---|---|---|---|---|---|
| G2 single agent | 1 | 0.00 | 0.00, 0.00, 0.00 | 4,172 | 0.0 | 33% |  |
| G4 random team, same sizes | 5 | 0.00 | 0.00, 0.00, 0.00 | 41,127 | 9.0 | 16% |  |
| GC one agent per class | 5 | 0.00 | 0.00, 0.00, 0.00 | 20,986 | 4.0 | 76% |  |
| G6 Infomap team (Co-Coder-style) | 1 | 0.00 | 0.00, 0.00, 0.00 | 4,172 | 0.0 | 33% | same team as G2 |
| G7 criterion team (ours) | 1 | 0.00 | 0.00, 0.00, 0.00 | 4,172 | 0.0 | 33% | same team as G2 |

## python/stocktrends (k* = 3)

| Condition | Agents | Pass rate (mean) | Runs | Tokens (mean) | Messages | Traceability | Note |
|---|---|---|---|---|---|---|---|
| G2 single agent | 1 | 0.11 | 0.11, 0.11, 0.11 | 3,681 | 0.0 | 0% |  |
| G4 random team, same sizes | 3 | 0.11 | 0.11, 0.11, 0.11 | 13,511 | 1.0 | 95% |  |
| GC one agent per class | 4 | 0.11 | 0.11, 0.11, 0.11 | 17,879 | 3.0 | 92% |  |
| G6 Infomap team (Co-Coder-style) | 4 | 0.11 | 0.11, 0.11, 0.11 | 17,879 | 3.0 | 92% | same team as GC |
| G7 criterion team (ours) | 3 | 0.11 | 0.11, 0.11, 0.11 | 14,162 | 2.0 | 85% |  |

## Go / no-go (pre-registered rules)

- G7 >= G4 on a majority of informative multi-agent tasks (at least 2, at least one strict win): **False** (1/1; strict wins 0)
- Tasks where every team scored 0 (excluded as uninformative): none
- G7 tokens <= 1.10 x G4 on every multi-agent task: **True**
- Single agent best where k* = 1: **False**
- G7 within 0.05 of G6: 1/1 tasks

**Verdict: NO-GO (provisional: not all pilot tasks/conditions are in yet)**

_3 runs on 5 tasks show direction and cost, not statistical proof._
