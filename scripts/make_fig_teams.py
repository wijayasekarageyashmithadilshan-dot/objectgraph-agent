"""Fig. 5: criterion team (G7) vs random team (G4) on stocktrends, pilot run 0.

(a)(b) cohesion (diagonal) and coupling (off-diagonal) between agents, as in MQ;
(c) tokens per agent in the logged run. Reads DevBench's design and runs/pilot/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from objectgraph.pipeline import load_project            # noqa: E402
from objectgraph.uml import parse_class_diagram           # noqa: E402
from objectgraph.graph import build_duty_graph            # noqa: E402
from objectgraph.conditions import build_conditions       # noqa: E402
from objectgraph.team import build_team                   # noqa: E402


def cc(graph, labels):
    groups = sorted(set(labels.tolist()), key=lambda g: int(np.flatnonzero(labels == g)[0]))
    k = len(groups)
    M = np.zeros((k, k))
    for a, ga in enumerate(groups):
        ia = labels == ga
        for b, gb in enumerate(groups):
            ib = labels == gb
            M[a, b] = graph.W[np.ix_(ia, ib)].sum() / (ia.sum() * ib.sum())
    return M


def main(project="python/stocktrends"):
    proj = load_project(ROOT / "DevBench", project)
    diagram = parse_class_diagram(proj["gold_text"])
    g = build_duty_graph(diagram)
    conds = build_conditions(g)
    fig = plt.figure(figsize=(3.5, 4.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.95])
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])]
    vmax = 0
    mats = {}
    for c in ("G7", "G4"):
        mats[c] = cc(g, conds[c]["labels"])
        vmax = max(vmax, mats[c].max())
    for ax, c, title in ((axes[0], "G7", "(a) Criterion team (G7)"), (axes[1], "G4", "(b) Random team (G4)")):
        team = build_team(c, conds[c]["labels"], g, diagram)
        M = mats[c]
        ax.imshow(M, cmap="Greens", vmin=0, vmax=vmax)
        names = [a.agent_id.replace("agent_", "A") for a in team.agents]
        k = len(names)
        ax.set_xticks(range(k), names, fontsize=7)
        ax.set_yticks(range(k), names, fontsize=7)
        for i in range(k):
            for j in range(k):
                ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if M[i, j] > 0.6 * vmax else "black")
        cls = ["+".join(sorted(set(x.classes))) for x in team.agents]
        ax.set_title(title, fontsize=8)
        ax.set_xlabel("\n".join(f"{n}: {c_}" for n, c_ in zip(names, cls)), fontsize=5.5)
    ax = axes[2]
    width = 0.38
    for i, c in enumerate(("G7", "G4")):
        run = json.loads((ROOT / "runs/pilot" / project.replace("/", "__") / c / "run0" / "run.json").read_text())
        bt = run["usage"]["by_tag"]
        tags = sorted(bt, key=lambda t: int(t.split("_")[1]))
        x = np.arange(len(tags)) + (i - 0.5) * width
        inp = [bt[t]["input_tokens"] for t in tags]
        out = [bt[t]["output_tokens"] for t in tags]
        col = "#1D9E75" if c == "G7" else "#B4B2A9"
        ax.bar(x, inp, width, color=col, alpha=0.55, label=f"{c} input")
        ax.bar(x, out, width, bottom=inp, color=col, label=f"{c} output")
    ax.set_xticks(np.arange(3), ["A1", "A2", "A3"], fontsize=7)
    ax.set_ylabel("tokens (run 0)", fontsize=7)
    ax.tick_params(labelsize=6.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylim(0, max(ax.get_ylim()[1], 1) * 1.35)
    ax.legend(fontsize=5.5, frameon=False, ncol=2, loc="upper right")
    ax.set_title("(c) Tokens per agent", fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "paper/figures/teams.pdf")
    fig.savefig(ROOT / "paper/figures_docx/fig_teams.png", dpi=240)
    print("ok", {c: np.round(m, 2).tolist() for c, m in mats.items()})


if __name__ == "__main__":
    main()
