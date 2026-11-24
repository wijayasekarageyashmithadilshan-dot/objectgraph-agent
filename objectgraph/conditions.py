"""The teams compared in the pilot. Every condition returns one label per duty
of the same duty graph; the orchestrator, prompts and token cap are identical.

  G2  single agent (with the design)
  G4  random team with the same group sizes as the reference team; for
      projects where the criterion says k*=1, the reference sizes are those
      of one-agent-per-class (so "split vs don't split" can be tested)
  GC  one agent per class
  G6  Infomap partition of the same duty graph (Co-Coder's partitioner)
  G7  the criterion (average linkage + MQ, k*)
  G8  LLM Architect team (CodeTeam-style; built in pipeline.run_condition, needs a model call)
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import adjusted_rand_score

from .criterion import select_k

CONDITIONS = ["G2", "G4", "GC", "G6", "G7"]
DESCRIPTION = {
    "G2": "single agent",
    "G4": "random team, same sizes",
    "GC": "one agent per class",
    "G6": "Infomap team (Co-Coder-style)",
    "G7": "criterion team (ours)",
    "G8": "LLM Architect team (CodeTeam-style)",
}


def class_labels(graph) -> np.ndarray:
    classes = sorted(set(graph.owner))
    return np.array([classes.index(o) for o in graph.owner])


def infomap_labels(W: np.ndarray, seed: int) -> np.ndarray:
    import warnings
    import infomap
    n = W.shape[0]
    if n == 1 or W.sum() == 0:
        return np.zeros(n, dtype=int)
    im = infomap.Infomap(silent=True, two_level=True, seed=seed)
    for i in range(n):
        im.add_node(i)
    for i in range(n):
        for j in range(i + 1, n):
            if W[i, j] > 0:
                im.add_link(i, j, float(W[i, j]))
    im.run()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mods = im.get_modules()
    lab = np.array([mods[i] for i in range(n)])
    return np.unique(lab, return_inverse=True)[1]


def same_partition(a: np.ndarray, b: np.ndarray) -> bool:
    return len(a) == len(b) and adjusted_rand_score(a, b) > 0.999999


def random_labels(reference: np.ndarray, avoid: list[np.ndarray], seed: int, tries: int = 1000) -> np.ndarray:
    """Shuffle the reference labels (same group sizes); redraw if the result
    equals any partition in `avoid` (e.g. the criterion's own team)."""
    rng = np.random.default_rng(seed)
    for _ in range(tries):
        lab = rng.permutation(reference)
        if not any(same_partition(lab, x) for x in avoid):
            return lab
    return lab  # tiny graphs may have no different partition; caller records this


def build_conditions(graph, lam: float = 0.0, seed: int = 20261121) -> dict[str, dict]:
    n = graph.n
    k_star, g7, _ = select_k(graph.W, lam)
    gc = class_labels(graph)
    ref = g7 if k_star > 1 else gc
    out = {
        "G2": np.zeros(n, dtype=int),
        "G7": g7,
        "GC": gc,
        "G6": infomap_labels(graph.W, seed),
    }
    out["G4"] = random_labels(ref, [g7, gc], seed)
    res = {}
    for name in CONDITIONS:
        lab = out[name]
        dup = next((o for o in CONDITIONS if o != name and o in res and same_partition(lab, out[o])), None)
        res[name] = {"labels": lab, "k": int(len(set(lab.tolist()))), "same_as": dup}
    res["_meta"] = {"k_star": int(k_star), "random_reference": "G7" if k_star > 1 else "GC", "seed": seed}
    return res
