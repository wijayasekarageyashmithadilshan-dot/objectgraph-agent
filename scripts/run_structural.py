"""Run the team-size criterion on every DevBench project (no LLM calls).

Usage:  python scripts/run_structural.py --devbench DevBench --out results
Writes: results/structural.json, results/table_main.csv,
        results/table_lambda.csv, results/table_weights.csv,
        results/figures/mq_curves.png
Every number is deterministic (fixed seeds, sorted inputs).
"""
from __future__ import annotations

import argparse
import itertools
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from objectgraph.uml import parse_class_diagram                      # noqa: E402
from objectgraph.graph import Weights, build_duty_graph, build_class_graph  # noqa: E402
from objectgraph.criterion import (select_k, mq, cut_weight, expected_random_cut,  # noqa: E402
                                   random_cuts)

DRAWS = 2000
SEED = 20261121
LAMBDAS = [0.0, 0.05, 0.1, 0.2]
GRID = [0.5, 1.0, 1.5]          # multipliers for the +-50% weight grid (3^4 = 81 settings)


def find_projects(root: Path) -> list[tuple[str, str, Path]]:
    out = []
    for lang_dir in sorted((root / "benchmark_data").iterdir()):
        if not lang_dir.is_dir():
            continue
        for proj in sorted(p for p in lang_dir.iterdir() if p.is_dir()):
            for cand in (proj / "UML_class.md", proj / "docs" / "UML_class.md"):
                if cand.exists():
                    out.append((lang_dir.name, proj.name, cand))
                    break
    return out


def louvain_labels(W: np.ndarray, seed: int) -> np.ndarray:
    G = nx.from_numpy_array(W)
    comms = nx.community.louvain_communities(G, weight="weight", seed=seed)
    lab = np.zeros(W.shape[0], dtype=int)
    for i, c in enumerate(sorted(comms, key=lambda s: min(s))):
        for v in c:
            lab[v] = i
    return lab


def infomap_labels(W: np.ndarray, seed: int) -> np.ndarray:
    import infomap
    im = infomap.Infomap(silent=True, two_level=True, seed=seed)
    n = W.shape[0]
    for i in range(n):
        im.add_node(i)
    for i in range(n):
        for j in range(i + 1, n):
            if W[i, j] > 0:
                im.add_link(i, j, float(W[i, j]))
    import warnings
    im.run()
    lab = np.zeros(n, dtype=int)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modules = im.get_modules()
    for node, mod in modules.items():
        lab[node] = mod
    _, lab = np.unique(lab, return_inverse=True)
    return lab


def analyse(W: np.ndarray, owner: list[str], level: str) -> dict:
    n = W.shape[0]
    k_star, lab, curve = select_k(W, 0.0)
    rec = {"level": level, "n": n, "k_star": int(k_star),
           "mq_curve": {int(k): round(v, 6) for k, v in curve.items()},
           "mq_star": round(curve[k_star], 6), "total_weight": round(float(W.sum() / 2), 6)}
    rec["k_by_lambda"] = {str(l): int(select_k(W, l)[0]) for l in LAMBDAS}
    if k_star > 1:
        sizes = [int((lab == g).sum()) for g in np.unique(lab)]
        obs = cut_weight(W, lab)
        rc = random_cuts(W, lab, DRAWS, SEED)
        rec.update({
            "sizes": sorted(sizes, reverse=True),
            "cut": round(obs, 6),
            "random_cut_mean": round(float(rc.mean()), 6),
            "random_cut_expected_closed_form": round(expected_random_cut(W, sizes), 6),
            "p_random": round((1 + int((rc <= obs).sum())) / (DRAWS + 1), 6),
            "cut_reduction_vs_random": round(1 - obs / rc.mean(), 6) if rc.mean() > 0 else None,
        })
    if level == "duty":
        cls = np.array([sorted(set(owner)).index(o) for o in owner])
        rec["n_classes"] = int(len(set(owner)))
        rec["gc_mq"] = round(mq(W, cls), 6)
        rec["gc_cut"] = round(cut_weight(W, cls), 6)
        rec["ari_vs_one_per_class"] = round(adjusted_rand_score(cls, lab), 6)
        # does any group split a class across agents?
        rec["splits_a_class"] = bool(any(len(set(lab[cls == c])) > 1 for c in np.unique(cls)))
        rec["criterion_mq_minus_gc_mq"] = round(curve[k_star] - mq(W, cls), 6)
    if n > 1 and W.sum() > 0:
        lv, im = louvain_labels(W, SEED), infomap_labels(W, SEED)
        rec["louvain_k"] = int(len(np.unique(lv)))
        rec["infomap_k"] = int(len(np.unique(im)))
        rec["ari_vs_louvain"] = round(adjusted_rand_score(lv, lab), 6)
        rec["ari_vs_infomap"] = round(adjusted_rand_score(im, lab), 6)
    return rec


