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


def r2b_saving() -> int:
    S = json.loads((ROOT / "results/experiment_2b/summary.json").read_text())
    T = S["per_task"]
    return round(100 * (1 - float(np.median([T[t]["G7"]["tokens"] / T[t]["G4"]["tokens"] for t in T]))))


def exp2b_text() -> str:
    f = ROOT / "results/experiment_2b/summary.json"
    if not f.exists():
        return ""
    S = json.loads(f.read_text())
    T = S["per_task"]
    m = {c: float(np.mean([T[t][c]["pass"] for t in T])) for c in CONDS}
    r74 = float(np.median([T[t]["G7"]["tokens"] / T[t]["G4"]["tokens"] for t in T]))
    r72 = float(np.median([T[t]["G7"]["tokens"] / T[t]["G2"]["tokens"] for t in T]))
    h1 = S["H1_primary"]
    return (f"{{bi:Second model family (Experiment 2b, pre-registered):}} A stronger open-weight model, NVIDIA Nemotron 3 Ultra "
            f"(550B parameters, temperature 0, one run per condition), was run on the same tasks; one task (Camera) was excluded "
            f"because its reference tests did not run in the second sandbox, leaving {len(T)}. Two reply-format faults of this model "
            f"(a code fence joined to the next file header, and a root folder copied into paths) were fixed in the parser and all runs "
            f"were rebuilt from the saved replies without new model calls; seven runs changed and are listed in the repository. "
            f"{['No', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight'][len(S['tasks_above_floor'])]} tasks have a condition above zero. The criterion's teams again used fewer tokens than random "
            f"teams of the same sizes (median ratio {r74:.2f}, {100 * (1 - r74):.0f}% fewer), but they did not pass more tests "
            f"({h1['wins']} wins, {h1['losses']} losses, {h1['ties']} ties; mean pass rate {m['G7']:.2f} against {m['G4']:.2f}). "
            f"Many failures with this model are replies cut off at the 8,000-token output cap, which is why a larger cap is registered "
            f"for the next experiment. Across both model families, the token saving replicates and a correctness advantage does not.")


