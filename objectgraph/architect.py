"""G8: an LLM Architect sizes the team and assigns file/class ownership (CodeTeam-style baseline).

CodeTeam (Wang et al., 2026) lets Architect agents propose a project-specific plan that fixes the
number of Developer agents and gives each file an owner, and a CTO agent picks a plan. This is a
simplified re-implementation for a controlled comparison: one Architect call (temperature 0) sees
the same requirements, design and file tree as the developers, proposes the number of developers
and assigns every design unit (a class, or the module-level code of a file) to one developer. The
developers, prompts, merge and scoring are then identical to every other condition, so only the
team-forming step differs. There is no CTO step, because at temperature 0 repeated Architect calls
on the same input give the same plan.
"""
from __future__ import annotations

import json
import re

import numpy as np

ARCH_SYSTEM = ("You are the software Architect of a team of LLM developer agents. You decide how many "
               "developers to use and which design units each one owns. Reply with JSON only.")

ARCH_TMPL = """# Requirements
{prd}

# Design (class diagram, grouped by file)
{design}

# File layout
{arch}

# Your task
Decide how many developer agents should implement this project (from 1 up to {max_k}) and assign every
design unit below to exactly one developer. A unit is a class, or a `mod_...` unit (the module-level
code of one file). Group units so that each developer can work as independently as possible, and use
more developers only where that helps.

Units:
{units}

Reply with JSON only, in this form:
{{"developers": [{{"id": 1, "units": ["UnitA", "UnitB"]}}, {{"id": 2, "units": ["UnitC"]}}]}}
"""


def _parse(text: str) -> list[list[str]]:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    devs = data.get("developers", []) if isinstance(data, dict) else []
    return [[str(u).strip("` ") for u in d.get("units", [])] for d in devs if isinstance(d, dict)]


def architect_labels(llm, prd: str, design_text: str, arch: str, graph, run_id: int = 0) -> tuple[np.ndarray, dict]:
    """One label per duty. Units the Architect omits or misnames go to developer 1 (recorded)."""
    units = sorted(set(graph.owner))
    user = ARCH_TMPL.format(prd=prd, design=design_text, arch=arch, max_k=len(units),
                            units="\n".join(f"- {u}" for u in units))
    reply = llm.call(ARCH_SYSTEM, user, tag="architect", run_id=run_id)
    plan = _parse(reply)
    owner_of: dict[str, int] = {}
    unknown = []
    for i, us in enumerate(plan):
        for u in us:
            if u in units and u not in owner_of:
                owner_of[u] = i
            elif u not in units:
                unknown.append(u)
    missing = [u for u in units if u not in owner_of]
    for u in missing:
        owner_of[u] = 0
    lab = np.array([owner_of[o] for o in graph.owner])
    lab = np.unique(lab, return_inverse=True)[1]
    info = {"developers_proposed": len(plan), "k": int(len(set(lab.tolist()))), "parsed": bool(plan),
            "units_missing": missing, "units_unknown": unknown, "reply": reply}
    return lab, info
