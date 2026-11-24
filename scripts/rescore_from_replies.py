"""Re-score saved runs from the model's raw replies (no model calls).

Used after a fix to reply parsing: every agent's raw reply is kept in runs/<block>/<task>/<cond>/run<i>/agent_*.md,
so the team's files can be rebuilt with the current parser and merge, and scored again.

  python scripts/rescore_from_replies.py --runs runs/experiment_2b --results results/experiment_2b \
      --data <projs_filtered_uml> --python <test interpreter> [--task level3/Reconnaissance ...]

A run is re-scored only if the current parser produces different files from those that were
scored; otherwise its row is left untouched. Every change is listed in rescore_log.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import objectgraph.orchestrator as orch                      # noqa: E402
from objectgraph.realbench_score import run_tests             # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
from run_realbench import task_dir                            # noqa: E402


def rebuild(run_dir: Path) -> dict[str, str]:
    team = json.loads((run_dir / "team.json").read_text())
    by_id = {a["agent_id"]: a for a in team["agents"]}
    fragments: dict[str, list] = {}
    for aid in team["order"]:
        f = run_dir / f"{aid}.md"
        if not f.exists():
            continue
        for path, code in orch.parse_blocks(f.read_text(encoding="utf-8")):
            fragments.setdefault(path, []).append((set(by_id[aid]["duties"]), code))
    return {p: orch.merge_fragments(p, [c for _, c in frs], [o for o, _ in frs]) for p, frs in fragments.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--task", action="append", default=[])
    a = ap.parse_args()
    orch.MERGE_V2 = True
    res = Path(a.results)
    log = []
    for rf in sorted(res.glob("level*.json")):
        d = json.loads(rf.read_text())
        t = d["task"]
        if a.task and t not in a.task:
            continue
        tdir = task_dir(Path(a.data), t)
        tree = (tdir / "uml_output" / "tree.txt")
        root = tree.read_text(encoding="utf-8").splitlines()[0].strip().rstrip("/") if tree.exists() else ""
        orch.STRIP_PREFIXES = (root + "/",) if root else ()
        changed = False
        for r in d["rows"]:
            run_dir = Path(a.runs) / t.replace("/", "__") / r["condition"] / f"run{r['run_id']}"
            files = rebuild(run_dir)
            if sorted(files) == sorted(r.get("files_written", [])) and all(
                    (run_dir / "code" / p).exists() and (run_dir / "code" / p).read_text(encoding="utf-8") == c
                    for p, c in files.items()):
                continue
            sc = run_tests(tdir, files, python=a.python)
            new = round(sc["passed"] / d["reference_passed"], 4)
            log.append({"task": t, "condition": r["condition"], "run_id": r["run_id"],
                        "files_before": r.get("files_written", []), "files_after": sorted(files),
                        "pass_before": r["pass_rate"], "pass_after": new})
            print(f"{t} {r['condition']} run{r['run_id']}: files {len(r.get('files_written', []))} -> {len(files)}, "
                  f"pass {r['pass_rate']} -> {new}")
            r.update({"pass_rate": new, "passed": sc["passed"], "files_written": sorted(files), "rescored": True})
            changed = True
        if changed:
            rf.write_text(json.dumps(d, indent=2))
    prev = json.loads((res / "rescore_log.json").read_text()) if (res / "rescore_log.json").exists() else []
    (res / "rescore_log.json").write_text(json.dumps(prev + log, indent=2))
    print(f"{len(log)} runs re-scored; log in {res}/rescore_log.json")


if __name__ == "__main__":
    main()