def exploratory(T: dict, tasks: list) -> str:
    import collections
    rows = [r for f in sorted((ROOT / "results/experiment_2").glob("level*.json"))
            for r in json.loads(f.read_text())["rows"]]
    B = collections.defaultdict(list)
    for r in rows:
        k = r["k"]
        B["1" if k == 1 else "2–3" if k <= 3 else "4–6" if k <= 6 else "7+"].append(r["pass_rate"] == 0)
    z = {g: (sum(v), len(v)) for g, v in B.items()}
    return (f"{{bi:Exploratory (not pre-registered):}} About half of the runs with up to 6 agents pass no test "
            f"({z['1'][0]} of {z['1'][1]} single-agent runs, {z['2–3'][0]} of {z['2–3'][1]} runs with 2–3 agents and "
            f"{z['4–6'][0]} of {z['4–6'][1]} with 4–6 agents), but all {z['7+'][1]} runs with 7 or more agents pass no test. "
            "Large teams arise only on larger designs, so team size and project difficulty are confounded here; "
            "within a project, the contrast on crx-analyzer (22 agents pass nothing, the criterion’s 3 agents pass 0.48) points the same way.")


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
        "abstract": f"In pre-registered experiments on RealBench with two model families, the criterion’s teams used {100 * (1 - float(np.median(r74))):.0f}% and {r2b_saving()}% fewer tokens than random teams of the same sizes, with no significant difference in tests passed (p = {h1['p']:.2f} with the first model), and avoided the collapse of one agent per class, which passed no test on {gc_zero} of {len(tasks)} projects with the first model.",
        "structural": f"RealBench {{cite:li2026realbench}} provides {n61} Python repositories in four difficulty levels, each with natural-language descriptions, a class diagram generated from the code, a file tree and executable tests. Its diagrams name files without folders and contain no inheritance or composition, so the duty graph reads file paths from the file tree, gives every file an owner (classes, and one unit per file for module-level functions or constants), and uses dependency, import and signature edges. With no model call, the criterion recommends a team for {split} of the {n61} projects, and the recommended size grows with difficulty: on average {lv.get('level1', 0)}, {lv.get('level2', 0)}, {lv.get('level3', 0)} and {lv.get('level4', 0)} agents for levels 1 to 4 (designs of {lvu.get('level1', 0)}, {lvu.get('level2', 0)}, {lvu.get('level3', 0)} and {lvu.get('level4', 0)} units). Its team differs from one agent per unit in {differ} projects.",
        "protocol": f"The tasks were chosen by a rule fixed before any model call: a criterion team of 2 to 6 agents that differs from both one agent per class and Infomap, so that the comparison is informative. Seventeen projects qualify; {len(S['unusable'])} are unusable because RealBench ships no tests for them or their reference code fails its own tests in the sandbox, which leaves {len(tasks)}. Agents receive the README (when RealBench ships one), the class diagram with its descriptions and the file tree, but never code or tests. Before any model call, the reference code was split according to every team, merged and scored; every team design reproduced the reference score on every task, which rules out losses caused by splitting or merging. This check found and fixed three faults in reading the designs and several in merging; one further merging fault (parenthesized multi-line imports) appeared in the first paid runs and was fixed, and those runs re-merged, before the full run. All fixes are logged. The model is DeepSeek V4.1 Flash (deepseek-v4.1-flash-1017, reasoning off, temperature 0) with three runs per condition and the same token cap as the pilot. The primary hypothesis is that G7 passes more tests than G4 (one-sided Wilcoxon signed-rank test over tasks); G7 against GC and G6 are secondary (Holm-corrected); and the token ratio of G7 to G4 is expected to be at most 1.10. When the first provider’s credit ran out after 9 runs, the experiment was moved to a second provider serving the same dated model and rerun in full, as recorded in an amendment.",
        "results": f"{['Zero','One','Two','Three','Four','Five','Six','Seven','Eight','Nine'][above]} of the {len(tasks)} tasks have a condition above zero, so the primary hypothesis is testable. It is not supported: G7 wins on {h1['wins']} tasks, loses on {h1['losses']} and ties on {h1['ties']} (p = {h1["p"]:.2f}; Table V). The secondary comparisons point the same way but are not significant either (G7 against GC: {sec['G7_vs_GC']['wins']} wins, {sec['G7_vs_GC']['losses']} loss, Holm-adjusted p = {sec['G7_vs_GC']['p_holm']:.2f}; against G6: {sec['G7_vs_G6']['wins']} wins, {sec['G7_vs_G6']['losses']} loss, p = {sec['G7_vs_G6']['p_holm']:.2f}). The criterion’s teams nonetheless have the highest mean pass rate ({mean['G7']:.2f}, against {mean['G4']:.2f} for random teams, {mean['G2']:.2f} for a single agent, {mean['G6']:.2f} for Infomap and {mean['GC']:.2f} for one agent per class), with their clearest gain on emojichef ({emo['G7']['pass']:.2f} against {emo['G4']['pass']:.2f} for random teams and {emo['G2']['pass']:.2f} for a single agent). The cost expectation holds: G7 uses a median {100 * (1 - float(np.median(r74))):.0f}% fewer tokens than G4 and {100 * (1 - float(np.median(r7c))):.0f}% fewer than GC, but {float(np.median(r72)):.1f} times as many as a single agent. One agent per class collapses: it passes no test on {gc_zero} of the {len(tasks)} tasks; on crx-analyzer its {crx['GC']['k']} agents spend about {crx['GC']['tokens'] / 1000:.0f}k tokens per run and pass nothing, whereas the criterion’s {crx['G7']['k']} agents pass {crx['G7']['pass']:.2f} of the tests with {crx['G7']['tokens'] / 1000:.0f}k.",
        "discussion": f"Two results are robust across both experiments. First, the criterion avoids the failure of large teams: splitting by class creates many small agents that each see one class, and the resulting interface mismatches (for example, two agents importing each other’s modules) break whole projects. Second, at equal team sizes, grouping duties by the design costs fewer tokens than grouping them at random. Whether that grouping also improves correctness remains open: with {h1['n_nonzero']} non-tied tasks, even {h1['n_nonzero']} wins of {h1['n_nonzero']} would give p = {1 / 2 ** h1['n_nonzero']:.4f}, so this experiment could not reach significance, and {len(tasks) - above} tasks sat at zero for every condition with this model. A stronger model, which lifts more tasks off the floor, and more tasks are the direct next steps; both will be registered before they run.",
        "threat": f"RealBench’s diagrams are generated from the code by a static-analysis tool, and its tests may call helpers that the diagram does not list. Only {len(tasks)} of 17 selected RealBench tasks are usable, and runs at temperature 0 are often identical, which limits the effective sample size.",
        "conclusion": f"On {len(tasks)} RealBench projects, the criterion’s teams did not significantly beat random teams of the same sizes, but they had the highest mean pass rate, used {100 * (1 - float(np.median(r74))):.0f}% fewer tokens than random teams and far fewer than one agent per class, which failed on {gc_zero} of {len(tasks)} projects. The criterion’s demonstrated value is therefore efficient, robust team sizing; whether it also improves correctness needs a stronger model and more tasks.",
        "exploratory": exploratory(T, tasks),
        "exp2b": exp2b_text(),
        "exp2b_short": f"With a second model family (Nemotron 3 Ultra, Experiment 2b, {len(json.loads((ROOT / 'results/experiment_2b/summary.json').read_text())['per_task'])} tasks), the token saving replicated ({r2b_saving()}% fewer tokens than random teams of the same sizes), but the criterion’s teams did not pass more tests ({json.loads((ROOT / 'results/experiment_2b/summary.json').read_text())['H1_primary']['wins']} wins, {json.loads((ROOT / 'results/experiment_2b/summary.json').read_text())['H1_primary']['losses']} losses); details are in Appendix C.",
        "conclusion_all": json.loads((ROOT / "paper/generated/agent.json").read_text())["conclusion"].split(" The main study will")[0]
            + f" In pre-registered experiments on RealBench with two model families, the criterion’s teams used {100 * (1 - float(np.median(r74))):.0f}% and {r2b_saving()}% fewer tokens than random teams of the same sizes, with no significant difference in tests passed, and with the first model they avoided the collapse of one agent per class, which failed on {gc_zero} of {len(tasks)} projects. The criterion’s demonstrated value is therefore cost-efficient, robust team sizing; whether it also improves correctness is being tested with a larger output cap and against a team sized by an LLM Architect.",
        "h2_note": "Hypothesis H2 (cross-agent dependency predicts messages) cannot be tested with this orchestrator: it hands code to an agent along the design’s dependency edges by construction, so the logged message count follows the cut and a correlation would be circular. Testing H2 needs agents that choose whom to contact, which is left to future work.",
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
    fig.savefig(ROOT / "paper/figures/exp2.pdf")          # vector version for the ICML draft
    print(json.dumps({k: v for k, v in out.items() if k not in ("table_rows",)}, indent=1)[:3000])


