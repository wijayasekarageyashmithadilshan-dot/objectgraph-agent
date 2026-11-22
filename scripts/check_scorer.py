"""Phase 0 scorer check: feed DevBench's OWN answer code through our scorer.

Every test should pass. If one does not, that test (or project) cannot be
used to score agents. Run this before spending any API money.

  python scripts/check_scorer.py --projects python/stocktrends python/lice python/TextCNN
  python scripts/check_scorer.py --projects cpp/xlsx2csv java/idcenter      # needs Docker image

Results are merged into results/reference_tests.json (used as the denominator
of every pass rate) and printed as a table.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from objectgraph.score import score_project  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--devbench", default=str(ROOT / "DevBench"))
    ap.add_argument("--projects", nargs="+", required=True)
    ap.add_argument("--scorer", default="auto", choices=["auto", "native", "docker"])
    ap.add_argument("--docker-image", default="devbench:complete")
    ap.add_argument("--results", default=str(ROOT / "results"))
    a = ap.parse_args()
    ref_path = Path(a.results) / "reference_tests.json"
    refs = json.loads(ref_path.read_text()) if ref_path.exists() else []
    rows = []
    for project in a.projects:
        pdir = Path(a.devbench) / "benchmark_data" / project
        cfg = json.loads((pdir / "repo_config.json").read_text())
        files = {f: (pdir / f).read_text(encoding="utf-8", errors="replace") for f in cfg.get("code_file_DAG", {})}
        oracle = score_project(pdir, files, scorer=a.scorer, docker_image=a.docker_image)
        empty = score_project(pdir, {}, scorer=a.scorer, docker_image=a.docker_image)
        ok = (oracle.get("status") == "scored" and oracle["total"] > 0
              and oracle["passed"] == oracle["total"] and empty.get("passed", 0) == 0)
        rec = {"project": project, "scorer": oracle.get("scorer"), "oracle": oracle,
               "empty_code_passed": empty.get("passed"), "usable": ok}
        for k in ("unit_test", "acceptance_test"):
            if k in oracle:
                rec[k] = {x: oracle[k][x] for x in ("passed", "failed", "errors", "skipped")}
        refs = [r for r in refs if r["project"] != project] + [rec]
        rows.append((project, oracle.get("status"), f"{oracle.get('passed', 0)}/{oracle.get('total', 0)}",
                     empty.get("passed"), "YES" if ok else "NO"))
    ref_path.write_text(json.dumps(refs, indent=2))
    print(f"{'project':28} {'status':12} {'answer code':12} {'empty code':10} usable")
    for r in rows:
        print(f"{r[0]:28} {str(r[1]):12} {r[2]:12} {str(r[3]):10} {r[4]}")


if __name__ == "__main__":
    main()
