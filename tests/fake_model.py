"""A fake model for testing the pipeline without an API key.

* Design extraction: returns the gold class diagram.
* Agents: return one FILE block with empty stubs for the classes they own.
The code is deliberately not a real implementation, so scores are ~0.
"""
import re


def fake_reply(system: str, user: str, gold_text: str) -> str:
    if "domain model as a Mermaid classDiagram" in user:
        return gold_text
    owned = re.search(r"Classes you own: (.*)", user).group(1).split(", ")
    duties = re.findall(r"^- (\S+\.\S+)$", user, flags=re.M)
    path = "stocktrends/indicators.py"
    m = re.search(r"`([\w/]+\.py)`:", user)
    if m:
        path = m.group(1) if "/" in m.group(1) else f"stocktrends/{m.group(1)}"
    lines = ["import pandas as pd", ""]
    for c in owned:
        lines.append(f"class {c}:")
        body = [d.split(".", 1)[1] for d in duties if d.startswith(c + ".") and not d.endswith("<state>")]
        if not body:
            lines.append("    pass")
        for meth in body:
            lines += [f"    # duty: {c}.{meth}", f"    def {meth}(self, *args, **kwargs):", "        return None"]
        lines.append("")
    return f"### FILE: {path}\n```python\n" + "\n".join(lines) + "\n```\n"


def fake_reply_realbench(system: str, user: str, project_dir) -> str:
    """Harness check for RealBench: each agent answers with the *reference* code
    of exactly the duties it owns (whole files cut down to its classes/methods and
    top-level functions, plus imports and module statements). If splitting,
    merging and scoring are correct, every team scores like the reference."""
    import ast
    import json
    from pathlib import Path
    from objectgraph.realbench import parse_tree, resolve_paths, _ident

    project_dir = Path(project_dir)
    duties = set(re.findall(r"^- (\S+\.\S+)$", user, flags=re.M))
    uml = next((project_dir / "uml_output").glob("*_uml.json"))
    mods = json.loads(uml.read_text())["modules"]
    tree = uml.parent / "tree.txt"
    paths = resolve_paths([m["name"] for m in mods], parse_tree(tree.read_text()) if tree.exists() else [])
    counts = {}
    for m in mods:
        for c in m.get("classes", []):
            counts[c["name"]] = counts.get(c["name"], 0) + 1
    blocks = []
    for m, path in zip(mods, paths):
        src = project_dir / "proj_clean" / path
        if not src.exists():
            continue
        code = src.read_text(encoding="utf-8", errors="ignore")
        try:
            tree_ = ast.parse(code)
        except SyntaxError:
            continue
        lines = code.splitlines()
        mod_unit = "mod_" + _ident(path.removesuffix(".py"))
        keep, owns_any = [], any(d.startswith(mod_unit + ".") for d in duties)
        for node in tree_.body:
            start = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno]) - 1
            seg = "\n".join(lines[start:node.end_lineno])
            if isinstance(node, ast.ClassDef):
                unit = node.name if counts.get(node.name, 1) == 1 else f"{_ident(path.removesuffix('.py'))}_{node.name}"
                mine = {d.split(".", 1)[1] for d in duties if d.startswith(unit + ".")}
                if not mine:
                    continue
                declared = {f["name"] for c in m.get("classes", []) if c["name"] == node.name
                            for f in c.get("methods") or []}
                owns_any = True
                drop = []
                for el in node.body:
                    if isinstance(el, (ast.FunctionDef, ast.AsyncFunctionDef)) and el.name not in mine \
                            and el.name in declared:
                        s0 = min([d.lineno for d in el.decorator_list] + [el.lineno]) - 1
                        drop.append((s0, el.end_lineno))
                cl = lines[start:node.end_lineno]
                for s0, e0 in sorted(drop, reverse=True):
                    del cl[s0 - start:e0 - start]
                body_left = [ln for ln in cl[1:] if ln.strip()]
                if not body_left:
                    cl.append("    pass")
                keep.append("\n".join(cl))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                declared_f = {f["name"] for f in m.get("functions") or []}
                if f"{mod_unit}.{node.name}" in duties or (node.name not in declared_f and owns_any):
                    owns_any = True
                    keep.append(seg)
            else:
                keep.append(seg)          # imports, constants, __main__ block
        if owns_any:
            blocks.append(f"### FILE: {path}\n```python\n" + "\n\n".join(keep) + "\n```\n")
    return "\n".join(blocks) or "### FILE: unused.py\n```python\npass\n```\n"
