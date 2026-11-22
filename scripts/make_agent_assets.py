"""Agent-study text, tables and figures for both paper versions.

Reads only result files (nothing is typed by hand):
  results/harness_check.json   zero-model-call check of split -> merge -> score
  results/probe.jsonl          single-agent model probe (model selection)
  results/pilot_summary.json   written by scripts/analyse_pilot.py (optional)
  results/reference_tests.json reference test totals
  prereg/plan.yaml             model, settings
Writes:
  paper/generated/agent.json         used by scripts/make_ieee_docx.py
  paper/generated/agent_results.tex  used by paper/content/body.tex
  paper/generated/agent_macros.tex   LaTeX macros (model id, slots)
  paper/figures/pilot.pdf, paper/figures_docx/fig_pilot.png (if the pilot exists)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "paper" / "generated"
COND = ["G2", "G4", "GC", "G6", "G7"]
NAME = {"G2": "Single agent", "G4": "Random team", "GC": "One agent per class",
        "G6": "Infomap team", "G7": "Criterion team"}


def ref_totals() -> dict:
    out = {}
    for r in json.loads((ROOT / "results" / "reference_tests.json").read_text()):
        if "status" in r:
            continue
        out[r["project"]] = sum(r[k]["passed"] + r[k]["failed"] + r[k]["errors"]
                                for k in ("unit_test", "acceptance_test") if k in r)
    return out


def to_latex(s: str) -> str:
    s = s.replace("%", r"\%").replace("&", r"\&").replace("≈", r"$\approx$").replace("≥", r"$\ge$")
    s = s.replace("k* =", r"$k^\ast$ =").replace("×", r"$\times$").replace("–", "--").replace("—", "---").replace("’", "'")
    s = re.sub(r"\{bi:([^{}]*)\}", r"\\textbf{\\emph{\1}}", s)
    s = re.sub(r"\{b:([^{}]*)\}", r"\\textbf{\1}", s)
    s = re.sub(r"\{i:([^{}]*)\}", r"\\emph{\1}", s)
    s = re.sub(r"\{cite:([^{}]*)\}", r"\\citep{\1}", s)
    s = re.sub(r"\{P:([^{}]*)\}", r"\\pending{\1}", s)
    s = re.sub(r"\{c:([^{}]*)\}", r"\\texttt{\1}", s)
    return s


def to_docx(s: str) -> str:
    return re.sub(r"\{c:([^{}]*)\}", r"\1", s)


def main() -> None:
    plan = yaml.safe_load((ROOT / "prereg" / "plan.yaml").read_text())
    model = plan["model"]["name"]
    totals = ref_totals()
    A: dict = {}

    # ---------------------------------------------------------------- settings
    A["model_sentence"] = (f"{{c:{model}}} (Qwen3-Coder-30B-A3B-Instruct, an open-weight coding model with a fixed "
                           f"release, accessed through the Vercel AI Gateway)")
    A["hardware"] = ("Agent runs for Python projects were executed on Google Colab (Python 3.13); every scoring run "
                     "builds a fresh virtual environment. C++ and Java projects are scored in DevBench’s container "
                     "image in GitHub Codespaces.")

    # ---------------------------------------------------------------- verification
    H = json.loads((ROOT / "results" / "harness_check.json").read_text())
    hrows = H["rows"]
    projs = sorted({r["project"] for r in hrows})
    allok = all(r["ok"] for r in hrows)
    uns = {r["project"]: r["unsplit"] for r in hrows}
    per = "; ".join(f"{p.split('/')[1]} {uns[p]}/{uns[p]}" for p in projs)
    A["verification"] = (
        "{bi:Pipeline verification without model calls:} To check that splitting, merging and scoring do not "
        "themselves change the outcome, DevBench’s reference implementation is cut into the fragments that each "
        "agent of each condition would own, merged by the same deterministic merge step as agent output, and "
        f"scored. Every condition must reach the score of the unsplit reference code, and every condition does "
        f"({per}, for G2, G4, GC, G6 and G7{'' if allok else '; see the released log for exceptions'}). "
        "A smoke run before the pilot exposed four defects in the harness, all fixed before any comparison and "
        "applied identically to every condition: a missing package installer on the host, subclasses merged "
        "before their base class, traceability markers written by the model without a comment sign, and classes "
        "split across agents losing methods in the merge. These changes are listed as deviations in the released "
        "pre-registration folder.")

    # ---------------------------------------------------------------- model probe
    P = [json.loads(l) for l in (ROOT / "results" / "probe.jsonl").read_text().splitlines() if l.strip()]
    prow = []
    for r in P:
        prow.append([r["model"].split("/")[1], "yes" if r["seq"] else "no", r["project"].split("/")[1],
                     f'{r["passed"]}/{r["of"]}', f'{r["tokens"]:,}'])
    A["probe_rows"] = prow
    A["probe"] = (
        "{bi:Model selection:} The model was chosen before the pilot by a probe that runs only the single-agent "
        "condition (G2), so the choice cannot favor any way of splitting. The decision rule was written down "
        "before the probe: switch to a larger reasoning model only if it passes at least three more tests in "
        "total, and add DevBench’s sequence diagram to every agent’s input only if it does not lower the score. "
        "Neither condition was met (Table IV): the larger model passed the same number of tests at about five "
        "times the tokens, and the sequence diagram did not help, so the pilot keeps the cheaper model and the "
        "original inputs.")

    # ---------------------------------------------------------------- pilot
    ps = ROOT / "results" / "pilot_summary.json"
    A["pilot"] = None
    if ps.exists():
        S = json.loads(ps.read_text())
        T, D = S["table"], S["decision"]
        rows = []
        for p, t in T.items():
            tot = totals.get(p)
            for c in COND:
                v = t["conditions"].get(c)
                if not v:
                    continue
                pr = v["pass_rate"]
                tests = "–" if pr is None or tot is None else f"{pr * tot:.1f}/{tot}"
                runs = ", ".join("–" if x is None else f"{x * tot:.0f}" for x in v["pass_rate_runs"]) if tot else ""
                rows.append([p.split("/")[1], f"{c} {NAME[c]}", str(v["k"]), tests, runs,
                             "–" if v["tokens"] is None else f"{v['tokens']:,.0f}",
                             "–" if v["messages"] is None else f"{v['messages']:.1f}",
                             (f"same team as {v['same_as']}" if v["same_as"] else "")])
        A["pilot_rows"] = rows
        verdict = D["verdict"]
        r1 = D["rule_G7_beats_G4_majority"]
        bits = []
        for p, t in T.items():
            c = t["conditions"]
            tot = totals.get(p) or 1
            if "G7" in c and "G4" in c and c["G7"]["pass_rate"] is not None and c["G4"]["pass_rate"] is not None:
                g7, g4 = c["G7"]["pass_rate"] * tot, c["G4"]["pass_rate"] * tot
                if t["k_star"] and t["k_star"] > 1:
                    bits.append(f"on {p.split('/')[1]} (k* = {t['k_star']}) the criterion team passed {g7:.1f} tests "
                                f"on average against {g4:.1f} for random teams of the same sizes, using "
                                f"{c['G7']['tokens']:,.0f} against {c['G4']['tokens']:,.0f} tokens per run")
            if t["k_star"] == 1 and "G2" in c and c["G2"]["pass_rate"] is not None:
                oth = {x: c[x]["pass_rate"] * tot for x in ("G4", "GC") if x in c and c[x]["pass_rate"] is not None}
                if oth:
                    bits.append(f"on {p.split('/')[1]} (k* = 1) the single agent passed {c['G2']['pass_rate'] * tot:.1f} "
                                f"tests against " + " and ".join(f"{v:.1f} ({k})" for k, v in oth.items()))
        A["pilot"] = (
            "{bi:Pilot (Python projects):} Table V reports three runs per condition. " +
            (("; ".join(bits)[:1].upper() + "; ".join(bits)[1:] + ". ") if bits else "") +
            (f"The pre-registered go/no-go analysis gives a provisional {verdict.split(' ')[0]} on the Python "
             f"projects alone; the decision becomes final once the C++ and Java pilot projects are scored"
             if "provisional" in verdict else f"The pre-registered go/no-go analysis returns {verdict}") +
            ". Absolute pass rates are low for every condition, because several tests require identifiers that "
            "appear neither in the requirements nor in the design (for example, a class constant named in a test "
            "only); conditions are therefore compared only with each other. With two projects and three runs, the "
            "pilot shows direction and cost, not statistical significance; H1–H4 are tested in the main study. "
            f"The Python pilot used {sum((v.get('tokens') or 0) * (v.get('runs') or 0) for t in T.values() for v in t['conditions'].values() if not v.get('same_as')):,.0f} "
            "tokens in total, which cost less than one US dollar with this model.")
        A["pilot_short"] = ("; ".join(bits) + ".") if bits else ""
        A["verdict"] = verdict
        # figure
        import matplotlib
        matplotlib.use("Agg")
        matplotlib.rcParams["pdf.fonttype"] = 42
        import matplotlib.pyplot as plt
        import numpy as np
        pj = list(T)
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
        colors = {"G2": "#888780", "G4": "#B4B2A9", "GC": "#7F77DD", "G6": "#378ADD", "G7": "#1D9E75"}
        w = 0.16
        for i, c in enumerate(COND):
            x = np.arange(len(pj)) + (i - 2) * w
            for ax, key in zip(axes, ("pass_rate", "tokens")):
                vals = []
                for p in pj:
                    v = T[p]["conditions"].get(c, {}).get(key)
                    vals.append(0 if v is None else (v * 100 if key == "pass_rate" else v / 1000))
                ax.bar(x, vals, w, color=colors[c], label=f"{c} {NAME[c]}")
        for ax, lab in zip(axes, ("tests passed (%)", "tokens per run (thousands)")):
            ax.set_xticks(np.arange(len(pj)), [p.split("/")[1] for p in pj], fontsize=8)
            ax.set_ylabel(lab, fontsize=8)
            ax.tick_params(labelsize=7)
            ax.spines[["top", "right"]].set_visible(False)
        axes[0].legend(fontsize=6, frameon=False, loc="upper right")
        fig.tight_layout()
        (ROOT / "paper" / "figures").mkdir(exist_ok=True)
        fig.savefig(ROOT / "paper" / "figures" / "pilot.pdf")
        fig.savefig(ROOT / "paper" / "figures_docx" / "fig_pilot.png", dpi=220)
        plt.close(fig)
        ab = []
        for p, t in T.items():
            c, tot = t["conditions"], totals.get(p) or 1
            if (t["k_star"] or 1) > 1 and all(x in c and c[x]["pass_rate"] is not None for x in ("G7", "G4")):
                ab.append(f"the criterion team passed {c['G7']['pass_rate'] * tot:.1f} of {tot} tests on "
                          f"{p.split('/')[1]} against {c['G4']['pass_rate'] * tot:.1f} for equal-size random teams")
            if t["k_star"] == 1 and "G2" in c and c["G2"]["pass_rate"] is not None:
                oth = [c[x]["pass_rate"] for x in ("G4", "GC") if x in c and c[x]["pass_rate"] is not None]
                if oth:
                    better = c["G2"]["pass_rate"] >= max(oth)
                    ab.append(f"where it recommends one agent ({p.split('/')[1]}), the single agent "
                              f"{'matched or beat' if better else 'trailed'} every split team")
        A["abstract"] = ("In a pre-registered pilot with an open-weight coding model, " + "; ".join(ab) +
                         "; absolute scores are low for all teams, and the main study adds tasks and a second model.")
        A["conclusion"] = ("In a first pre-registered pilot, " + A["pilot_short"] +
                           " These pilot results show direction and cost only; the main study tests the hypotheses "
                           "on more projects and a second model.")
    else:
        A["pilot_rows"] = None
        A["pilot"] = "{P:Pilot table (stocktrends and lice): tests passed, tokens and messages per condition}"
        A["abstract"] = ("{P:pilot result: tests passed and tokens of the criterion team against single-agent, random, "
                         "one-agent-per-class and Infomap teams}")
        A["conclusion"] = "{P:one-sentence pilot result, stated only as strongly as the evidence allows}"
    A["contribution4"] = ("A pre-registered agent study with four hypotheses, controlled conditions, an equal token "
                          "budget per run, a zero-cost verification of the agent harness and a pilot on DevBench "
                          "(Section VI).")
    A["threat_extra"] = ("DevBench’s tests also check identifiers that are absent from the requirements and the "
                         "design, which lowers every condition’s absolute score; TextCNN is excluded from the pilot "
                         "because its reference code passes only 5 of 13 tests in the sandbox, as the pre-registered "
                         "scorer rule requires.")
    A["main_pending"] = [
        "{bi:Main study (planned, pre-registered):} The confirmatory tests follow the pilot. H1 uses a paired "
        "Wilcoxon signed-rank test over tasks with Holm correction and reports bootstrap confidence intervals; H2 "
        "correlates cut weight with logged messages per agent pair (Spearman); H3 cross-tabulates the split or "
        "no-split decision against the empirically better choice; and H4 repeats H1 with designs extracted from the "
        "requirements. The study adds the C++ and Java DevBench projects, further multi-agent tasks to reach the "
        "roughly 36 that the power analysis requires, and a second model from a different model family."]

    GEN.mkdir(parents=True, exist_ok=True)
    (GEN / "agent.json").write_text(json.dumps({k: (to_docx(v) if isinstance(v, str) else v)
                                                for k, v in A.items()}, indent=1, ensure_ascii=False))

    # ---------------------------------------------------------------- LaTeX
    L = []
    L.append(to_latex(A["verification"].replace("{bi:Pipeline verification without model calls:}",
                                                 r"\paragraph{Pipeline verification without model calls.}")) + "\n")
    L.append(to_latex(A["probe"].replace("{bi:Model selection:}", r"\paragraph{Model selection.}")
                      .replace("(Table IV)", r"(Table~\ref{tab:probe})")) + "\n")
    L.append(r"""\begin{table}[t]\centering\small
