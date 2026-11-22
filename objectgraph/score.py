"""Score code with DevBench's own tests.

The reference implementation (``code_file_DAG`` files) is deleted from a
temporary copy of the project, the given files are written in its place, and
the unit and acceptance tests run.

* Python: a fresh virtual environment on this machine ("native").
* C++ / Java / JavaScript: DevBench's Docker image (g++ 11, JDK 14, Node),
  built once with
      docker build --platform linux/amd64 -t devbench:complete DevBench/docker/complete
  Newer compilers on the host do not build DevBench's own reference code,
  so the image is required for these languages.

Run scripts/check_scorer.py first: it feeds DevBench's own answer code through
this scorer and must report every test passing.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from .testparse import counts, junit_counts, strip_reporting

FIXES = {" test": " unit_tests", " test_acceptance.py": " acceptance_tests/test_acceptance.py"}


def _prepare(project_dir: Path, files: dict[str, str], tmp: Path) -> tuple[Path, dict]:
    cfg = json.loads((project_dir / "repo_config.json").read_text())
    work = tmp / project_dir.name
    shutil.copytree(project_dir, work)
    for ref in cfg.get("code_file_DAG", {}):
        (work / ref).unlink(missing_ok=True)
    for p, code in files.items():
        dst = work / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(code, encoding="utf-8")
    return work, cfg


def _setup_lines(work: Path, cfg: dict) -> list[str]:
    name = cfg.get("setup_shell_script") or ""
    setup = work / name if name else None
    if not setup or not setup.is_file():
        return []
    lines = [l.replace("sudo ", "") for l in setup.read_text().splitlines()
             if l.strip() and not l.lstrip().startswith("#")]
    if not (work / "requirements.txt").exists() and (work / "docs" / "requirements.txt").exists():
        lines = [l.replace("-r requirements.txt", "-r docs/requirements.txt") for l in lines]
    return lines


def _test_commands(work: Path, cfg: dict) -> list[tuple[str, str]]:
    cmds = []
    for kind in ("unit_test_script", "acceptance_test_script"):
        cmd = strip_reporting(cfg.get(kind, ""))
        if not cmd:
            continue
        for old, new in FIXES.items():
            if cmd.endswith(old) and not (work / old.strip()).exists() and (work / new.strip()).exists():
                cmd = cmd[: -len(old)] + new
        cmds.append((kind.replace("_script", ""), cmd))
    return cmds


def _collect(out: dict, kind: str, text: str, work: Path, language: str) -> None:
    c = counts(text)
    if language == "java":
        j = junit_counts(work / "build")
        if sum(j.values()):
            c = j
            shutil.rmtree(work / "build" / "test-results", ignore_errors=True)
    n = c["passed"] + c["failed"] + c["errors"]
    out[kind] = {**c, "total": n}
    out["passed"] += c["passed"]
    out["total"] += n
    if n == 0:
        out.setdefault("log_tails", {})[kind] = text[-1500:]


def score_project(project_dir: Path, files: dict[str, str], scorer: str = "auto",
                  docker_image: str = "devbench:complete", timeout: int = 1800) -> dict:
    cfg = json.loads((Path(project_dir) / "repo_config.json").read_text())
    lang = cfg.get("language")
    mode = scorer if scorer != "auto" else ("native" if lang == "python" else "docker")
    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        work, cfg = _prepare(Path(project_dir), files, tmp)
        out = {"status": "scored", "scorer": mode, "language": lang, "passed": 0, "total": 0}
        setup = _setup_lines(work, cfg)
        tests = _test_commands(work, cfg)
        if mode == "native":
            env = dict(os.environ, PYTHONPATH=str(work))
            if lang == "python":
                venv = tmp / "venv"
                subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
                env.update(VIRTUAL_ENV=str(venv), PATH=f"{venv}/bin:{os.environ['PATH']}")
                setup = ["pip install -q pytest"] + setup
            sh = lambda c: subprocess.run(c, shell=True, cwd=work, env=env, capture_output=True,
                                          text=True, timeout=timeout)
            if setup:
                sh(" && ".join(setup))
            for kind, cmd in tests:
                p = sh(cmd)
                _collect(out, kind, p.stdout + p.stderr, work, lang)
        elif mode == "docker":
            if shutil.which("docker") is None:
                return {"status": "needs_docker", "language": lang}
            name = f"ogscore-{uuid.uuid4().hex[:8]}"
            start = subprocess.run(["docker", "run", "-d", "--rm", "--platform", "linux/amd64",
                                    "--name", name, "-v", f"{work}:/work", "-w", "/work",
                                    docker_image, "sleep", "infinity"], capture_output=True, text=True)
            if start.returncode != 0:
                return {"status": "docker_error", "language": lang, "detail": start.stderr[-800:]}
            try:
                dx = lambda c: subprocess.run(["docker", "exec", name, "bash", "-lc", c],
                                              capture_output=True, text=True, timeout=timeout)
                if setup:
                    s = dx(" && ".join(setup))
                    out["setup_ok"] = s.returncode == 0
                for kind, cmd in tests:
                    p = dx(cmd)
                    _collect(out, kind, p.stdout + p.stderr, work, lang)
            finally:
                # files written by the container belong to root; hand them back before cleanup
                subprocess.run(["docker", "exec", name, "chmod", "-R", "a+rwX", "/work"], capture_output=True)
                subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        else:
            raise ValueError(scorer)
        out["pass_rate"] = round(out["passed"] / out["total"], 4) if out["total"] else 0.0
        return out


def score_python(project_dir: Path, files: dict[str, str], timeout: int = 900) -> dict:
    """Backward-compatible wrapper."""
    return score_project(project_dir, files, scorer="native", timeout=timeout)