def weight_grid(diagram, default_lab: np.ndarray, default_k: int) -> dict:
    same_k, aris = 0, []
    for mult in itertools.product(GRID, repeat=4):
        w = Weights(*(m * d for m, d in zip(mult, Weights().as_dict().values())))
        g = build_duty_graph(diagram, w)
        k, lab, _ = select_k(g.W, 0.0)
        same_k += int(k == default_k)
        aris.append(adjusted_rand_score(default_lab, lab))
    total = len(GRID) ** 4
    return {"settings": total, "same_k": same_k, "same_k_share": round(same_k / total, 6),
            "mean_ari_vs_default": round(float(np.mean(aris)), 6)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--devbench", default="DevBench")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    root, out = Path(args.devbench), Path(args.out)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    records = []
    for lang, proj, path in find_projects(root):
        diagram = parse_class_diagram(path.read_text(encoding="utf-8"))
        dg = build_duty_graph(diagram)
        cg = build_class_graph(diagram)
        duty = analyse(dg.W, dg.owner, "duty")
        _, dlab, _ = select_k(dg.W, 0.0)
        duty["weight_grid"] = weight_grid(diagram, dlab, duty["k_star"])
        duty["teams"] = {}
        for g in np.unique(dlab):
            duty["teams"][f"agent_{int(g) + 1}"] = [dg.duties[i] for i in np.flatnonzero(dlab == g)]
        cls = analyse(cg.W, cg.owner, "class")
        records.append({"language": lang, "project": proj,
                        "uml_path": str(path.relative_to(root)), "duty": duty, "class": cls})
        print(f"{lang}/{proj}: duties={duty['n']} k*={duty['k_star']} | classes={cls['n']} k*={cls['k_star']}")

    meta = {"devbench_commit": "bb593c1f9c535ff0dde0c9f4807d58c9566c3a6c", "draws": DRAWS,
            "seed": SEED, "lambdas": LAMBDAS, "default_weights": Weights().as_dict(),
            "python": platform.python_version(), "numpy": np.__version__}
    (out / "structural.json").write_text(json.dumps({"meta": meta, "projects": records}, indent=2))

    rows = []
    for r in records:
        d, c = r["duty"], r["class"]
        rows.append({
            "project": f"{r['language']}/{r['project']}", "classes": d["n_classes"], "duties": d["n"],
            "k_star_duty": d["k_star"], "sizes": "+".join(map(str, d.get("sizes", [d["n"]]))),
            "cut_reduction_vs_random": d.get("cut_reduction_vs_random"), "p_random": d.get("p_random"),
            "closed_form_vs_sampled": (f"{d['random_cut_expected_closed_form']:.3f} / {d['random_cut_mean']:.3f}"
                                       if "random_cut_mean" in d else ""),
            "mq_minus_one_per_class": d["criterion_mq_minus_gc_mq"],
            "splits_a_class": d["splits_a_class"], "ari_vs_one_per_class": d["ari_vs_one_per_class"],
            "same_k_over_81_weights": d["weight_grid"]["same_k"],
            "louvain_k": d.get("louvain_k"), "infomap_k": d.get("infomap_k"),
            "k_star_class": c["k_star"],
        })
    pd.DataFrame(rows).to_csv(out / "table_main.csv", index=False)
    pd.DataFrame([{"project": f"{r['language']}/{r['project']}", **{f"lambda_{k}": v for k, v in r["duty"]["k_by_lambda"].items()}}
                  for r in records]).to_csv(out / "table_lambda.csv", index=False)
    pd.DataFrame([{"project": f"{r['language']}/{r['project']}", **r["duty"]["weight_grid"]}
                  for r in records]).to_csv(out / "table_weights.csv", index=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    multi = [r for r in records if r["duty"]["k_star"] > 1]
    cols = 4
    rws = int(np.ceil(len(multi) / cols)) or 1
    fig, axes = plt.subplots(rws, cols, figsize=(3.2 * cols, 2.4 * rws), squeeze=False)
    for ax, r in zip(axes.ravel(), multi):
        cur = r["duty"]["mq_curve"]
        ks = sorted(map(int, cur))
        ax.plot(ks, [cur[k] for k in ks], color="#3B6D11", lw=1.5)
        ax.axvline(r["duty"]["k_star"], color="#888780", ls="--", lw=1)
        ax.set_title(f"{r['project']} (k*={r['duty']['k_star']})", fontsize=9)
        ax.set_xlabel("agents k", fontsize=8)
        ax.set_ylabel("MQ", fontsize=8)
        ax.tick_params(labelsize=7)
    for ax in axes.ravel()[len(multi):]:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(out / "figures" / "mq_curves.png", dpi=200)
    print(f"\nWrote {out}/structural.json and tables.")


if __name__ == "__main__":
    main()
