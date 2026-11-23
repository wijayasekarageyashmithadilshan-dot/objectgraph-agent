"""Run the team-size criterion on every RealBench design (no LLM calls).

Usage:  python scripts/run_realbench_structural.py --root <dir with level1..level4> --out results
Writes: results/realbench_structural.json, results/realbench_table.csv

Two views per project:
  * "full"    - classes + module-level functions (the whole design an agent
                team must implement; main view);
  * "classes" - classes only (comparable to the DevBench class diagrams).
Every number is deterministic (fixed seeds, sorted inputs).
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from objectgraph.realbench import load_realbench                     # noqa: E402
from objectgraph.graph import Weights, build_duty_graph              # noqa: E402
from objectgraph.criterion import select_k                           # noqa: E402
from run_structural import analyse, weight_grid, SEED, DRAWS, LAMBDAS  # noqa: E402


def find_projects(root: Path) -> list[tuple[str, str, str, Path]]:
    out = []
    for uml in sorted(root.glob("level*/*/*/uml_output/*_uml.json")):
        if "__MACOSX" in uml.parts:
            continue
        proj_dir = uml.parent.parent
        out.append((proj_dir.parent.parent.name, proj_dir.parent.name, proj_dir.name, uml))
    return out


def view(uml: Path, include_functions: bool) -> dict | None:
    diagram, stats = load_realbench(uml, uml.parent / "dag.json", include_functions)
    if not diagram.classes:
        return {"empty": True, "mapping": stats}
    g = build_duty_graph(diagram)
    if g.n == 0:
        return {"empty": True, "mapping": stats}
    rec = analyse(g.W, g.owner, "duty")
    rec["mapping"] = stats
    rec["units"] = rec.pop("n_classes")
    _, lab, _ = select_k(g.W, 0.0)
    rec["weight_grid"] = weight_grid(diagram, lab, rec["k_star"]) if g.n <= 400 else None
    rec["teams"] = {f"agent_{int(k) + 1}": [g.duties[i] for i in np.flatnonzero(lab == k)]
                    for k in np.unique(lab)}
    # components: groups of units with no edge between them at all
    import networkx as nx
    G = nx.from_numpy_array((g.W > 0).astype(int))
    rec["components"] = nx.number_connected_components(G)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    root, out = Path(args.root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    records, rows = [], []
    for level, domain, proj, uml in find_projects(root):
        full, cls = view(uml, True), view(uml, False)
        records.append({"level": level, "domain": domain, "project": proj, "full": full, "classes": cls})
        f = full
        if f.get("empty"):
            print(f"{level}/{proj}: empty design"); continue
        row = {"level": level, "domain": domain, "project": proj,
               "units": f.get("units"), "classes": f["mapping"]["classes"],
               "module_functions": f["mapping"]["module_functions"], "duties": f.get("n"),
               "components": f.get("components"), "k_star": f.get("k_star"),
               "sizes": "+".join(map(str, f.get("sizes", [f.get("n")]))),
               "splits_a_unit": f.get("splits_a_class"), "ari_vs_one_per_unit": f.get("ari_vs_one_per_class"),
               "mq_minus_one_per_unit": f.get("criterion_mq_minus_gc_mq"),
               "cut_reduction_vs_random": f.get("cut_reduction_vs_random"), "p_random": f.get("p_random"),
               "same_k_over_81_weights": (f.get("weight_grid") or {}).get("same_k"),
               "infomap_k": f.get("infomap_k"), "louvain_k": f.get("louvain_k"),
               "k_star_classes_only": None if cls.get("empty") else cls.get("k_star"),
               "classes_only_duties": None if cls.get("empty") else cls.get("n")}
        rows.append(row)
        print(f"{level}/{proj}: units={row['units']} duties={row['duties']} comps={row['components']} "
              f"k*={row['k_star']} infomap={row['infomap_k']} | classes-only k*={row['k_star_classes_only']}")

    meta = {"benchmark": "RealBench (arXiv 2604.22659), projs_filtered_uml", "projects": len(records),
            "draws": DRAWS, "seed": SEED, "lambdas": LAMBDAS, "default_weights": Weights().as_dict(),
            "python": platform.python_version(), "numpy": np.__version__}
    (out / "realbench_structural.json").write_text(json.dumps({"meta": meta, "projects": records}, indent=2))
    pd.DataFrame(rows).to_csv(out / "realbench_table.csv", index=False)
    print(f"\nWrote {out}/realbench_structural.json and realbench_table.csv")


if __name__ == "__main__":
    main()
