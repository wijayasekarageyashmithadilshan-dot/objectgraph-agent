"""Text, table rows and figure for Experiment 2 (RealBench) in the IEEE Access draft.

  python scripts/make_exp2_assets.py
Reads results/experiment_2/summary.json and results/realbench_table.csv.
Writes paper/generated/exp2.json and paper/figures_docx/fig_exp2.png.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
import pandas as pd               # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONDS = ["G2", "G4", "GC", "G6", "G7"]
SHORT = {"draeician_crules": "crules", "salvozappa_gattino": "gattino", "FreddyRodgers_emojichef": "emojichef",
         "aliyun_alibabacloud-dms-mcp-server": "alibaba-dms-mcp", "antoine311200_torchcolor": "torchcolor",
         "pab1it0_adx-mcp-server": "adx-mcp", "rileydakota_crx-analyzer": "crx-analyzer", "Camera": "Camera",
         "Reconnaissance": "Reconnaissance"}


def main() -> None:
    S = json.loads((ROOT / "results/experiment_2/summary.json").read_text())
    tab = pd.read_csv(ROOT / "results/realbench_table.csv")
    T = S["per_task"]
    tasks = sorted(T, key=lambda t: (t.split("/")[0], SHORT[t.split("/", 1)[1]].lower()))
    mean = {c: float(np.mean([T[t][c]["pass"] for t in tasks])) for c in CONDS}
    tok = {c: float(np.median([T[t][c]["tokens"] for t in tasks])) for c in CONDS}
    r74 = [T[t]["G7"]["tokens"] / T[t]["G4"]["tokens"] for t in tasks]
    r7c = [T[t]["G7"]["tokens"] / T[t]["GC"]["tokens"] for t in tasks]
    r72 = [T[t]["G7"]["tokens"] / T[t]["G2"]["tokens"] for t in tasks]
    gc_zero = sum(T[t]["GC"]["pass"] == 0 for t in tasks)
    above = len(S["tasks_above_floor"])
    h1, sec = S["H1_primary"], S["H1_secondary"]
    n61 = len(tab)
    split = int((tab.k_star > 1).sum())
    lv = tab.groupby("level").k_star.mean().round(1).to_dict()
    lvu = tab.groupby("level").units.mean().round(1).to_dict()
    differ = int((tab.ari_vs_one_per_unit < 0.999).sum())
    crx = T["level2/rileydakota_crx-analyzer"]
    emo = T["level2/FreddyRodgers_emojichef"]

    rows = []
    for t in tasks:
        p = T[t]
        rows.append([SHORT[t.split("/", 1)[1]], t.split("/")[0].replace("level", "L"),
                     *[f'{p[c]["pass"]:.2f} ({p[c]["k"]})' for c in CONDS],
                     f'{p["G7"]["tokens"] / 1000:.0f}k / {p["G4"]["tokens"] / 1000:.0f}k'])
    rows.append(["Mean", "", *[f"{mean[c]:.2f}" for c in CONDS],
                 f'{np.median([T[t]["G7"]["tokens"] for t in tasks]) / 1000:.0f}k / {tok["G4"] / 1000:.0f}k'])

    out = {
        "contribution": f"5) A second pre-registered experiment on RealBench {{cite:li2026realbench}}: a zero-call structural study of all {n61} projects, and five team designs compared on {len(tasks)} real Python projects with their own tests, after a harness check in which every team design reproduces the reference score (Section VII).",
        "abstract": f"A second pre-registered experiment on {len(tasks)} RealBench projects found no significant quality difference between the criterion’s teams and random teams of the same sizes (p = {h1['p']:.2f}), but the criterion’s teams had the highest mean pass rate ({mean['G7']:.2f} versus {mean['G4']:.2f}), used {100 * (1 - float(np.median(r74))):.0f}% fewer tokens than random teams, and avoided the collapse of one agent per class, which passed no test on {gc_zero} of {len(tasks)} projects.",
        "structural": f"RealBench {{cite:li2026realbench}} provides {n61} Python repositories in four difficulty levels, each with natural-language descriptions, a class diagram generated from the code, a file tree and executable tests. Its diagrams name files without folders and contain no inheritance or composition, so the duty graph reads file paths from the file tree, gives every file an owner (classes, and one unit per file for module-level functions or constants), and uses dependency, import and signature edges. With no model call, the criterion recommends a team for {split} of the {n61} projects, and the recommended size grows with difficulty: on average {lv.get('level1', 0)}, {lv.get('level2', 0)}, {lv.get('level3', 0)} and {lv.get('level4', 0)} agents for levels 1 to 4 (designs of {lvu.get('level1', 0)}, {lvu.get('level2', 0)}, {lvu.get('level3', 0)} and {lvu.get('level4', 0)} units). Its team differs from one agent per unit in {differ} projects.",
        "protocol": f"The tasks were chosen by a rule fixed before any model call: a criterion team of 2 to 6 agents that differs from both one agent per class and Infomap, so that the comparison is informative. Seventeen projects qualify; {len(S['unusable'])} are unusable because RealBench ships no tests for them or their reference code fails its own tests in the sandbox, which leaves {len(tasks)}. Agents receive the README (when RealBench ships one), the class diagram with its descriptions and the file tree, but never code or tests. Before any model call, the reference code was split according to every team, merged and scored; every team design reproduced the reference score on every task, which rules out losses caused by splitting or merging. This check found and fixed three faults in reading the designs and several in merging; one further merging fault (parenthesized multi-line imports) appeared in the first paid runs and was fixed, and those runs re-merged, before the full run. All fixes are logged. The model is DeepSeek V4.1 Flash (deepseek-v4.1-flash-1017, reasoning off, temperature 0) with three runs per condition and the same token cap as the pilot. The primary hypothesis is that G7 passes more tests than G4 (one-sided Wilcoxon signed-rank test over tasks); G7 against GC and G6 are secondary (Holm-corrected); and the token ratio of G7 to G4 is expected to be at most 1.10. When the first provider’s credit ran out after 9 runs, the experiment was moved to a second provider serving the same dated model and rerun in full, as recorded in an amendment.",
        "results": f"{['Zero','One','Two','Three','Four','Five','Six','Seven','Eight','Nine'][above]} of the {len(tasks)} tasks have a condition above zero, so the primary hypothesis is testable. It is not supported: G7 wins on {h1['wins']} tasks, loses on {h1['losses']} and ties on {h1['ties']} (p = {h1["p"]:.2f}; Table V). The secondary comparisons point the same way but are not significant either (G7 against GC: {sec['G7_vs_GC']['wins']} wins, {sec['G7_vs_GC']['losses']} loss, Holm-adjusted p = {sec['G7_vs_GC']['p_holm']:.2f}; against G6: {sec['G7_vs_G6']['wins']} wins, {sec['G7_vs_G6']['losses']} loss, p = {sec['G7_vs_G6']['p_holm']:.2f}). The criterion’s teams nonetheless have the highest mean pass rate ({mean['G7']:.2f}, against {mean['G4']:.2f} for random teams, {mean['G2']:.2f} for a single agent, {mean['G6']:.2f} for Infomap and {mean['GC']:.2f} for one agent per class), with their clearest gain on emojichef ({emo['G7']['pass']:.2f} against {emo['G4']['pass']:.2f} for random teams and {emo['G2']['pass']:.2f} for a single agent). The cost expectation holds: G7 uses a median {100 * (1 - float(np.median(r74))):.0f}% fewer tokens than G4 and {100 * (1 - float(np.median(r7c))):.0f}% fewer than GC, but {float(np.median(r72)):.1f} times as many as a single agent. One agent per class collapses: it passes no test on {gc_zero} of the {len(tasks)} tasks; on crx-analyzer its {crx['GC']['k']} agents spend about {crx['GC']['tokens'] / 1000:.0f}k tokens per run and pass nothing, whereas the criterion’s {crx['G7']['k']} agents pass {crx['G7']['pass']:.2f} of the tests with {crx['G7']['tokens'] / 1000:.0f}k.",
        "discussion": f"Two results are robust across both experiments. First, the criterion avoids the failure of large teams: splitting by class creates many small agents that each see one class, and the resulting interface mismatches (for example, two agents importing each other’s modules) break whole projects. Second, at equal team sizes, grouping duties by the design costs fewer tokens than grouping them at random. Whether that grouping also improves correctness remains open: with {h1['n_nonzero']} non-tied tasks, even {h1['n_nonzero']} wins of {h1['n_nonzero']} would give p = {1 / 2 ** h1['n_nonzero']:.4f}, so this experiment could not reach significance, and {len(tasks) - above} tasks sat at zero for every condition with this model. A stronger model, which lifts more tasks off the floor, and more tasks are the direct next steps; both will be registered before they run.",
        "threat": f"RealBench’s diagrams are generated from the code by a static-analysis tool, and its tests may call helpers that the diagram does not list. Only {len(tasks)} of 17 selected RealBench tasks are usable, and runs at temperature 0 are often identical, which limits the effective sample size.",
        "conclusion": f"On {len(tasks)} RealBench projects, the criterion’s teams did not significantly beat random teams of the same sizes, but they had the highest mean pass rate, used {100 * (1 - float(np.median(r74))):.0f}% fewer tokens than random teams and far fewer than one agent per class, which failed on {gc_zero} of {len(tasks)} projects. The criterion’s demonstrated value is therefore efficient, robust team sizing; whether it also improves correctness needs a stronger model and more tasks.",
        "table_rows": rows,
        "fig_caption": "Experiment 2 on RealBench: mean pass rate over three runs per task and condition (top) and median tokens per run (bottom). Cells show the share of the reference code’s passing tests that each condition passes.",
    }
    (ROOT / "paper/generated/exp2.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))

    fig, ax = plt.subplots(2, 1, figsize=(3.45, 4.2), gridspec_kw={"height_ratios": [2.2, 1]})
    M = np.array([[T[t][c]["pass"] for c in CONDS] for t in tasks])
    im = ax[0].imshow(M, cmap="Blues", vmin=0, vmax=0.8, aspect="auto")
    ax[0].set_xticks(range(len(CONDS)), CONDS, fontsize=7)
    ax[0].set_yticks(range(len(tasks)), [SHORT[t.split("/", 1)[1]] for t in tasks], fontsize=7)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax[0].text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6,
                       color="white" if M[i, j] > 0.45 else "#222222")
    ax[0].set_title("Pass rate (share of reference tests)", fontsize=8)
    ax[0].tick_params(length=0)
    vals = [tok[c] / 1000 for c in CONDS]
    bars = ax[1].bar(CONDS, vals, color=["#9aa5b1", "#9aa5b1", "#9aa5b1", "#9aa5b1", "#2a78d6"], width=0.6)
    for b, v in zip(bars, vals):
        ax[1].text(b.get_x() + b.get_width() / 2, v + 0.6, f"{v:.0f}k", ha="center", fontsize=6.5)
    ax[1].set_ylabel("Median tokens\nper run (k)", fontsize=7)
    ax[1].tick_params(labelsize=7)
    ax[1].spines[["top", "right"]].set_visible(False)
    ax[1].set_ylim(0, max(vals) * 1.25)
    fig.tight_layout()
    fig.savefig(ROOT / "paper/figures_docx/fig_exp2.png", dpi=220)
    print(json.dumps({k: v for k, v in out.items() if k not in ("table_rows",)}, indent=1)[:3000])


if __name__ == "__main__":
    main()
