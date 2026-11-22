"""Cheap model probe BEFORE the pilot: single agent (G2) only.

Model choice is checked on the single-agent condition, never on the team
conditions, so it cannot favour any way of splitting. Results go to separate
folders (cache_probe/, runs/probe/) and are reported as exploratory.

    python scripts/probe_model.py --model alibaba/qwen3.6-35b-a3b --projects python/stocktrends python/lice
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from objectgraph.llm import LLM                               # noqa: E402
from objectgraph.pipeline import load_project, get_design, run_condition  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--provider", default="vercel")
    ap.add_argument("--projects", nargs="+", default=["python/stocktrends", "python/lice"])
    ap.add_argument("--no-seq", action="store_true", help="leave out the sequence diagram")
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--devbench", default=str(ROOT / "DevBench"))
    a = ap.parse_args()
    llm = LLM(a.provider, a.model, ROOT / "cache_probe", temperature=0.0, max_tokens=a.max_tokens)
    rows = []
    for project in a.projects:
        proj = load_project(Path(a.devbench), project)
        design = get_design(proj, "gold", llm, 0)
        out = ROOT / "runs" / "probe" / a.model.replace("/", "--") / project.replace("/", "__")
        s = run_condition(proj, project, design, "G2", llm, 0, out, ROOT / "results" / "reference_tests.json",
                          budget=200000, use_seq=not a.no_seq)
        sc = s.get("score", {})
        rows.append({"project": project, "model": a.model, "seq": not a.no_seq,
                     "passed": sc.get("passed"), "of": sc.get("reference_total", sc.get("total")),
                     "tokens": s.get("tokens"), "output_tokens": s.get("output_tokens")})
        print(f"{a.model:32} {project:22} passed {sc.get('passed')}/{sc.get('reference_total', sc.get('total'))}"
              f"  tokens {s.get('tokens')} (output {s.get('output_tokens')})")
    path = ROOT / "results" / "probe.jsonl"
    with path.open("a") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
