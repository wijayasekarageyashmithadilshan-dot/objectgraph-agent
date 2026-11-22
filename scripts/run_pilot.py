"""Experiment 1: run all pilot conditions on one project (5 teams x 3 runs).

  export ANTHROPIC_API_KEY=...
  python scripts/run_pilot.py --project python/stocktrends
  python scripts/run_pilot.py --project cpp/xlsx2csv            # needs devbench:complete image
  python scripts/run_pilot.py --project python/stocktrends --offline   # replay, no API

Settings come from prereg/plan.yaml. Results: runs/pilot/<project>/<cond>/run<id>/
(report.html, summary.json, code/, ...) and results/pilot/<project>.json.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from objectgraph.llm import LLM                                        # noqa: E402
from objectgraph.pipeline import load_project, get_design, run_condition  # noqa: E402


def git_state() -> dict:
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        tag = subprocess.run(["git", "-C", str(ROOT), "describe", "--tags", "--exact-match"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "prereg"], capture_output=True, text=True).stdout.strip())
        return {"commit": head or None, "tag": tag or None, "prereg_modified_since_commit": dirty}
    except FileNotFoundError:
        return {"commit": None, "tag": None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--plan", default=str(ROOT / "prereg" / "plan.yaml"))
    ap.add_argument("--devbench", default=str(ROOT / "DevBench"))
    ap.add_argument("--conditions", nargs="*", help="subset, e.g. G7 G4")
    ap.add_argument("--runs", nargs="*", type=int, help="subset of run ids")
    ap.add_argument("--provider", default=None, help="override (use 'fake' for a dry run)")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--no-score", action="store_true")
    ap.add_argument("--scorer", default="auto")
    ap.add_argument("--docker-image", default="devbench:complete")
    ap.add_argument("--cache", default=str(ROOT / "cache"))
    ap.add_argument("--out", default=str(ROOT / "runs" / "pilot"))
    ap.add_argument("--results", default=str(ROOT / "results"))
    a = ap.parse_args()

    plan = yaml.safe_load(Path(a.plan).read_text())
    m = plan["model"]
    provider = a.provider or m["provider"]
    gs = git_state()
    if provider != "fake" and not a.offline and gs.get("tag") != "prereg-v1":
        print("WARNING: the commit is not tagged prereg-v1. Freeze the plan first (see prereg/plan.yaml).")
    proj = load_project(Path(a.devbench), a.project)
    fake_fn = None
    if provider == "fake":
        from tests.fake_model import fake_reply
        fake_fn = lambda s, u: fake_reply(s, u, proj["gold_text"])
    llm = LLM(provider, m["name"], a.cache, offline=a.offline, temperature=m["temperature"],
              max_tokens=m["max_tokens_per_call"], fake_fn=fake_fn)
    conds = a.conditions or plan["conditions"]
    runs = a.runs if a.runs is not None else list(range(plan["runs_per_condition"]))
    ref = Path(a.results) / "reference_tests.json"
    rows = []
    for rid in runs:
        design = get_design(proj, plan["design"], llm, rid)
        for c in conds:
            out = Path(a.out) / a.project.replace("/", "__") / c / f"run{rid}"
            s = run_condition(proj, a.project, design, c, llm, rid, out, ref, agents=True,
                              score=not a.no_score, scorer=a.scorer, docker_image=a.docker_image,
                              lam=plan["criterion"]["lambda"], budget=plan["token_cap_per_run"])
            rows.append(s)
            print(f"{c:3} run{rid}: k={s['k']} pass={s.get('pass_rate')} tokens={s.get('tokens')} "
                  f"msgs={s.get('messages')}" + (f" (same team as {s['same_as']})" if s["same_as"] else ""))
    res_dir = Path(a.results) / "pilot"
    res_dir.mkdir(parents=True, exist_ok=True)
    path = res_dir / f"{a.project.replace('/', '__')}.json"
    old = json.loads(path.read_text())["rows"] if path.exists() else []
    keep = [r for r in old if (r["condition"], r["run_id"]) not in {(x["condition"], x["run_id"]) for x in rows}]
    path.write_text(json.dumps({"project": a.project, "model": m["name"], "provider": provider,
                                "git": gs, "rows": keep + rows}, indent=2))
    print(f"\nWrote {path}. Next: python scripts/analyse_pilot.py")


if __name__ == "__main__":
    main()