\caption{Single-agent model probe (G2) used to choose the pilot model before any team comparison.}\label{tab:probe}
\begin{tabular}{llllr}\toprule
Model & Seq. diagram & Project & Tests & Tokens\\\midrule
""" + "\n".join(" & ".join(to_latex(x) for x in r) + r"\\" for r in A["probe_rows"]) +
             "\n\\bottomrule\\end{tabular}\\end{table}\n")
    if A["pilot_rows"]:
        L.append(to_latex(A["pilot"].replace("{bi:Pilot (Python projects):}", r"\paragraph{Pilot (Python projects).}")
                          .replace("Table V", r"Table~\ref{tab:pilot}")) + "\n")
        L.append(r"""\begin{table*}[t]\centering\small
\caption{Pilot on DevBench's Python projects: mean tests passed over three runs (per-run counts in brackets), mean tokens and messages per run. Identical teams receive identical prompts and cached responses.}\label{tab:pilot}
\begin{tabular}{lllllrrl}\toprule
Project & Condition & Agents & Tests (mean) & Runs & Tokens & Messages & Note\\\midrule
""" + "\n".join(" & ".join(to_latex(x) for x in r) + r"\\" for r in A["pilot_rows"]) +
                 "\n\\bottomrule\\end{tabular}\\end{table*}\n")
        L.append(r"""\begin{figure}[t]\centering\includegraphics[width=\linewidth]{figures/pilot.pdf}
\caption{Pilot: tests passed (left) and tokens per run (right) for each condition.}\label{fig:pilot}\end{figure}
""")
    else:
        L.append(to_latex(A["pilot"]) + "\n")
    for t in A["main_pending"]:
        L.append(to_latex(t) + "\n")
    (GEN / "agent_results.tex").write_text("\n".join(L))
    M = [r"\newcommand{\ModelSentence}{" + to_latex(A["model_sentence"]) + "}",
         r"\newcommand{\RunHardware}{" + to_latex(A["hardware"]) + "}",
         r"\newcommand{\AgentAbstract}{" + to_latex(A["abstract"]) + "}",
         r"\newcommand{\AgentConclusion}{" + to_latex(A["conclusion"]) + "}",
         r"\newcommand{\ContributionFour}{" + to_latex(A["contribution4"]) + "}",
         r"\newcommand{\ThreatExtra}{" + to_latex(A["threat_extra"]) + "}"]
    (GEN / "agent_macros.tex").write_text("\n".join(M) + "\n")
    print("pilot included:", bool(A["pilot_rows"]))


if __name__ == "__main__":
    main()