if __name__ == "__main__":
    main()


def latex() -> None:
    """LaTeX versions for the ICML draft: paper/generated/exp2_macros.tex, exp2_table.tex, figures/exp2.pdf."""
    import re
    E = json.loads((ROOT / "paper/generated/exp2.json").read_text())

    def tex(t: str) -> str:
        t = t.replace("%", r"\%").replace("&", r"\&").replace("’", "'").replace("“", "``").replace("”", "''")
        t = t.replace("_", r"\_")
        t = re.sub(r"\{bi:(.*?)\}", r"\\textbf{\1}", t)
        t = re.sub(r"\{cite:([\w,]+)\}", lambda m: r"\citep{" + m.group(1).replace(r"\_", "_") + "}", t)
        t = re.sub(r"(\d)k\b", r"\1k", t)
        t = t.replace("Table V", r"Table~\ref{tab:exp2}").replace("(Section VII)", r"(Section~\ref{sec:exp2})")
        t = t.replace("Sections VI and VII", r"Sections~\ref{sec:agents} and~\ref{sec:exp2}")
        return t
    names = {"contribution": "ExpTwoContribution", "abstract": "ExpTwoAbstract", "structural": "ExpTwoStructural",
             "protocol": "ExpTwoProtocol", "results": "ExpTwoResults", "discussion": "ExpTwoDiscussion",
             "threat": "ExpTwoThreat", "exploratory": "ExpTwoExploratory", "exp2b": "ExpTwoB", "exp2b_short": "ExpTwoBShort", "conclusion_all": "ConclusionAll", "h2_note": "ExpTwoHTwoNote", "conclusion": "ExpTwoConclusion", "fig_caption": "ExpTwoFigCaption"}
    lines = ["% generated by scripts/make_exp2_assets.py"]
    for k, n in names.items():
        v = E[k][3:] if k == "contribution" else E[k]          # drop the "5) " numbering
        lines.append(r"\newcommand{\%s}{%s}" % (n, tex(v)))
    (ROOT / "paper/generated/exp2_macros.tex").write_text("\n".join(lines) + "\n")
    rows = [" & ".join(tex(c) for c in r) + r" \\" for r in E["table_rows"]]
    rows.insert(len(rows) - 1, r"\midrule")
    (ROOT / "paper/generated/exp2_table.tex").write_text(
        "\\begin{tabular}{@{}llrrrrrr@{}}\n\\toprule\nTask & Lvl & G2 & G4 & GC & G6 & G7 & Tokens G7/G4 \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")



if __name__ == "__main__":
    latex()


def icml_split() -> None:
    """ICML page limit: move the pilot's detailed table and figures to the appendix (text unchanged)."""
    import re
    src = (ROOT / "paper/generated/agent_results.tex").read_text()
    floats = []

    def take(m):
        block = m.group(0)
        if any(lbl in block for lbl in (r"\label{tab:probe}", r"\label{tab:pilot}", r"\label{fig:teams}")):
            # the appendix is one column: every float goes exactly where it is written ([H]), at a readable size
            block = block.replace("\\begin{table*}[t]", "\\begin{table}[H]").replace("\\end{table*}", "\\end{table}")
            block = block.replace("[t]", "[H]").replace("[h]", "[H]")
            block = block.replace("width=\\linewidth", "width=0.5\\linewidth")
            if r"\label{tab:pilot}" in block:       # 8 columns: scale to the text width
                block = re.sub(r"(\\begin\{tabular\}.*?\\end\{tabular\})", lambda m: "\\resizebox{\\textwidth}{!}{" + m.group(1) + "}", block, flags=re.S)
            floats.append(block)
            return ""
        return block
    body = re.sub(r"\\begin\{(table\*?|figure\*?)\}.*?\\end\{\1\}", take, src, flags=re.S)
    (ROOT / "paper/generated/agent_results_icml_body.tex").write_text(body)
    order = [r"\label{tab:pilot}", r"\label{tab:probe}", r"\label{fig:teams}"]   # largest first: no gap before it
    floats.sort(key=lambda b: next((i for i, l in enumerate(order) if l in b), 9))
    (ROOT / "paper/generated/agent_results_icml_floats.tex").write_text("\n\n".join(floats) + "\n")


if __name__ == "__main__":
    icml_split()
