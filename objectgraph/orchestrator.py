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
{seq}
# Your assignment ({agent_id} of {k})
Classes you own: {classes}
Duties you must implement (ID = Class.method):
{duties}
{others}
{received}
Write your code now."""

# the closing fence must stand on its own line, so ``` inside a docstring does not end the block
_BLOCK = re.compile(r"###\s*FILE:\s*`?(?P<path>[^\s`]+)`?\s*\n```[^\n]*\n(?P<code>.*?)^```[ \t]*$", re.S | re.M)


@dataclass
class RunResult:
    files: dict[str, str]
    agent_outputs: dict[str, str]
    messages: list[dict] = field(default_factory=list)
    stopped_by_budget: bool = False
    traceability: float = 0.0


_BARE_DUTY = re.compile(r"^(?P<ind>[ \t]*)(?P<tag>duty:\s*[\w.<>]+)[ \t]*$", re.M)


def fix_duty_markers(path: str, code: str) -> str:
    """Turn bare ``duty: Class.method`` lines into comments.

    The prompt asks for a *comment*; models sometimes drop the comment sign, and
    in Python ``duty: Renko.get_ohlc_data`` is then an annotated statement that
    raises NameError at import time. Only lines consisting of nothing but the
    marker are touched, identically for every condition.
    """
    sign = "#" if path.endswith((".py", ".sh", ".rb")) else "//"
    return _BARE_DUTY.sub(lambda m: f"{m.group('ind')}{sign} {m.group('tag')}", code)


_THINK = re.compile(r"<think>.*?</think>", re.S)


def parse_blocks(text: str) -> list[tuple[str, str]]:
    text = _THINK.sub("", text)      # reasoning models may echo their thinking
    return [(m.group("path").strip("`"), fix_duty_markers(m.group("path").strip("`"), m.group("code")))
            for m in _BLOCK.finditer(text)]


def _seg(lines, node):
    """Source of a node, including decorators and comment lines directly above."""
    start = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno]) - 1
    while start > 0 and lines[start - 1].lstrip().startswith("#"):
        start -= 1
    return "\n".join(lines[start:node.end_lineno]), start


def _py_units(code: str):
    """Split Python source into top-level units: (kind, name, payload, text)."""
    import ast
    tree = ast.parse(code)
    lines = code.splitlines()
    units = []
    for node in tree.body:
        text, start = _seg(lines, node)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            units.append(("import", None, None, text))
        elif isinstance(node, ast.ClassDef):
            bases = [b.id if isinstance(b, ast.Name) else getattr(b, "attr", "") for b in node.bases]
            _, body_start = _seg(lines, node.body[0])
            header = "\n".join(lines[start:max(body_start, node.lineno)])
            members, methods = [], []
            for el in node.body:
                t, _ = _seg(lines, el)
                if isinstance(el, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if MERGE_V2 and methods and methods[-1][0] == el.name:
                        # property getter + setter (or overloads) travel together
                        methods[-1] = (el.name, methods[-1][1] + "\n\n" + t)
                    else:
                        methods.append((el.name, t))
                else:
                    members.append(t)
            units.append(("class", node.name, {"bases": bases, "header": header,
                                                "members": members, "methods": methods}, text))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            units.append(("def", node.name, None, text))
        elif (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
              and getattr(node.test.left, "id", "") == "__name__"):
            units.append(("main", None, None, text))
        else:
            units.append(("stmt", None, None, text))
    return units


def _indent(text: str) -> str:
    import textwrap
    if MERGE_V2 and text[:1] in (" ", "\t"):
        return text            # already a class-body member; re-indenting would change string literals
    return textwrap.indent(textwrap.dedent(text), "    ")


def _load_names(text: str) -> tuple[set[str], set[str]]:
    """(names a top-level unit defines, names it needs when the module is imported).
    Function bodies run later, so only decorators, defaults and annotations count."""
    import ast
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set(), set()
    defined, used = set(), set()

    def visit(node, top=True):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if top:
                defined.add(node.name)
            a = node.args
            anns = [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]
                    if x is not None and x.annotation is not None]
            for x in node.decorator_list + a.defaults + [d for d in a.kw_defaults if d] + anns \
                    + ([node.returns] if node.returns else []):
                visit(x, False)
            return
        if isinstance(node, ast.Lambda):
            return
        if isinstance(node, ast.ClassDef):
            if top:
                defined.add(node.name)
            for x in node.bases + node.decorator_list + [k.value for k in node.keywords]:
                visit(x, False)
            for x in node.body:
                visit(x, False)
            return
        if isinstance(node, ast.Name):
            (defined if isinstance(node.ctx, ast.Store) and top else used).add(node.id)
            return
        for child in ast.iter_child_nodes(node):
            visit(child, top and isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Tuple, ast.List)))
    for n in tree.body:
        visit(n, True)
    return defined, used - defined


def _order_by_need(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Stable topological order of (key, text): a unit comes after the units
    defining names it needs at import time; cycles keep source order."""
    info = [_load_names(t) for _, t in items]
    owner = {}
    for i, (d, _) in enumerate(info):
        for n in d:
            owner.setdefault(n, i)
    deps = [{owner[n] for n in u if n in owner and owner[n] != i} for i, (_, u) in enumerate(info)]
    out, done, visiting = [], set(), set()

    def go(i):
        if i in done or i in visiting:
            return
        visiting.add(i)
        for j in sorted(deps[i]):
            go(j)
        visiting.discard(i)
        done.add(i)
        out.append(items[i])
    for i in range(len(items)):
        go(i)
    return out


