"""Step 5: run an agent team and merge its code.

The same orchestrator runs every condition; only the TeamSpec changes.

* Agents run in the TeamSpec's dependency order.
* Every agent sees the PRD, the full domain model and the architecture
  design (DevBench's standard inputs), plus its own duty list with IDs.
* An agent also receives the code already written by the agents it depends
  on. Each such hand-over is one "message", and its size is logged in tokens.
* Agents answer with ``### FILE: <path>`` blocks containing only their own
  classes. Fragments for the same file are merged by syntax (see
  merge_fragments): imports first, base classes before subclasses, and the
  class owner's version kept if a class is written twice.
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


def _py_units(code: str):
    """Split Python source into (kind, name, bases, text) top-level units."""
    import ast
    tree = ast.parse(code)
    lines = code.splitlines()
    units = []
    for node in tree.body:
        start = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno]) - 1
        while start > 0 and lines[start - 1].lstrip().startswith("#"):
            start -= 1          # keep comment lines directly above the unit
        text = "\n".join(lines[start:node.end_lineno])
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            units.append(("import", None, [], text))
        elif isinstance(node, ast.ClassDef):
            bases = [b.id if isinstance(b, ast.Name) else getattr(b, "attr", "") for b in node.bases]
            units.append(("class", node.name, bases, text))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            units.append(("def", node.name, [], text))
        elif (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
              and getattr(node.test.left, "id", "") == "__name__"):
            units.append(("main", None, [], text))
        else:
            units.append(("stmt", None, [], text))
    return units


def merge_fragments(path: str, fragments: list[str], owners: list[set[str]] | None = None) -> str:
    """Merge several agents' fragments of one file.

    Python files are merged by syntax: imports first (de-duplicated), then other
    module-level code, then classes ordered so that a base class comes before
    the classes that inherit from it, then any ``if __name__ == "__main__"``
    block. If two fragments define the same class, the version written by the
    agent that owns the class is kept (``owners[i]`` = classes owned by the
    author of ``fragments[i]``); otherwise the longer version is kept. The same
    rule applies to every condition. If a fragment does not parse, fall back to
    simple concatenation.
    """
    if len(fragments) == 1:
        return fragments[0]
    if path.endswith(".py"):
        try:
            per = [_py_units(f) for f in fragments]
        except SyntaxError:
            per = None
        if per is not None:
            imports, seen_imp, stmts, defs, classes, mains = [], set(), [], {}, {}, []
            for i, units in enumerate(per):
                own = owners[i] if owners and i < len(owners) else set()
                for kind, name, bases, text in units:
                    if kind == "import":
                        for line in text.splitlines():
                            if line.strip() and line.strip() not in seen_imp:
                                seen_imp.add(line.strip())
                                imports.append(line)
                    elif kind == "class":
                        prev = classes.get(name)
                        cand = (name in own, len(text), i)
                        if prev is None or cand[:2] > prev[0][:2]:
                            classes[name] = (cand, bases, text, prev[3] if prev else len(classes))
                    elif kind == "def":
                        if name not in defs or len(text) > len(defs[name]):
                            defs[name] = text
                    elif kind == "main":
                        if text not in mains:
                            mains.append(text)
                    elif text not in stmts:
                        stmts.append(text)
            # base classes first; otherwise keep first-seen order
            order = sorted(classes, key=lambda n: classes[n][3])
            placed, out_cls = set(), []

            def place(n, stack=()):
                if n in placed or n in stack:
                    return
                for b in classes[n][1]:
                    if b in classes:
                        place(b, stack + (n,))
                placed.add(n)
                out_cls.append(classes[n][2])
            for n in order:
                place(n)
            parts = ["\n".join(imports)] + stmts + list(defs.values()) + out_cls + mains
            return "\n\n\n".join(p for p in parts if p.strip()) + "\n"
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
            fragments.setdefault(path, []).append((set(a.classes), code))
    files = {p: merge_fragments(p, [c for _, c in frs], [o for o, _ in frs])
             for p, frs in fragments.items()}
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
