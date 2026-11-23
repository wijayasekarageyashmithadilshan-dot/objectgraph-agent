"""Read RealBench designs (``<project>_uml.json`` + ``dag.json``) into the same
``ClassDiagram`` that the Mermaid parser produces, so the duty graph, the
criterion and the baselines run unchanged.

RealBench (arXiv 2604.22659) ships, per project, a JSON class diagram that
was generated with SciTools Understand:

    {"modules": [{"name": "pkg/file.py", "functions": [...],
                  "variables": [...], "classes": [{"name", "attributes",
                  "methods", "relationships", "stereotypes"}]}]}

and a file-level dependency DAG (``dag.json``: nodes = files, edges = imports).

Mapping (documented in docs/realbench_mapping.md):

* every class becomes a ``UMLClass``; its methods keep their parameter and
  return types, so signature references to other declared classes are found
  by ``build_duty_graph`` exactly as for DevBench;
* with ``include_functions=True`` the module-level functions of each file
  form one pseudo-class named after the file (``mod_<path>``), because an
  agent that owns those functions writes that file;
* class ``relationships`` (all of type ``dependency`` in RealBench) whose
  target is a declared class become weak relations (``..>``);
* each ``dag.json`` edge (file A imports file B) becomes a weak relation
  between every unit declared in A and every unit declared in B.

RealBench diagrams contain no inheritance or composition, so the ``strong``
weight is never used; this is a property of the data, not of the method.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .uml import ClassDiagram, Relation, UMLClass

WEAK = "..>"


def _ident(text: str) -> str:
    return re.sub(r"\W", "_", text)


def _member(fn: dict) -> str:
    params = []
    for p in fn.get("parameters") or []:
        if p.get("name") in ("self", "cls"):
            continue
        t = p.get("type")
        params.append(f"{p.get('name')}: {t}" if t and t != "Any" else str(p.get("name")))
    ret = fn.get("returnType") or ""
    return f"+{fn['name']}({', '.join(params)}) {ret}".rstrip()


def _attr(v: dict) -> str:
    t = v.get("type")
    return f"+{v['name']}: {t}" if t else f"+{v['name']}"


def load_realbench(uml_json: Path, dag_json: Path | None = None,
                   include_functions: bool = True) -> tuple[ClassDiagram, dict]:
    """Return the diagram and a small dict of mapping statistics."""
    data = json.loads(Path(uml_json).read_text(encoding="utf-8"))
    modules = data.get("modules", [])

    # class names that occur in more than one file are qualified with the file
    counts: dict[str, int] = {}
    for m in modules:
        for c in m.get("classes", []):
            counts[c["name"]] = counts.get(c["name"], 0) + 1

    classes: dict[str, UMLClass] = {}
    units_by_file: dict[str, list[str]] = {}
    local_name: dict[tuple[str, str], str] = {}     # (file, class) -> unit name
    global_name: dict[str, str] = {}                 # unique class -> unit name
    stats = {"files": len(modules), "classes": 0, "module_functions": 0,
             "duplicate_class_names": sum(1 for v in counts.values() if v > 1),
             "class_dependencies_kept": 0, "class_dependencies_external": 0,
             "class_dependencies_ambiguous": 0, "file_edges": 0}

    for m in modules:
        f = m["name"]
        units_by_file.setdefault(f, [])
        for c in m.get("classes", []):
            name = c["name"] if counts[c["name"]] == 1 else f"{_ident(Path(f).stem)}_{c['name']}"
            if name in classes:            # same class declared twice in one file
                continue
            k = UMLClass(name,
                         methods=[_member(x) for x in c.get("methods") or []],
                         attributes=[_attr(a) for a in c.get("attributes") or []])
            if not k.methods and not k.attributes:
                k.stereotypes.append("declared")   # keep member-less classes as one state duty
            classes[name] = k
            units_by_file[f].append(name)
            local_name[(f, c["name"])] = name
            if counts[c["name"]] == 1:
                global_name[c["name"]] = name
            stats["classes"] += 1
        fns = m.get("functions") or []
        if include_functions and fns:
            name = "mod_" + _ident(f.removesuffix(".py"))
            classes[name] = UMLClass(name, methods=[_member(x) for x in fns],
                                     attributes=[_attr(v) for v in m.get("variables") or []])
            units_by_file[f].append(name)
            stats["module_functions"] += len(fns)

    relations: list[Relation] = []
    for m in modules:
        f = m["name"]
        for c in m.get("classes", []):
            src = local_name.get((f, c["name"]))
            if src is None:
                continue
            for r in c.get("relationships") or []:
                t = r.get("target")
                if (f, t) in local_name:
                    tgt = local_name[(f, t)]
                elif t in global_name:
                    tgt = global_name[t]
                elif counts.get(t, 0) > 1:
                    stats["class_dependencies_ambiguous"] += 1
                    continue
                else:
                    stats["class_dependencies_external"] += 1
                    continue
                if tgt != src:
                    relations.append(Relation(src, tgt, WEAK, "dependency"))
                    stats["class_dependencies_kept"] += 1

    if dag_json is not None and Path(dag_json).exists():
        dag = json.loads(Path(dag_json).read_text(encoding="utf-8"))
        for e in dag.get("edges", []):
            a, b = units_by_file.get(e["source"], []), units_by_file.get(e["target"], [])
            if a and b:
                stats["file_edges"] += 1
            for x in a:
                for y in b:
                    if x != y:
                        relations.append(Relation(x, y, WEAK, "import"))
    return ClassDiagram(classes, relations), stats
