"""Team-size criterion: average-linkage clustering + Mancoridis MQ.

For a partition into k groups with sizes N_i:
  A_i  = 2 * W_in(i) / N_i^2               (intra-connectivity)
  E_ij = W_between(i, j) / (N_i * N_j)       (inter-connectivity)
  MQ   = mean_i A_i - mean_{i<j} E_ij        (k > 1);   MQ = A_1 for k = 1
which is the weighted, undirected form of Mancoridis et al. (1998).
k* = argmax_k  MQ(k) - lam * (k - 1) / (n - 1).
"""
from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import linkage, cut_tree
from scipy.spatial.distance import squareform


def mq(W: np.ndarray, labels: np.ndarray) -> float:
    _, lab = np.unique(labels, return_inverse=True)
    k = int(lab.max()) + 1
    B = np.zeros((len(lab), k))
    B[np.arange(len(lab)), lab] = 1.0
    S = B.T @ W @ B                                   # S[a, b] = weight between groups a and b
    N = B.sum(axis=0)
    A = np.diag(S) / N ** 2                           # diag(S) = 2 * W_in
    if k == 1:
        return float(A[0])
    iu = np.triu_indices(k, 1)
    E = S[iu] / (N[iu[0]] * N[iu[1]])
    return float(A.mean() - E.mean())


def cut_weight(W: np.ndarray, labels: np.ndarray) -> float:
    """Total weight of edges whose endpoints are in different groups."""
    diff = labels[:, None] != labels[None, :]
    return float(W[diff].sum() / 2)


def hierarchy(W: np.ndarray) -> np.ndarray:
    """Average-linkage tree on distance 1 - W (non-edges at distance 1)."""
    D = 1.0 - W
    np.fill_diagonal(D, 0.0)
    return linkage(squareform(D, checks=False), method="average")


def all_cuts(W: np.ndarray) -> dict[int, np.ndarray]:
    n = W.shape[0]
    if n == 1:
        return {1: np.zeros(1, dtype=int)}
    Z = hierarchy(W)
    return {k: cut_tree(Z, n_clusters=k).ravel() for k in range(1, n + 1)}


def select_k(W: np.ndarray, lam: float = 0.0) -> tuple[int, np.ndarray, dict[int, float]]:
    """Return k*, its labels and the MQ curve."""
    n = W.shape[0]
    cuts = all_cuts(W)
    curve = {k: mq(W, lab) for k, lab in cuts.items()}
    if n == 1:
        return 1, cuts[1], curve
    score = {k: curve[k] - lam * (k - 1) / (n - 1) for k in curve}
    best = max(score.values())
    k_star = min(k for k, v in score.items() if np.isclose(v, best))  # ties -> fewer agents
    return k_star, cuts[k_star], curve


def expected_random_cut(W: np.ndarray, sizes: list[int]) -> float:
    """Closed form for the expected cut of a uniformly random partition with
    the given group sizes: each edge is internal with probability
    sum_i N_i (N_i - 1) / (n (n - 1))."""
    n = W.shape[0]
    total = W.sum() / 2
    p_in = sum(s * (s - 1) for s in sizes) / (n * (n - 1))
    return float(total * (1 - p_in))


def random_cuts(W: np.ndarray, labels: np.ndarray, draws: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.empty(draws)
    for t in range(draws):
        out[t] = cut_weight(W, rng.permutation(labels))
    return out
