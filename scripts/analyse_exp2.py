"""Analyse Experiment 2 (RealBench) exactly as registered in prereg/plan.yaml.

  python scripts/analyse_exp2.py [--results results/experiment_2]

H1 primary  : per-task mean pass rate G7 > G4, one-sided Wilcoxon signed-rank over
              usable tasks (zero differences dropped), alpha 0.05.
H1 secondary: G7 vs GC and G7 vs G6, two-sided Wilcoxon, Holm-corrected.
H2 cost     : median over tasks of mean tokens(G7) / mean tokens(G4) <= 1.10.
Floor rule  : fewer than 4 usable tasks with any condition above 0 -> H1 untestable.
Writes results/experiment_2/summary.json and summary.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

CONDS = ["G2", "G4", "GC", "G6", "G7"]


def holm(ps: dict[str, float]) -> dict[str, float]:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def test(a: list[float], b: list[float], alternative: str) -> dict:
    d = np.array(a) - np.array(b)
    nz = d[d != 0]
    res = {"n_tasks": len(d), "n_nonzero": int(len(nz)), "wins": int((d > 0).sum()),
           "losses": int((d < 0).sum()), "ties": int((d == 0).sum()),
           "mean_diff": round(float(d.mean()), 4) if len(d) else None}
    if len(nz) == 0:
        res["p"] = 1.0
        return res
    res["p"] = round(float(wilcoxon(nz, alternative=alternative, zero_method="wilcox").pvalue), 6)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/experiment_2")
    ap.add_argument("--conditions", nargs="*", default=CONDS)
    a = ap.parse_args()
    res = Path(a.results)
    conds = a.conditions
    ref = json.loads((res / "reference.json").read_text())
    tasks, rows_md = {}, []
    for f in sorted(res.glob("level*.json")):
        d = json.loads(f.read_text())
        t = d["task"]
        if not ref.get(t, {}).get("usable"):
            continue
        per = {}
        for c in conds:
            rs = [r for r in d["rows"] if r["condition"] == c]
            if rs:
                per[c] = {"pass": float(np.mean([r["pass_rate"] for r in rs])),
                          "runs": [r["pass_rate"] for r in rs],
                          "tokens": float(np.mean([r.get("tokens") or 0 for r in rs])),
                          "k": rs[0]["k"], "same_as": rs[0].get("same_as"),
                          "stopped": sum(bool(r.get("stopped_by_budget")) for r in rs)}
        if all(c in per for c in conds):
            tasks[t] = per
    usable = sorted(tasks)
    above0 = [t for t in usable if any(tasks[t][c]["pass"] > 0 for c in conds)]
    out = {"usable_tasks": usable, "tasks_above_floor": above0,
           "unusable": {t: r.get("reason", "") for t, r in ref.items() if not r.get("usable")}}
    col = lambda c: [tasks[t][c]["pass"] for t in usable]
    if len(above0) < 4:
        out["H1_primary"] = {"verdict": "untestable at this model strength (floor rule)", "tasks_above_floor": len(above0)}
    else:
        h1 = test(col("G7"), col("G4"), "greater")
        h1["verdict"] = "supported" if h1["p"] < 0.05 else "not supported"
        out["H1_primary"] = h1
    sec = {f"G7_vs_{c}": test(col("G7"), col(c), "two-sided") for c in conds if c not in ("G7", "G4")}
    adj = holm({k: v["p"] for k, v in sec.items()})
    for k in sec:
        sec[k]["p_holm"] = round(adj[k], 6)
    out["H1_secondary"] = sec
    ratios = [tasks[t]["G7"]["tokens"] / tasks[t]["G4"]["tokens"] for t in usable if tasks[t]["G4"]["tokens"] > 0]
    med = float(np.median(ratios)) if ratios else None
    out["H2_cost"] = {"median_ratio_G7_over_G4": round(med, 4) if med else None,
                      "verdict": None if med is None else ("supported" if med <= 1.10 else "not supported")}
    out["per_task"] = tasks
    (res / "summary.json").write_text(json.dumps(out, indent=2))

    md = ["# Experiment 2 (RealBench) summary", "",
          f"Usable tasks: {len(usable)}; tasks with any condition above 0: {len(above0)}.", "",
          "| Task | " + " | ".join(f"{c} pass (k)" for c in conds) + " |", "|---" * (len(conds) + 1) + "|"]
    for t in usable:
        md.append(f"| {t.split('/', 1)[1]} | " + " | ".join(
            f"{tasks[t][c]['pass']:.2f} ({tasks[t][c]['k']})" for c in conds) + " |")
    md += ["", f"H1 primary (G7 > G4): {out['H1_primary']}", "",
           *[f"{k}: {v}" for k, v in sec.items()], "", f"H2 cost: {out['H2_cost']}"]
    if out["unusable"]:
        md += ["", "Unusable tasks: " + "; ".join(f"{t} ({r[:80]})" for t, r in out["unusable"].items())]
    (res / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
