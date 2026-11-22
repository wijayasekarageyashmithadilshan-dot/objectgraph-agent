"""Run ObjectGraph-Agent end to end on one DevBench project and draw every step.

  # steps 1-4 only, gold design, no API needed:
  python scripts/run_pipeline.py --project python/stocktrends --no-agents

  # full run with Claude (key in the ANTHROPIC_API_KEY environment variable):
  python scripts/run_pipeline.py --project python/stocktrends --design extracted \
      --provider anthropic --model claude-sonnet-5-5 --run-id 0

  # rebuild the same run later without any API calls:
  python scripts/run_pipeline.py ... --offline

Output: runs/<project>/<design>/<method>/run<id>/  (report.html, team.json,
run.json, score.json, code/, design.md) and the reply cache in cache/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from objectgraph.uml import parse_class_diagram                     # noqa: E402
from objectgraph.graph import build_duty_graph                      # noqa: E402
from objectgraph.criterion import select_k, mq, cut_weight          # noqa: E402
from objectgraph.extract import extract_design, compare_to_gold     # noqa: E402
from objectgraph.team import build_team                             # noqa: E402
from objectgraph.llm import LLM                                     # noqa: E402
from objectgraph import report as R                                 # noqa: E402


def find(project_dir: Path, name: str) -> Path | None:
    for p in (project_dir / name, project_dir / "docs" / name):
        if p.exists():
            return p
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--devbench", default=str(ROOT / "DevBench"))
    ap.add_argument("--project", required=True, help="e.g. python/stocktrends")
    ap.add_argument("--design", choices=["gold", "extracted"], default="gold")
    ap.add_argument("--provider", choices=["anthropic", "fake"], default="anthropic")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--run-id", type=int, default=0)
    ap.add_argument("--lam", type=float, default=0.0)
    ap.add_argument("--budget", type=int, default=200_000, help="token cap per run (all agents)")
    ap.add_argument("--offline", action="store_true", help="replay from cache only")
    ap.add_argument("--no-agents", action="store_true", help="stop after step 4")
    ap.add_argument("--no-score", action="store_true")
    ap.add_argument("--cache", default=str(ROOT / "cache"))
    ap.add_argument("--out", default=str(ROOT / "runs"))
    a = ap.parse_args()

    pdir = Path(a.devbench) / "benchmark_data" / a.project
    prd = find(pdir, "PRD.md").read_text(encoding="utf-8")
    arch_p = find(pdir, "architecture_design.md")
    arch = arch_p.read_text(encoding="utf-8") if arch_p else ""
    gold_text = find(pdir, "UML_class.md").read_text(encoding="utf-8")
    gold = parse_class_diagram(gold_text)
    out = Path(a.out) / a.project.replace("/", "__") / a.design / "criterion" / f"run{a.run_id}"
    out.mkdir(parents=True, exist_ok=True)

    fake_fn = None
    if a.provider == "fake":
        from tests.fake_model import fake_reply
        fake_fn = lambda s, u: fake_reply(s, u, gold_text)
    llm = LLM(a.provider, a.model, a.cache, offline=a.offline, token_budget=a.budget, fake_fn=fake_fn)

    sections = []
    # Step 1 - domain model
    if a.design == "gold":
        design_text, diagram, extract_log, cmp = gold_text, gold, [], None
        expl = ("The domain model is DevBench's own class diagram (<i>gold</i> design). It was "
                "written together with the answer code, so it is an upper bound.")
    else:
        design_text, diagram, extract_log = extract_design(llm, prd, run_id=a.run_id)
        cmp = compare_to_gold(diagram, gold)
        expl = ("Claude read only the PRD and wrote this class diagram (<i>extracted</i> design). "
                f"Repair attempts: {len(extract_log) - 1}. Classes matched to the gold design: "
                f"precision {cmp['precision']}, recall {cmp['recall']}, F1 {cmp['f1']} "
                f"(missing: {', '.join(cmp['missing']) or 'none'}; extra: {', '.join(cmp['extra']) or 'none'}).")
    (out / "design.md").write_text(design_text, encoding="utf-8")
    sections.append(("Step 1 - Build the domain model", expl, [R.fig_domain_model(diagram)], ""))

    # Step 2 - duty graph
    g = build_duty_graph(diagram)
    pos = R.duty_layout(g)
    sections.append(("Step 2 - Turn the design into a duty graph",
                     "Every method becomes a <b>duty</b> (a dot). Duties are linked when they share a "
                     "class (1.0), their classes inherit/compose (0.5) or use each other (0.25), or a "
                     "method's signature names another class (0.5).", [R.fig_duty_graph(g, pos)], ""))

    # Step 3 - cohesion, coupling, team size
    k_star, labels, curve = select_k(g.W, a.lam)
    team = build_team("criterion", labels, g, diagram)
    sections.append(("Step 3 - Score cohesion and coupling to choose the team size",
                     "Average-linkage clustering merges the most strongly linked duties first (3a). "
                     "Cutting the tree at every height gives a team of every size, and each one is "
                     "scored with MQ: average cohesion inside agents minus average coupling between "
                     f"agents (3b). The best score picks <b>k* = {k_star}</b>. The matrix (3c) shows "
                     "the chosen team's cohesion and coupling.",
                     [R.fig_cohesion(g, curve, k_star)] + ([R.fig_cc_matrix(g, labels, team)] if k_star > 1 else []),
                     ""))
    # Step 4 - task allocation
    sections.append(("Step 4 - Give each agent its tasks",
                     "Each group becomes one agent that owns those duties and the classes they belong "
                     f"to. Agents run in dependency order: <b>{' &rarr; '.join(team.order)}</b>.",
                     [R.fig_team(g, labels, pos, team)], R.team_table(team) + R.duty_lists(team)))
    summary = {"project": a.project, "design": a.design, "k_star": int(k_star), "duties": g.n,
               "mq": round(curve[k_star], 4), "cut": team.cut, "extract_log": extract_log,
               "design_vs_gold": cmp}
    (out / "team.json").write_text(json.dumps(team.to_dict(), indent=2))

    # Steps 5-6 - run the agents and score
    if not a.no_agents:
        from objectgraph.orchestrator import run_team, save_run
        res = run_team(team, llm, prd, design_text, arch, run_id=a.run_id)
        usage = {"input_tokens": llm.usage.input_tokens, "output_tokens": llm.usage.output_tokens,
                 "calls": llm.usage.calls, "cached_calls": llm.usage.cached_calls,
                 "by_tag": llm.usage.by_tag}
        save_run(res, team, out, usage)
        run = json.loads((out / "run.json").read_text())
        sections.append(("Step 5 - Run the agents",
                         f"Model <code>{a.model}</code>, run {a.run_id}, token cap {a.budget:,}. "
                         f"Total tokens {llm.usage.total:,} ({llm.usage.cached_calls} of "
                         f"{llm.usage.calls} calls replayed from cache). Duties marked in the code "
                         f"(traceability): {100 * res.traceability:.0f}%."
                         + (" <b>Stopped at the token cap.</b>" if res.stopped_by_budget else ""),
                         [R.fig_run(team, run)], ""))
        summary.update({"tokens": llm.usage.total, "messages": len(res.messages),
                        "traceability": res.traceability, "stopped_by_budget": res.stopped_by_budget})
        if not a.no_score:
            from objectgraph.score import score_python
            sc = score_python(pdir, res.files)
            ref = ROOT / "results" / "reference_tests.json"
            if sc.get("status") == "scored" and ref.exists():
                for r in json.loads(ref.read_text()):
                    if r["project"] == a.project:
                        ref_total = sum(r[k]["passed"] + r[k]["failed"] + r[k]["errors"]
                                        for k in ("unit_test", "acceptance_test") if k in r)
                        sc["reference_total"] = ref_total
                        sc["pass_rate"] = round(sc["passed"] / max(ref_total, sc["total"], 1), 4)
            (out / "score.json").write_text(json.dumps(sc, indent=2))
            summary["score"] = sc
            txt = (f"<b>{sc['passed']} / {sc.get('reference_total', sc['total'])}</b> DevBench tests "
                   f"passed (pass rate {sc['pass_rate']:.2f})." if sc.get("status") == "scored"
                   else f"Not scored here: {sc.get('status')} ({sc.get('language')}).")
            sections.append(("Step 6 - Score the code with DevBench's tests",
                             "The reference implementation is deleted, the agents' files are put in its "
                             "place, and DevBench's unit and acceptance tests run in a fresh environment. "
                             + txt, [], ""))
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    title = f"ObjectGraph-Agent - {a.project} ({a.design} design, run {a.run_id})"
    (out / "report.html").write_text(R.build_html(title, sections), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "extract_log"}, indent=1))
    print(f"report: {out / 'report.html'}")


if __name__ == "__main__":
    main()
