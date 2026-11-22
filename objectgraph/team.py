"""Step 4: turn a partition of the duty graph into agent task assignments.

Each agent owns whole duties (and therefore the classes they belong to). For
every pair of agents we record the cut weight between them and which agent
depends on which (A depends on B if a relation or signature of A's classes
points at B's classes). Agents then run in dependency order, so an agent
receives the code of the agents it depends on (these hand-overs are the
"messages" we count).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

import numpy as np

from .graph import DutyGraph
from .uml import ClassDiagram, method_name


@dataclass
class AgentSpec:
    agent_id: str
    duties: list[str]
    classes: list[str]
    depends_on: list[str] = field(default_factory=list)
    cut_to: dict = field(default_factory=dict)        # other agent -> cut weight


@dataclass
class TeamSpec:
    method: str
    k: int
    agents: list[AgentSpec]
    order: list[str]
    cut: float

    def to_dict(self) -> dict:
        d = asdict(self)
        d["agents"] = [asdict(a) for a in self.agents]
        return d


def _class_deps(diagram: ClassDiagram, classes: list[str]) -> dict[str, set[str]]:
    """Directed class dependencies: X -> Y if X uses/inherits/composes Y, or a
    method signature of X names Y."""
    deps = {c: set() for c in classes}
    for r in diagram.relations:
        a, b = r.a, r.b
        if a not in deps or b not in deps or a == b:
            continue
        # for these arrows b depends on a (b inherits a, or b is the whole that contains a)
        if r.arrow in ("<|--", "<|..", "--*", "--o", "<--", "<.."):
            a, b = b, a
        deps[a].add(b)
    for c in classes:
        for raw in diagram.classes[c].methods:
            text = raw.replace(method_name(raw), " ")
            for other in classes:
                if other != c and other in text:
                    deps[c].add(other)
    return deps


def build_team(method: str, labels: np.ndarray, graph: DutyGraph, diagram: ClassDiagram) -> TeamSpec:
    groups = sorted(set(labels.tolist()), key=lambda g: int(np.flatnonzero(labels == g)[0]))
    names = {g: f"agent_{i + 1}" for i, g in enumerate(groups)}
    agents = []
    for g in groups:
        idx = np.flatnonzero(labels == g)
        duties = [graph.duties[i] for i in idx]
        classes = sorted({graph.owner[i] for i in idx})
        agents.append(AgentSpec(names[g], duties, classes))
    by_name = {a.agent_id: a for a in agents}
    owner_agent = {}
    for a in agents:
        for c in a.classes:
            owner_agent.setdefault(c, a.agent_id)
    W = graph.W
    for i, gi in enumerate(groups):
        for gj in groups[i + 1:]:
            w = float(W[np.ix_(labels == gi, labels == gj)].sum())
            if w > 0:
                by_name[names[gi]].cut_to[names[gj]] = round(w, 4)
                by_name[names[gj]].cut_to[names[gi]] = round(w, 4)
    cdeps = _class_deps(diagram, sorted(set(graph.owner)))
    for a in agents:
        dep = set()
        for c in a.classes:
            for d in cdeps.get(c, ()):
                o = owner_agent.get(d)
                if o and o != a.agent_id:
                    dep.add(o)
        a.depends_on = sorted(dep)
    # dependency order (Kahn); cycles are broken by agent number
    remaining = {a.agent_id: set(a.depends_on) for a in agents}
    order = []
    while remaining:
        ready = sorted([n for n, d in remaining.items() if not d], key=lambda s: int(s.split("_")[1]))
        if not ready:
            ready = [min(remaining, key=lambda s: int(s.split("_")[1]))]
        n = ready[0]
        order.append(n)
        remaining.pop(n)
        for d in remaining.values():
            d.discard(n)
    diff = labels[:, None] != labels[None, :]
    return TeamSpec(method, len(groups), agents, order, round(float(W[diff].sum() / 2), 4))
