"""Zero-token check of the team pipeline (split -> merge -> score).

For every condition, each agent is given DevBench's own answer code, cut down to
the methods of the duties assigned to it (plus module-level code). The fragments
are merged exactly as agent output is merged and scored with DevBench's tests.
If the merge and scoring are correct, every condition must reach the score of
the unsplit answer code. No model is called.

    python scripts/check_harness.py --projects python/stocktrends python/lice
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from objectgraph.pipeline import load_project            # noqa: E402
from objectgraph.uml import parse_class_diagram           # noqa: E402
from objectgraph.graph import build_duty_graph            # noqa: E402
from objectgraph.conditions import build_conditions, CONDITIONS  # noqa: E402
from objectgraph.team import build_team                   # noqa: E402
from objectgraph.orchestrator import _py_units, _indent, merge_fragments  # noqa: E402
from objectgraph.score import score_project               # noqa: E402


def agent_fragment(code: str, duties: set[str]) -> str:
    parts = []
    classes_with_duty = {d.split(".")[0] for d in duties}
    for kind, name, info, text in _py_units(code):
        if kind in ("import", "stmt", "def", "main"):
            parts.append(text)
        elif kind == "class" and name in classes_with_duty:
            mine = [t for m, t in info["methods"] if f"{name}.{m}" in duties]
            body = [_indent(t) for t in info["members"]] + [_indent(t) for t in mine]
            parts.append(info["header"].rstrip() + "\n" + ("\n\n".join(body) if body else "    pass"))
    return "\n\n\n".join(parts) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", nargs="+", required=True)
    ap.add_argument("--devbench", default=str(ROOT / "DevBench"))
    ap.add_argument("--conditions", nargs="*", default=CONDITIONS)
    a = ap.parse_args()
    rows = []
    for project in a.projects:
        proj = load_project(Path(a.devbench), project)
        cfg = json.loads((proj["dir"] / "repo_config.json").read_text())
        ref_files = [p for p in cfg.get("code_file_DAG", {}) if p.endswith(".py")]
        ref_code = {p: (proj["dir"] / p).read_text(encoding="utf-8") for p in ref_files}
        full = score_project(proj["dir"], ref_code)
        diagram = parse_class_diagram(proj["gold_text"])
        g = build_duty_graph(diagram)
        conds = build_conditions(g)
        print(f"{project}: unsplit answer code {full['passed']}/{full['total']}")
        for c in a.conditions:
            team = build_team(c, conds[c]["labels"], g, diagram)
            by_id = {x.agent_id: x for x in team.agents}
            files = {}
            for p, code in ref_code.items():
                frs, owners = [], []
                for aid in team.order:
                    ag = by_id[aid]
                    frs.append(agent_fragment(code, set(ag.duties)))
                    owners.append(set(ag.duties))
                files[p] = merge_fragments(p, frs, owners)
            sc = score_project(proj["dir"], files)
            ok = sc["passed"] == full["passed"]
            print(f"  {c:3} k={team.k}: {sc['passed']}/{sc['total']}  {'OK' if ok else 'MISMATCH'}")
            rows.append({"project": project, "condition": c, "k": team.k, "passed": sc["passed"],
                         "unsplit": full["passed"], "ok": ok})
    bad = [r for r in rows if not r["ok"]]
    print("\nHARNESS OK" if not bad else f"\nHARNESS PROBLEMS: {len(bad)}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