def _is_docstring(t: str) -> bool:
    s = t.lstrip()
    return s.startswith(('"', "'", 'r"', "r'"))


def _merge_class(name: str, versions: list) -> str:
    """versions: list of (duties_of_author, info, text, index). Rebuild one class
    whose every method comes from the agent assigned that duty."""
    def owned(v, m):
        return f"{name}.{m}" in v[0]

    def n_owned(v):
        return sum(owned(v, m) for m, _ in v[1]["methods"])
    skel = max(versions, key=lambda v: (n_owned(v), any(d.startswith(name + ".") for d in v[0]),
                                        len(v[2]), -v[3]))
    chosen, order = {}, []
    for m, t in skel[1]["methods"]:
        chosen[m] = (owned(skel, m), t)
        order.append(m)
    for v in versions:
        if v is skel:
            continue
        for m, t in v[1]["methods"]:
            if m not in chosen:
                chosen[m] = (owned(v, m), t)
                order.append(m)
            elif owned(v, m) and not chosen[m][0]:
                chosen[m] = (True, t)
    members = list(skel[1]["members"])
    for v in versions:
        for t in v[1]["members"]:
            if t not in members and not _is_docstring(t):
                members.append(t)
    body = [_indent(t) for t in members] + [_indent(chosen[m][1]) for m in order]
    return skel[1]["header"].rstrip() + "\n" + ("\n\n".join(body) if body else "    pass")


# Merge v2 (Experiment 2, RealBench): units keep source order and are then sorted
# so that every name used at import time is defined first; class members keep their
# own indentation. The pilot keeps merge v1 so its cached runs reproduce exactly
# (prereg/deviations.md).
MERGE_V2 = False


def merge_fragments(path: str, fragments: list[str], owners: list[set[str]] | None = None) -> str:
    """Merge several agents' fragments of one file.

    Python files are merged by syntax: imports first (de-duplicated), then other
    module-level code, then classes with base classes before the classes that
    inherit from them, then any ``if __name__ == "__main__"`` block. When several
    fragments define the same class (a class split across agents, or a stub of
    another agent's class), the class is rebuilt method by method: each method is
    taken from the agent assigned that duty (``owners[i]`` = duty IDs
    "Class.method" assigned to the author of ``fragments[i]``); methods nobody was
    assigned come from the most complete version. The same rule applies to every
    condition. If a fragment does not parse, fall back to concatenation.
    """
    if len(fragments) == 1:
        return fragments[0]
    if path.endswith(".py"):
        try:
            per = [_py_units(f) for f in fragments]
        except SyntaxError:
            per = None
        if per is not None:
            seq: list[tuple] = []          # unit keys in source order across fragments
            imports, seen_imp, stmts, defs, mains = [], set(), [], {}, []
            def_owned: dict[str, bool] = {}
            classes, first_seen = {}, {}
            for i, units in enumerate(per):
                own = owners[i] if owners and i < len(owners) else set()
                prev = -1
                for kind, name, info, text in units:
                    if kind != "import":
                        key = (kind, name if kind in ("class", "def") else text)
                        if key in seq:
                            prev = seq.index(key)
                        else:
                            prev += 1
                            seq.insert(prev, key)
                    if kind == "import":
                        for line in text.splitlines():
                            if line.strip() and line.strip() not in seen_imp:
                                seen_imp.add(line.strip())
                                imports.append(line)
                    elif kind == "class":
                        classes.setdefault(name, []).append((own, info, text, i))
                        first_seen.setdefault(name, len(first_seen))
                    elif kind == "def":
                        # a top-level function comes from the agent that owns it (RealBench
                        # module-function duties are "mod_<file>.<name>"); otherwise the longest
                        mine = any(d.startswith("mod_") and d.endswith("." + name) for d in own)
                        cur = def_owned.get(name, False)
                        if name not in defs or (mine and not cur) or (mine == cur and len(text) > len(defs[name])):
                            defs[name] = text
                            def_owned[name] = mine
                    elif kind == "main":
                        if text not in mains:
                            mains.append(text)
                    elif text not in stmts:
                        stmts.append(text)
            built = {n: (vs[0][2] if len(vs) == 1 else _merge_class(n, vs), vs[0][1]["bases"])
                     for n, vs in classes.items()}
            placed, out_cls = set(), []

            def place(n, stack=()):
                if n in placed or n in stack:
                    return
                for bse in built[n][1]:
                    if bse in built:
                        place(bse, stack + (n,))
                placed.add(n)
                out_cls.append(built[n][0])
            if not MERGE_V2:
                for n in sorted(built, key=first_seen.get):
                    place(n)
                parts = ["\n".join(imports)] + stmts + list(defs.values()) + out_cls + mains
            else:
                # keep the units in source order (module code may use a class defined
                # above it), still placing every base class before its subclasses
                items = []
                for kind, key in seq:
                    if kind == "class":
                        items.append((key, built[key][0]))
                    elif kind == "def":
                        items.append((key, defs[key]))
                    elif kind == "stmt":
                        items.append((key, key))
                parts = ["\n".join(imports)] + [t for _, t in _order_by_need(items)] + mains
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
             run_id: int = 0, seq: str = "") -> RunResult:
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
        seq_block = f"\n# Sequence diagram (how the classes interact)\n{seq}\n" if seq else ""
        user = USER_TMPL.format(prd=prd, design=design_text, arch=arch, seq=seq_block,
                                agent_id=aid, k=team.k,
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
            fragments.setdefault(path, []).append((set(a.duties), code))
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
