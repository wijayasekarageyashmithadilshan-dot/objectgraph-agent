"""Turn one RealBench project into the inputs the agent pipeline expects.

Agents see only design material that RealBench distributes: the project's
README (when RealBench ships one in ``proj_clean``), the class diagram
(``uml_output/<project>_uml.json``, with its natural-language descriptions)
and the file tree (``uml_output/tree.txt``). They never see source code or tests.
"""
from __future__ import annotations

import json
from pathlib import Path

from .realbench import load_realbench, parse_tree, resolve_paths, _ident


def _sig(fn: dict) -> str:
    ps = []
    for p in fn.get("parameters") or []:
        s = p.get("name", "")
        if p.get("type") and p["type"] != "Any":
            s += f": {p['type']}"
        if p.get("defaultValue") is not None:
            s += f" = {p['defaultValue']}"
        ps.append(s)
    ret = f" -> {fn['returnType']}" if fn.get("returnType") else ""
    return f"{fn['name']}({', '.join(ps)}){ret}"


def _desc(x: dict) -> str:
    d = (x.get("description") or "").strip().replace("\n", " ")
    return f"  # {d}" if d else ""


def render_design(uml_json: Path) -> str:
    """Readable class diagram grouped by file, with the unit names used as owners."""
    data = json.loads(Path(uml_json).read_text(encoding="utf-8"))
    modules = data.get("modules", [])
    tree = Path(uml_json).parent / "tree.txt"
    paths = resolve_paths([m["name"] for m in modules],
                          parse_tree(tree.read_text(encoding="utf-8")) if tree.exists() else [])
    counts: dict[str, int] = {}
    for m in modules:
        for c in m.get("classes", []):
            counts[c["name"]] = counts.get(c["name"], 0) + 1
    out = ["Units: every class is a unit named after the class; the module-level functions of a file "
           "form one unit named `mod_<file path>` and are written as top-level functions of that file "
           "(not inside a class). Write every unit in the file shown.", ""]
    for m, path in zip(modules, paths):
        out.append(f"## File `{path}`")
        for v in m.get("variables") or []:
            out.append(f"- module variable `{v['name']}`" + (f": {v['type']}" if v.get("type") else "") + _desc(v))
        fns = m.get("functions") or []
        unit = "mod_" + _ident(path.removesuffix(".py"))
        if fns:
            out.append(f"- unit `{unit}` (top-level functions):")
            for f in fns:
                out.append(f"    - `{_sig(f)}`{_desc(f)}")
        elif m.get("variables"):
            out.append(f"- unit `{unit}`: the module variables above")
        elif not m.get("classes"):
            out.append(f"- unit `{unit}`: module-level code of this file (e.g. package imports and exports)")
        for c in m.get("classes", []):
            name = c["name"] if counts[c["name"]] == 1 else f"{_ident(path.removesuffix('.py'))}_{c['name']}"
            label = f"`{c['name']}`" + (f" (unit `{name}`)" if name != c["name"] else "")
            out.append(f"- class {label}{_desc(c)}")
            for a in c.get("attributes") or []:
                out.append(f"    - attribute `{a['name']}`" + (f": {a['type']}" if a.get("type") else ""))
            for f in c.get("methods") or []:
                out.append(f"    - method `{_sig(f)}`{_desc(f)}")
            deps = sorted({r["target"] for r in c.get("relationships") or [] if r.get("target") in counts})
            if deps:
                out.append(f"    - uses: {', '.join(deps)}")
        out.append("")
    return "\n".join(out)


_JUNK = ("__pycache__", ".pytest_cache", ".cursor", ".git", ".idea", ".vscode", "venv", ".venv", ".egg-info")


def clean_tree(text: str) -> str:
    """Drop cache and tool folders (and everything under them) from tree.txt."""
    out, skip_depth = [], None
    for line in text.splitlines():
        stripped = line.lstrip("\u2502 ").lstrip("\u251c\u2514\u2500 ")
        depth = (len(line) - len(line.lstrip("\u2502 \u251c\u2514\u2500"))) // 4
        if skip_depth is not None and depth > skip_depth:
            continue
        skip_depth = None
        if any(j in stripped for j in _JUNK):
            skip_depth = depth
            continue
        out.append(line)
    return "\n".join(out)


def load_task(project_dir: Path) -> dict:
    project_dir = Path(project_dir)
    uml = next((project_dir / "uml_output").glob("*_uml.json"))
    diagram, stats = load_realbench(uml, uml.parent / "dag.json", include_functions=True)
    readme = next(iter(sorted((project_dir / "proj_clean").glob("README*"))), None)
    prd = readme.read_text(encoding="utf-8", errors="ignore") if readme else \
        "(RealBench ships no README for this project; the requirements are the descriptions in the domain model.)"
    tree = (uml.parent / "tree.txt").read_text(encoding="utf-8") if (uml.parent / "tree.txt").exists() else ""
    tree = clean_tree(tree)
    arch = ("File layout (paths are relative to the project root; the first line is the root folder):\n"
            + tree + "\nWrite each file at exactly the path shown, e.g. `src/pkg/module.py`.")
    text = render_design(uml)
    return {"dir": project_dir, "prd": prd, "arch": arch, "seq": "", "gold_text": text,
            "design": {"text": text, "diagram": diagram, "log": [], "cmp": None}, "mapping": stats}
