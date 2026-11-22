"""Step 1: build the domain model (a Mermaid class diagram) from the PRD.

Two sources:
* "gold"      - DevBench's own UML_class.md (upper bound; written with the answer code)
* "extracted" - Claude reads only the PRD and writes the class diagram (H4)

The extracted diagram must parse with our parser and contain at least one
class with a method; otherwise the parser's complaint is sent back and the
model gets up to `repairs` more attempts (each attempt is logged).
"""
from __future__ import annotations

import re

from .uml import parse_class_diagram, ClassDiagram

SYSTEM = (
    "You are a senior software designer. From a product requirements document you "
    "write an object-oriented domain model as a Mermaid classDiagram. Use one class "
    "per real concept, list each class's methods with parameters, and add relations "
    "(--> uses, --|> inherits, *-- composition, o-- aggregation). Put functions that "
    "belong to no class in a class named Global_functions. Output only one fenced "
    "```mermaid block, nothing else.")

USER_TMPL = (
    "Product requirements document:\n<<<PRD\n{prd}\nPRD>>>\n\n"
    "Write the domain model as a Mermaid classDiagram.{feedback}")


def validate(diagram: ClassDiagram) -> list[str]:
    problems = []
    with_methods = [c for c, k in diagram.classes.items() if k.methods]
    if not diagram.classes:
        problems.append("no classes were found")
    elif not with_methods:
        problems.append("no class has any method; list methods with parentheses, e.g. +run()")
    for r in diagram.relations:
        for end in (r.a, r.b):
            if end not in diagram.classes:
                problems.append(f"relation mentions undeclared class {end}")
    return problems


def extract_design(llm, prd: str, run_id: int = 0, repairs: int = 2) -> tuple[str, ClassDiagram, list[dict]]:
    log, feedback = [], ""
    text, diagram = "", None
    for attempt in range(repairs + 1):
        text = llm.call(SYSTEM, USER_TMPL.format(prd=prd, feedback=feedback),
                        tag=f"extract_attempt_{attempt}", run_id=run_id)
        diagram = parse_class_diagram(text)
        problems = validate(diagram)
        log.append({"attempt": attempt, "classes": len(diagram.classes),
                    "relations": len(diagram.relations), "problems": problems})
        if not problems:
            break
        feedback = ("\n\nYour previous diagram had these problems; fix them and output the "
                    "full corrected diagram:\n- " + "\n- ".join(problems) +
                    "\n\nPrevious diagram:\n" + text)
    return text, diagram, log


def compare_to_gold(extracted: ClassDiagram, gold: ClassDiagram) -> dict:
    """Class-name precision/recall (case- and underscore-insensitive)."""
    norm = lambda s: re.sub(r"[_\s]", "", s).lower()
    e = {norm(c) for c, k in extracted.classes.items() if k.methods or k.attributes}
    g = {norm(c) for c, k in gold.classes.items() if k.methods or k.attributes}
    tp = len(e & g)
    p = tp / len(e) if e else 0.0
    r = tp / len(g) if g else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3),
            "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0,
            "matched": sorted(e & g), "extra": sorted(e - g), "missing": sorted(g - e)}
