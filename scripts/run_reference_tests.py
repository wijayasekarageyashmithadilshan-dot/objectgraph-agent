"""Run DevBench's own tests against DevBench's reference code (Python projects).

This checks the scorer before any agent is scored: if the reference code does
not pass its own tests in our environment, that test cannot be used.

Usage: python scripts/run_reference_tests.py --devbench DevBench --out results
Writes results/reference_tests.json and results/table_reference_tests.csv.
Each project runs in a fresh virtual environment under a temporary copy.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

SKIP = {"TextCNN": "needs a Hugging Face model/dataset download (network)"}
TIMEOUT = 900


def counts(output: str) -> dict:
    """Parse pytest and unittest summaries."""
    c = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for m in re.finditer(r"=+ (.*?) in [\d.]+s", output):
        for n, kind in re.findall(r"(\d+) (passed|failed|errors?|skipped)", m.group(1)):
            c["errors" if kind.startswith("error") else kind] += int(n)
    ran = re.findall(r"Ran (\d+) tests?", output)
    if ran:
        total = sum(map(int, ran))
        f = sum(int(x) for x in re.findall(r"failures=(\d+)", output))
        e = sum(int(x) for x in re.findall(r"errors=(\d+)", output))
        s = sum(int(x) for x in re.findall(r"skipped=(\d+)", output))
        c["failed"] += f
        c["errors"] += e
        c["skipped"] += s
        c["passed"] += total - f - e - s
    return c


def strip_reporting(cmd: str) -> str:
    """Drop coverage/JSON-report flags: they test coverage, not correctness,
    and --cov-fail-under=100 would fail a correct implementation."""
    cmd = re.sub(r"--cov\S*", "", cmd)
    cmd = re.sub(r"--json-report\S*", "", cmd)
    return re.sub(r"\s+", " ", cmd).strip()


def run(cmd: str, cwd: Path, env: dict) -> tuple[int, str]:
    p = subprocess.run(cmd, shell=True, cwd=cwd, env=env, capture_output=True, text=True, timeout=TIMEOUT)
    return p.returncode, p.stdout + p.stderr


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--devbench", default="DevBench")
    ap.add_argument("--out", default="results")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    src = Path(args.devbench) / "benchmark_data" / "python"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for proj in sorted(p for p in src.iterdir() if p.is_dir()):
        if args.only and proj.name not in args.only:
            continue
        rec = {"project": f"python/{proj.name}"}
        if proj.name in SKIP:
            rec["status"] = f"skipped: {SKIP[proj.name]}"
            results.append(rec)
            print(rec)
            continue
        cfg = json.loads((proj / "repo_config.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / proj.name
            shutil.copytree(proj, work)
            venv = Path(tmp) / "venv"
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
            env = dict(os.environ, VIRTUAL_ENV=str(venv), PATH=f"{venv}/bin:{os.environ['PATH']}",
                       PYTHONPATH=str(work))
            run("pip install -q pytest", work, env)
            setup = work / cfg.get("setup_shell_script", "setup_shell_script.sh")
            if setup.is_file():
                lines = [l for l in setup.read_text().splitlines()
                         if l.strip() and not l.startswith("#") and "sudo" not in l]
                # some scripts point at requirements.txt but ship docs/requirements.txt
                if not (work / "requirements.txt").exists() and (work / "docs" / "requirements.txt").exists():
                    lines = [l.replace("-r requirements.txt", "-r docs/requirements.txt") for l in lines]
                code, log = run(" && ".join(lines) or "true", work, env)
                rec["setup_ok"] = code == 0
                if code != 0:
                    rec["setup_log_tail"] = log[-800:]
            for kind in ("unit_test_script", "acceptance_test_script"):
                cmd = strip_reporting(cfg.get(kind, ""))
                if not cmd:
                    continue
                # hone's config names "test" and "test_acceptance.py", but the
                # files live in unit_tests/ and acceptance_tests/ (DevBench mismatch)
                fixes = {" test": " unit_tests", " test_acceptance.py": " acceptance_tests/test_acceptance.py"}
                for old, new in fixes.items():
                    target = old.strip()
                    if cmd.endswith(old) and not (work / target).exists() and (work / new.strip()).exists():
                        cmd = cmd[: -len(old)] + new
                        rec.setdefault("path_fixes", []).append(f"{target} -> {new.strip()}")
                code, log = run(cmd, work, env)
                c = counts(log)
                rec[kind.replace("_script", "")] = {"command": cmd, **c, "exit_code": code}
                if c["passed"] + c["failed"] + c["errors"] == 0:
                    rec[kind.replace("_script", "") + "_log_tail"] = log[-800:]
        results.append(rec)
        print(json.dumps({k: v for k, v in rec.items() if not k.endswith("log_tail")}))
    (out / "reference_tests.json").write_text(json.dumps(results, indent=2))
    rows = []
    for r in results:
        row = {"project": r["project"], "status": r.get("status", "ran")}
        for k in ("unit_test", "acceptance_test"):
            if k in r:
                t = r[k]
                row[k] = f"{t['passed']}/{t['passed'] + t['failed'] + t['errors']}"
        rows.append(row)
    pd.DataFrame(rows).to_csv(out / "table_reference_tests.csv", index=False)


if __name__ == "__main__":
    main()
