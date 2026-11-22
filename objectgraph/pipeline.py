"""Run one condition (team) on one DevBench project: design -> duty graph ->
team -> agents -> score, and write a step-by-step report."""
from __future__ import annotations

import json
from pathlib import Path

from .uml import parse_class_diagram
from .graph import build_duty_graph
from .criterion import select_k
from .extract import extract_design, compare_to_gold
from .team import build_team
from .conditions import build_conditions, DESCRIPTION
from . import report as R


def find(project_dir: Path, name: str) -> Path | None:
    for p in (project_dir / name, project_dir / "docs" / name):
        if p.exists():
            return p
    return None


def load_project(devbench: Path, project: str) -> dict:
    pdir = Path(devbench) / "benchmark_data" / project
    arch = find(pdir, "architecture_design.md")
    return {"dir": pdir, "prd": find(pdir, "PRD.md").read_text(encoding="utf-8"),
            "arch": arch.read_text(encoding="utf-8") if arch else "",
            "seq": (find(pdir, "UML_sequence.md").read_text(encoding="utf-8")
                    if find(pdir, "UML_sequence.md") else ""),
            "gold_text": find(pdir, "UML_class.md").read_text(encoding="utf-8")}


def get_design(proj: dict, design: str, llm, run_id: int) -> dict:
    gold = parse_class_diagram(proj["gold_text"])
    if design == "gold":
        return {"text": proj["gold_text"], "diagram": gold, "log": [], "cmp": None}
    text, diagram, log = extract_design(llm, proj["prd"], run_id=run_id)
    return {"text": text, "diagram": diagram, "log": log, "cmp": compare_to_gold(diagram, gold)}


def run_condition(proj: dict, project: str, design: dict, condition: str, llm, run_id: int,
                  out: Path, ref_tests: Path | None, agents: bool = True, score: bool = True,
                  scorer: str = "auto", docker_image: str = "devbench:complete", lam: float = 0.0,
                  budget: int | None = None, use_seq: bool = False) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    diagram = design["diagram"]
    g = build_duty_graph(diagram)
    conds = build_conditions(g, lam)
    labels = conds[condition]["labels"]
    team = build_team(condition, labels, g, diagram)
    k_star, crit_labels, curve = select_k(g.W, lam)
    pos = R.duty_layout(g)
    (out / "design.md").write_text(design["text"], encoding="utf-8")

    if design["cmp"] is None:
        expl1 = "DevBench's own class diagram (<i>gold</i> design; an upper bound)."
    else:
        c = design["cmp"]
        expl1 = (f"Claude wrote this from the PRD alone (<i>extracted</i> design). Repairs: "
                 f"{len(design['log']) - 1}. Match to gold classes: precision {c['precision']}, "
                 f"recall {c['recall']}, F1 {c['f1']}.")
    sections = [
        ("Step 1 - Build the domain model", expl1, [R.fig_domain_model(diagram)], ""),
        ("Step 2 - Turn the design into a duty graph",
         "Every method is a duty (dot); line width is dependency weight.", [R.fig_duty_graph(g, pos)], ""),
        ("Step 3 - Cohesion, coupling and team size",
         f"The criterion's best team size is <b>k* = {k_star}</b>.", [R.fig_cohesion(g, curve, k_star)], ""),
        (f"Step 4 - Team for condition {condition}: {DESCRIPTION[condition]}",
         f"{team.k} agent(s). Run order: <b>{' &rarr; '.join(team.order)}</b>."
         + (f" This team is identical to {conds[condition]['same_as']}." if conds[condition]["same_as"] else ""),
         [R.fig_team(g, labels, pos, team)] + ([R.fig_cc_matrix(g, labels, team)] if team.k > 1 else []),
         R.team_table(team) + R.duty_lists(team)),
    ]
    summary = {"project": project, "condition": condition, "description": DESCRIPTION[condition],
               "run_id": run_id, "k": team.k, "k_star": int(k_star), "duties": g.n, "cut": team.cut,
               "same_as": conds[condition]["same_as"], "design_vs_gold": design["cmp"]}
    (out / "team.json").write_text(json.dumps(team.to_dict(), indent=2))

    if agents:
        from .orchestrator import run_team, save_run
        from .llm import Usage
        llm.usage = Usage()
        if budget is not None:
            llm.token_budget = budget
        res = run_team(team, llm, proj["prd"], design["text"], proj["arch"], run_id=run_id,
                       seq=proj["seq"] if use_seq else "")
        usage = {"input_tokens": llm.usage.input_tokens, "output_tokens": llm.usage.output_tokens,
                 "calls": llm.usage.calls, "cached_calls": llm.usage.cached_calls, "by_tag": llm.usage.by_tag}
        save_run(res, team, out, usage)
        run = json.loads((out / "run.json").read_text())
        sections.append(("Step 5 - Run the agents",
                         f"Tokens {llm.usage.total:,}; messages {len(res.messages)}; traceability "
                         f"{100 * res.traceability:.0f}%."
                         + (" <b>Stopped at the token cap.</b>" if res.stopped_by_budget else ""),
                         [R.fig_run(team, run)], ""))
        summary.update({"tokens": llm.usage.total, "input_tokens": llm.usage.input_tokens,
                        "output_tokens": llm.usage.output_tokens, "messages": len(res.messages),
                        "message_tokens": sum(m["tokens"] for m in res.messages),
                        "traceability": res.traceability, "stopped_by_budget": res.stopped_by_budget})
        if score:
            from .score import score_project
            sc = score_project(proj["dir"], res.files, scorer=scorer, docker_image=docker_image)
            if sc.get("status") == "scored" and ref_tests and ref_tests.exists():
                for r in json.loads(ref_tests.read_text()):
                    if r["project"] == project and "status" not in r:
                        tot = sum(r[k]["passed"] + r[k]["failed"] + r[k]["errors"]
                                  for k in ("unit_test", "acceptance_test") if k in r)
                        sc["reference_total"] = tot
                        sc["pass_rate"] = round(sc["passed"] / max(tot, sc["total"], 1), 4)
            (out / "score.json").write_text(json.dumps(sc, indent=2))
            summary["score"] = sc
            summary["pass_rate"] = sc.get("pass_rate")
            txt = (f"<b>{sc['passed']} / {sc.get('reference_total', sc['total'])}</b> tests passed."
                   if sc.get("status") == "scored" else f"Not scored: {sc.get('status')}.")
            sections.append(("Step 6 - Score with DevBench's tests", txt, [], ""))
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    title = f"{project} - {condition} ({DESCRIPTION[condition]}), run {run_id}"
    (out / "report.html").write_text(R.build_html(title, sections), encoding="utf-8")
    return summary
