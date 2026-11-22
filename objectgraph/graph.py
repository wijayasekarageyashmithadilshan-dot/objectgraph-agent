"""Build the weighted duty graph from a parsed class diagram.

Nodes ("duties") are the methods of each declared class; a class without
methods contributes one state duty ``Class.<state>``. Edge weights add up
from four sources, each with its own weight (see ``Weights``):

* ``intra``  - two duties of the same class (they share the class's state);
* ``strong`` - every duty pair across a composition/aggregation/inheritance/
               realisation relation;
* ``weak``   - every duty pair across an association/dependency ("uses");
* ``sig``    - a method whose signature names another declared class, linked
               to every duty of that class.

Relations to classes that are only mentioned (library types such as ``File``)
are ignored, because no agent would implement them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

import numpy as np

from .uml import ClassDiagram


@dataclass(frozen=True)
class Weights:
    intra: float = 1.0
    strong: float = 0.5
    weak: float = 0.25
    sig: float = 0.5

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class DutyGraph:
    duties: list[str]          # "Class.method"
    owner: list[str]           # class of each duty
    W: np.ndarray              # symmetric, zero diagonal, normalised to max 1

    @property
    def n(self) -> int:
        return len(self.duties)

    def class_partition(self) -> np.ndarray:
        classes = sorted(set(self.owner))
        idx = {c: i for i, c in enumerate(classes)}
        return np.array([idx[c] for c in self.owner])


def _declared(diagram: ClassDiagram) -> list[str]:
    """Classes that have members or appear as a relation endpoint *and* were
    declared with a body. Undeclared, member-less names are library types."""
    return sorted(c for c, k in diagram.classes.items() if k.methods or k.attributes or k.stereotypes)


def build_duty_graph(diagram: ClassDiagram, w: Weights = Weights()) -> DutyGraph:
    classes = _declared(diagram)
    duties, owner = [], []
    for c in classes:
        names = diagram.classes[c].method_names() or ["<state>"]
        for m in names:
            duties.append(f"{c}.{m}")
            owner.append(c)
    n = len(duties)
    W = np.zeros((n, n))
    by_class = {c: [i for i, o in enumerate(owner) if o == c] for c in classes}

    def add_block(A: list[int], B: list[int], val: float) -> None:
        if val == 0:
            return
        for i in A:
            for j in B:
                if i != j:
                    W[i, j] += val
                    W[j, i] += val

    for c, ids in by_class.items():
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                W[ids[x], ids[y]] += w.intra
                W[ids[y], ids[x]] += w.intra

    seen_pairs = set()
    for r in diagram.relations:
        if r.a not in by_class or r.b not in by_class or r.a == r.b:
            continue
        key = (frozenset((r.a, r.b)), r.strong)
        if key in seen_pairs:          # duplicate declarations count once
            continue
        seen_pairs.add(key)
        add_block(by_class[r.a], by_class[r.b], w.strong if r.strong else w.weak)

    # signature references: a method that names another declared class
    for c in classes:
        k = diagram.classes[c]
        for raw in k.methods:
            from .uml import method_name
            mname = method_name(raw)
            i = duties.index(f"{c}.{mname}") if f"{c}.{mname}" in duties else None
            if i is None:
                continue
            sig = raw.split("(", 1)
            text = (sig[1] if len(sig) > 1 else "") + " " + sig[0].replace(mname, " ")
            for other in classes:
                if other != c and re.search(rf"\b{re.escape(other)}\b", text):
                    add_block([i], by_class[other], w.sig)

    mx = W.max()
    if mx > 0:
        W = W / mx
    return DutyGraph(duties, owner, W)


def build_class_graph(diagram: ClassDiagram, w: Weights = Weights()) -> DutyGraph:
    """Class-level graph: one node per declared class (used as a coarser
    granularity check). Edge weight = strong/weak relation weight plus ``sig``
    for each signature reference."""
    classes = _declared(diagram)
    idx = {c: i for i, c in enumerate(classes)}
    n = len(classes)
    W = np.zeros((n, n))
    seen = set()
    for r in diagram.relations:
        if r.a in idx and r.b in idx and r.a != r.b:
            key = (frozenset((r.a, r.b)), r.strong)
            if key in seen:
                continue
            seen.add(key)
            v = w.strong if r.strong else w.weak
            W[idx[r.a], idx[r.b]] += v
            W[idx[r.b], idx[r.a]] += v
    from .uml import method_name
    for c in classes:
        for raw in diagram.classes[c].methods:
            for other in classes:
                if other != c and re.search(rf"\b{re.escape(other)}\b", raw.replace(method_name(raw), " ")):
                    W[idx[c], idx[other]] += w.sig
                    W[idx[other], idx[c]] += w.sig
    mx = W.max()
    if mx > 0:
        W = W / mx
    return DutyGraph([f"{c}" for c in classes], classes, W)
