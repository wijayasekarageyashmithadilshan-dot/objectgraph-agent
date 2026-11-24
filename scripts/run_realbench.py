"""Experiment 2: the five conditions on the pre-registered RealBench tasks.

  python scripts/run_realbench.py --data <folder with level1..level4> --check     # zero calls: reference scores
  python scripts/run_realbench.py --data <...> --task level2/FreddyRodgers_emojichef
  python scripts/run_realbench.py --data <...> --all
  python scripts/run_realbench.py --data <...> --all --provider fake               # dry run, no API

Settings come from prereg/plan.yaml (experiment_2 block; model from its `model`
key). Results: results/experiment_2/<task>.json, reference.json; runs/experiment_2/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from objectgraph.llm import LLM                                  # noqa: E402
from objectgraph.pipeline import run_condition                    # noqa: E402
from objectgraph.realbench_task import load_task                  # noqa: E402
from objectgraph.realbench_score import run_tests, source_files   # noqa: E402
from run_pilot import git_state, plan_frozen_tag                  # noqa: E402


def task_dir(data: Path, task: str) -> Path:
    level, name = task.split("/", 1)
    hits = [p for p in (data / level).glob(f"*/{name}") if p.is_dir()]
    if not hits:
        raise SystemExit(f"task {task} not found under {data}")
    return hits[0]


def reference(data: Path, tasks: list[str], out: Path, python: str) -> dict:
    path = out / "reference.json"
    ref = json.loads(path.read_text()) if path.exists() else {}
    for t in tasks:
        if t in ref:
            continue
        d = task_dir(data, t)
        if not (d / "proj_with_test").exists():
            ref[t] = {"usable": False, "reason": "RealBench ships no tests for this project", "passed": 0}
        else:
            r = run_tests(d, None, python=python)
            ref[t] = {"usable": r["passed"] > 0, "passed": r["passed"], "failed": r["failed"],
                      "errors": r["errors"], "total": r["total"],
                      "reason": "" if r["passed"] > 0 else "reference code passes no test here: " + r["log_tail"][-300:]}
        print(f"{t}: reference passes {ref[t]['passed']} -> {'usable' if ref[t]['usable'] else 'NOT usable'}")
        path.write_text(json.dumps(ref, indent=2))
    return ref


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="folder that contains level1..level4")
    ap.add_argument("--plan", default=str(ROOT / "prereg" / "plan.yaml"))
    ap.add_argument("--block", default="experiment_2", help="plan block: experiment_2 or experiment_2b")
    ap.add_argument("--task", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true", help="only score the reference code (no model calls)")
    ap.add_argument("--fresh-reference", action="store_true", help="re-run the reference tests here instead of reusing usable_from")
    ap.add_argument("--conditions", nargs="*")
    ap.add_argument("--runs", nargs="*", type=int)
    ap.add_argument("--provider", default=None, help="'fake' for a dry run")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--python", default=sys.executable, help="interpreter that runs the tests")
    ap.add_argument("--no-budget", action="store_true", help="harness check only: no token cap")
    ap.add_argument("--cache", default=str(ROOT / "cache"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--results", default=None)
    a = ap.parse_args()

    import objectgraph.orchestrator as orch
    orch.MERGE_V2 = True
    plan = yaml.safe_load(Path(a.plan).read_text())
    e2 = plan[a.block]
    a.out = a.out or str(ROOT / "runs" / a.block)
    a.results = a.results or str(ROOT / "results" / a.block)
    data, res = Path(a.data), Path(a.results)
    res.mkdir(parents=True, exist_ok=True)
    tasks = a.task or (e2["tasks"] if (a.all or a.check) else [])
    if not tasks:
        raise SystemExit("give --task level/name, --all or --check")
    src_ref = ROOT / "results" / str(e2.get("usable_from", "")) / "reference.json"
    if e2.get("usable_from") and not a.fresh_reference and not (res / "reference.json").exists() and src_ref.exists():
        (res / "reference.json").write_text(src_ref.read_text())   # same tasks, same usability rule
    ref = reference(data, tasks, res, a.python)
    if a.check:
        print(f"\n{sum(r['usable'] for r in ref.values() if r)} usable of {len(tasks)}; wrote {res}/reference.json")
        return

    m = {**plan["model"], **plan[e2["model"]]}
    provider = a.provider or m["provider"]
    frozen = plan_frozen_tag(Path(a.plan))
    if provider != "fake" and not a.offline and not frozen:
        raise SystemExit("prereg/plan.yaml does not match any prereg-* tag. Create the release first.")
    if frozen:
        print(f"Plan matches frozen tag {frozen}.")
    conds = a.conditions or e2["conditions"]
    runs = a.runs if a.runs is not None else list(range(e2["runs_per_condition"]))
    if e2.get("usable_from"):          # usability already decided (same tasks, same sandbox rule)
        tasks = [t for t in tasks if ref.get(t, {}).get("usable")]

    for t in tasks:
        if not ref[t]["usable"]:
            print(f"{t}: skipped (not usable: {ref[t]['reason'][:120]})")
            continue
        d = task_dir(data, t)
        task = load_task(d)
        tree = next((d / "uml_output").glob("tree.txt"), None)
        root = tree.read_text(encoding="utf-8").splitlines()[0].strip().rstrip("/") if tree else ""
        orch.STRIP_PREFIXES = (root + "/",) if root else ()
        fake_fn = None
        if provider == "fake":
            from tests.fake_model import fake_reply_realbench
            fake_fn = lambda s, u: fake_reply_realbench(s, u, d)
        llm = LLM(provider, m["name"], a.cache, offline=a.offline, temperature=m["temperature"],
                  max_tokens=m["max_tokens_per_call"], fake_fn=fake_fn,
                  reasoning_effort=m.get("reasoning_effort"), reasoning_enabled=m.get("reasoning_enabled"))
        rows, failed, stop = [], [], False
        for rid in runs:
            for c in conds:
                out = Path(a.out) / t.replace("/", "__") / c / f"run{rid}"
                try:
                    s = run_condition(task, t, task["design"], c, llm, rid, out, None, agents=True, score=False,
                                      lam=plan["criterion"]["lambda"], budget=None if a.no_budget else plan["token_cap_per_run"])
                except Exception as e:      # provider failure: skipped, not scored as 0
                    print(f"{t} {c} run{rid}: FAILED, not counted ({type(e).__name__}: {str(e)[:300]})")
                    failed.append({"condition": c, "run_id": rid, "error": f"{type(e).__name__}: {str(e)[:500]}"})
                    if "refused the call" in str(e):
                        print("Stopping: the provider refused the call (key, credit, access or model).")
                        stop = True
                        break
                    continue
                files = {p.relative_to(out / "code").as_posix(): p.read_text(encoding="utf-8", errors="ignore")
                         for p in (out / "code").rglob("*") if p.is_file()} if (out / "code").exists() else {}
                sc = run_tests(d, files, python=a.python)
                s["passed"] = sc["passed"]
                s["reference_passed"] = ref[t]["passed"]
                s["pass_rate"] = round(sc["passed"] / ref[t]["passed"], 4)
                s["files_written"] = sorted(files)
                s["source_files_expected"] = source_files(d)
                (out / "score.json").write_text(json.dumps({k: v for k, v in sc.items() if k != "cases"}, indent=2))
                (out / "summary.json").write_text(json.dumps(s, indent=2))
                rows.append(s)
                print(f"{t} {c} run{rid}: k={s['k']} pass={s['pass_rate']} ({sc['passed']}/{ref[t]['passed']}) "
                      f"tokens={s.get('tokens')}" + (f" (same team as {s['same_as']})" if s["same_as"] else ""))
            if stop:
                break
        path = res / f"{t.replace('/', '__')}.json"
        old = json.loads(path.read_text())["rows"] if path.exists() else []
        keep = [r for r in old if (r["condition"], r["run_id"]) not in {(x["condition"], x["run_id"]) for x in rows}]
        path.write_text(json.dumps({"task": t, "model": m["name"], "provider": provider, "plan_tag": frozen,
                                    "git": git_state(), "reference_passed": ref[t]["passed"],
                                    "rows": keep + rows, "failed_runs": failed}, indent=2))
        if stop:
            break
    print(f"\nWrote {res}. Next: python scripts/analyse_exp2.py")


if __name__ == "__main__":
    main()
