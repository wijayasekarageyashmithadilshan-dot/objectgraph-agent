"""Analyse Experiment 1 and apply the pre-registered go/no-go rules.

  python scripts/analyse_pilot.py
Reads results/pilot/*.json and prereg/plan.yaml. Writes
results/pilot_summary.md, results/pilot_summary.json and
results/figures/pilot_pass_tokens.png.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from objectgraph.conditions import DESCRIPTION  # noqa: E402

COND_ORDER = ["G2", "G4", "GC", "G6", "G7"]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return float(np.mean(xs)) if xs else None


def main(results: Path = ROOT / "results", plan_path: Path = ROOT / "prereg" / "plan.yaml") -> dict:
    plan = yaml.safe_load(plan_path.read_text())
    files = sorted((results / "pilot").glob("*.json"))
    table = {}
    for f in files:
        d = json.loads(f.read_text())
        rows = d["rows"]
        proj = d["project"]
        table[proj] = {"k_star": rows[0]["k_star"] if rows else None, "conditions": {}}
        for c in COND_ORDER:
            rs = [r for r in rows if r["condition"] == c]
            if not rs:
                continue
            table[proj]["conditions"][c] = {
                "k": rs[0]["k"], "same_as": rs[0]["same_as"], "runs": len(rs),
                "pass_rate": mean([r.get("pass_rate") for r in rs]),
                "pass_rate_runs": [r.get("pass_rate") for r in rs],
                "tokens": mean([r.get("tokens") for r in rs]),
                "messages": mean([r.get("messages") for r in rs]),
                "traceability": mean([r.get("traceability") for r in rs]),
                "budget_stops": sum(bool(r.get("stopped_by_budget")) for r in rs),
            }

    # go/no-go rules (see prereg/plan.yaml)
    multi = {p: t for p, t in table.items() if (t["k_star"] or 1) > 1}
    single = {p: t for p, t in table.items() if t["k_star"] == 1}
    wins, strict, token_ok, ties_g6, uninformative = [], [], [], [], []
    for p, t in multi.items():
        c = t["conditions"]
        rates = [v["pass_rate"] for v in c.values() if v["pass_rate"] is not None]
        if rates and max(rates) == 0:
            uninformative.append(p)          # every team failed: says nothing about splitting
            continue
        if "G7" in c and "G4" in c and c["G7"]["pass_rate"] is not None and c["G4"]["pass_rate"] is not None:
            strict.append(c["G7"]["pass_rate"] > c["G4"]["pass_rate"])
            wins.append(c["G7"]["pass_rate"] >= c["G4"]["pass_rate"])
            token_ok.append(c["G7"]["tokens"] <= 1.10 * c["G4"]["tokens"])
        if "G7" in c and "G6" in c and c["G7"]["pass_rate"] is not None and c["G6"]["pass_rate"] is not None:
            ties_g6.append(abs(c["G7"]["pass_rate"] - c["G6"]["pass_rate"]) <= 0.05)
    rule1 = len(wins) >= 2 and sum(wins) > len(wins) / 2 and any(strict)
    rule2 = bool(token_ok) and all(token_ok)
    lice_ok = []
    for p, t in single.items():
        c = t["conditions"]
        others = [c[x]["pass_rate"] for x in ("GC", "G4") if x in c and c[x]["pass_rate"] is not None]
        if "G2" in c and c["G2"]["pass_rate"] is not None and others and max(others + [c["G2"]["pass_rate"]]) > 0:
            lice_ok.append(c["G2"]["pass_rate"] >= max(others))
    rule3 = bool(lice_ok) and all(lice_ok)
    complete = all(len(t["conditions"]) == len(COND_ORDER) for t in table.values()) and len(table) == len(plan["tasks"])
    verdict = "GO" if (rule1 and rule2 and rule3) else "NO-GO"
    if not complete:
        verdict += " (provisional: not all pilot tasks/conditions are in yet)"
    # Experiment 1b (k*=1 tasks): H3a cost, H3b correctness
    h3a, h3b_wins, h3b_tasks = [], 0, 0
    for p, t in single.items():
        c = t["conditions"]
        if "G2" not in c:
            continue
        split = [c[x] for x in ("G4", "GC") if x in c and c[x]["tokens"] is not None]
        if split:
            h3a.append(all(c["G2"]["tokens"] < v["tokens"] for v in split))
        rates = [v["pass_rate"] for v in c.values() if v["pass_rate"] is not None]
        if rates and max(rates) > 0:
            h3b_tasks += 1
            h3b_wins += c["G2"]["pass_rate"] >= max(c[x]["pass_rate"] for x in ("G4", "GC") if x in c)
    g6_cmp = []
    for p, t in single.items():
        c = t["conditions"]
        if "G2" in c and "G6" in c and not c["G6"].get("same_as"):
            g6_cmp.append({"project": p, "G2_pass": c["G2"]["pass_rate"], "G6_pass": c["G6"]["pass_rate"],
                           "G2_tokens": c["G2"]["tokens"], "G6_tokens": c["G6"]["tokens"], "G6_k": c["G6"]["k"]})
    exp1b = {"exploratory_G2_vs_infomap": g6_cmp, "H3a_G2_fewer_tokens_on_every_k1_task": bool(h3a) and all(h3a), "k1_tasks": len(h3a),
             "H3b_G2_at_least_as_correct_majority": h3b_tasks > 0 and h3b_wins > h3b_tasks / 2,
             "H3b_informative_tasks": h3b_tasks, "H3b_wins": int(h3b_wins)}
    decision = {"experiment_1b": exp1b, "rule_G7_beats_G4_majority": {"passed": rule1, "wins": sum(wins), "tasks": len(wins)},
                "rule_G7_tokens_within_10pct_of_G4": {"passed": rule2},
                "rule_single_agent_best_when_kstar_1": {"passed": rule3, "tasks": len(lice_ok)},
                "G7_ties_G6_on": f"{sum(ties_g6)}/{len(ties_g6)} tasks",
                "uninformative_tasks": uninformative,
                "verdict": verdict}

    # markdown
    md = ["# Experiment 1 (pilot) summary", "",
          f"Model: `{', '.join(sorted({json.loads(f.read_text()).get('model', '?') for f in files})) or plan['model']['name']}` · design: {plan['design']} · runs per condition: {plan['runs_per_condition']}", ""]
    for p, t in table.items():
        md += [f"## {p} (k* = {t['k_star']})", "",
               "| Condition | Agents | Pass rate (mean) | Runs | Tokens (mean) | Messages | Traceability | Note |",
               "|---|---|---|---|---|---|---|---|"]
        for c, v in t["conditions"].items():
            pr = "-" if v["pass_rate"] is None else f"{v['pass_rate']:.2f}"
            runs = ", ".join("-" if x is None else f"{x:.2f}" for x in v["pass_rate_runs"])
            tok = "-" if v["tokens"] is None else f"{v['tokens']:,.0f}"
            note = f"same team as {v['same_as']}" if v["same_as"] else ""
            if v["budget_stops"]:
                note += f" {v['budget_stops']} hit token cap"
            md.append(f"| {c} {DESCRIPTION[c]} | {v['k']} | {pr} | {runs} | {tok} | "
                      f"{v['messages'] if v['messages'] is not None else '-'} | "
                      f"{'-' if v['traceability'] is None else f'{100 * v['traceability']:.0f}%'} | {note} |")
        md.append("")
    md += ["## Go / no-go (pre-registered rules)", "",
           f"- G7 >= G4 on a majority of informative multi-agent tasks (at least 2, at least one strict win): **{rule1}** ({sum(wins)}/{len(wins)}; strict wins {sum(strict)})",
           f"- Tasks where every team scored 0 (excluded as uninformative): {', '.join(uninformative) or 'none'}",
           f"- G7 tokens <= 1.10 x G4 on every multi-agent task: **{rule2}**",
           f"- Single agent best where k* = 1: **{rule3}**",
           f"- G7 within 0.05 of G6: {decision['G7_ties_G6_on']}",
           "", "## Experiment 1b (k* = 1 tasks)", "",
           f"- H3a single agent uses fewer tokens than split teams on every k*=1 task: **{exp1b['H3a_G2_fewer_tokens_on_every_k1_task']}** ({exp1b['k1_tasks']} tasks)",
           f"- H3b single agent at least as correct on a majority of informative k*=1 tasks: **{exp1b['H3b_G2_at_least_as_correct_majority']}** ({exp1b['H3b_wins']}/{exp1b['H3b_informative_tasks']})",
           *[f"- Exploratory, single agent vs Infomap team (k={r['G6_k']}) on {r['project']}: tests {r['G2_pass']} vs {r['G6_pass']}, tokens {r['G2_tokens']:,.0f} vs {r['G6_tokens']:,.0f}" for r in exp1b["exploratory_G2_vs_infomap"]],
           "", f"**Verdict: {verdict}**", "",
           "_3 runs per condition show direction and cost, not statistical proof._"]
    (results / "pilot_summary.md").write_text("\n".join(md) + "\n")
    (results / "pilot_summary.json").write_text(json.dumps({"table": table, "decision": decision}, indent=2))

    # figure
    if table:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        projs = list(table)
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.2))
        width = 0.16
        colors = {"G2": "#888780", "G4": "#B4B2A9", "GC": "#7F77DD", "G6": "#378ADD", "G7": "#1D9E75"}
        for i, c in enumerate(COND_ORDER):
            x = np.arange(len(projs)) + (i - 2) * width
            for ax, key in zip(axes, ("pass_rate", "tokens")):
                vals = [table[p]["conditions"].get(c, {}).get(key) or 0 for p in projs]
                ax.bar(x, vals, width, color=colors[c], label=f"{c} {DESCRIPTION[c]}")
        for ax, lab in zip(axes, ("tests passed (share)", "tokens per run")):
            ax.set_xticks(np.arange(len(projs)), [p.split("/")[1] for p in projs], fontsize=8)
            ax.set_ylabel(lab)
        axes[0].set_ylim(0, 1)
        axes[0].legend(fontsize=7, frameon=False, ncol=1, loc="upper left", bbox_to_anchor=(1.0, 1.0))
        axes[1].legend().remove() if axes[1].get_legend() else None
        fig.tight_layout()
        (results / "figures").mkdir(parents=True, exist_ok=True)
        fig.savefig(results / "figures" / "pilot_pass_tokens.png", dpi=180)
    print("\n".join(md))
    return decision


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "results"), help="e.g. results/second_model")
    main(Path(ap.parse_args().results))
