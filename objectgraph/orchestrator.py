"""Step 5: run an agent team and merge its code.

The same orchestrator runs every condition; only the TeamSpec changes.

* Agents run in the TeamSpec's dependency order.
* Every agent sees the PRD, the full domain model and the architecture
  design (DevBench's standard inputs), plus its own duty list with IDs.
* An agent also receives the code already written by the agents it depends
  on. Each such hand-over is one "message", and its size is logged in tokens.
* Agents answer with ``### FILE: <path>`` blocks containing only their own
  classes. Fragments for the same file are merged: imports first
  (de-duplicated), then fragments in dependency order.
* Agents mark each implemented duty with a ``duty: <Class.method>`` comment,
  which gives the traceability score.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .llm import LLM, BudgetExceeded
from .team import TeamSpec

SYSTEM = (
    "You are one engineer in a team of AI agents building a software project. You "
    "implement ONLY the classes and duties assigned to you, exactly as named in the "
    "domain model, so that the other agents' code fits with yours. Put a comment "
    "`duty: <Class.method>` directly above every method you implement. Answer only "
    "with one or more blocks of the form:\n### FILE: <relative/path>\n```<language>\n"
    "<code>\n```\nUse the file paths from the architecture design. Do not write tests.")

USER_TMPL = """# Product requirements
{prd}

# Domain model (whole team)
{design}

# Architecture design (file layout)
{arch}

# Your assignment ({agent_id} of {k})
Classes you own: {classes}
Duties you must implement (ID = Class.method):
{duties}
{others}
{received}
Write your code now."""

_BLOCK = re.compile(r"###\s*FILE:\s*(?P<path>\S+)\s*\n```[^\n]*\n(?P<code>.*?)```", re.S)


@dataclass
class RunResult:
    files: dict[str, str]
    agent_outputs: dict[str, str]
    messages: list[dict] = field(default_factory=list)
    stopped_by_budget: bool = False
    traceability: float = 0.0


def parse_blocks(text: str) -> list[tuple[str, str]]:
    return [(m.group("path").strip("`"), m.group("code")) for m in _BLOCK.finditer(text)]


def merge_fragments(path: str, fragments: list[str]) -> str:
    if len(fragments) == 1:
        return fragments[0]
    if path.endswith(".py"):
        imports, bodies, seen = [], [], set()
        for frag in fragments:
            body = []
            for line in frag.splitlines():
                if re.match(r"^(import |from \S+ import )", line):
                    if line.strip() not in seen:
                        seen.add(line.strip())
                        imports.append(line)
                else:
                    body.append(line)
            bodies.append("\n".join(body).strip("\n"))
        return "\n".join(imports) + "\n\n\n" + "\n\n\n".join(bodies) + "\n"
    return "\n\n".join(fragments)


def run_team(team: TeamSpec, llm: LLM, prd: str, design_text: str, arch: str,
             run_id: int = 0) -> RunResult:
    by_id = {a.agent_id: a for a in team.agents}
    outputs: dict[str, str] = {}
    fragments: dict[str, list[str]] = {}
    messages = []
    stopped = False
    for aid in team.order:
        a = by_id[aid]
        others = ""
        if team.k > 1:
            lines = [f"- {o.agent_id} owns: {', '.join(o.classes)}" for o in team.agents if o.agent_id != aid]
            others = "\nOther agents (do NOT implement their classes):\n" + "\n".join(lines) + "\n"
        received = ""
        for dep in a.depends_on:
            if dep in outputs:
                code = "\n\n".join(f"### FILE: {p}\n{c}" for p, c in parse_blocks(outputs[dep]))
                received += f"\n# Code already written by {dep} (you depend on it)\n{code}\n"
                messages.append({"from": dep, "to": aid, "tokens": len(code) // 4})
        user = USER_TMPL.format(prd=prd, design=design_text, arch=arch, agent_id=aid, k=team.k,
                                classes=", ".join(a.classes),
                                duties="\n".join(f"- {d}" for d in a.duties),
                                others=others, received=received)
        try:
            out = llm.call(SYSTEM, user, tag=aid, run_id=run_id)
        except BudgetExceeded:
            stopped = True
            break
        outputs[aid] = out
        for path, code in parse_blocks(out):
            fragments.setdefault(path, []).append(code)
    files = {p: merge_fragments(p, frs) for p, frs in fragments.items()}
    all_duties = [d for a in team.agents for d in a.duties if not d.endswith(".<state>")]
    code_all = "\n".join(files.values())
    traced = sum(1 for d in all_duties if re.search(rf"duty:\s*{re.escape(d)}\b", code_all))
    trace = traced / len(all_duties) if all_duties else 1.0
    return RunResult(files, outputs, messages, stopped, round(trace, 4))


def save_run(res: RunResult, team: TeamSpec, out_dir: Path, usage: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for p, code in res.files.items():
        f = out_dir / "code" / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(code, encoding="utf-8")
    (out_dir / "team.json").write_text(json.dumps(team.to_dict(), indent=2))
    (out_dir / "run.json").write_text(json.dumps({
        "messages": res.messages, "stopped_by_budget": res.stopped_by_budget,
        "traceability": res.traceability, "files": sorted(res.files), "usage": usage}, indent=2))
    for aid, text in res.agent_outputs.items():
        (out_dir / f"{aid}.md").write_text(text, encoding="utf-8")
