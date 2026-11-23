"""Score code for a RealBench project with RealBench's own tests.

Layout of a RealBench project folder:
    proj_clean/      reference code without tests (defines which files are "source")
    proj_with_test/  reference code + tests
    uml_output/      design (class diagram JSON, package diagram, file tree)

Scoring a candidate: copy ``proj_with_test`` (without any virtualenv), delete
every source file that ``proj_clean`` defines, write the candidate's files in
their place, run pytest with a per-test timeout and count passed test cases
from the JUnit XML. The reference score is the same run with the reference
source left in place. pass_rate = passed(candidate) / passed(reference).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SKIP_DIRS = {"venv", ".venv", "env", "__pycache__", ".git", "node_modules", ".pytest_cache"}


def _py_files(root: Path) -> list[str]:
    out = []
    for p in root.rglob("*.py"):
        rel = p.relative_to(root)
        if not any(part in SKIP_DIRS for part in rel.parts):
            out.append(rel.as_posix())
    return sorted(out)


def source_files(project: Path) -> list[str]:
    """Python files the team must write (those in proj_clean)."""
    return _py_files(project / "proj_clean")


def test_files(project: Path) -> list[str]:
    src = set(source_files(project))
    return [f for f in _py_files(project / "proj_with_test") if f not in src]


def _copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if n in SKIP_DIRS])


def _count(xml_path: Path) -> dict:
    if not xml_path.exists():
        return {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "total": 0, "cases": {}}
    root = ET.parse(xml_path).getroot()
    cases = {}
    for tc in root.iter("testcase"):
        name = f"{tc.get('classname', '')}::{tc.get('name', '')}"
        if tc.find("failure") is not None:
            cases[name] = "failed"
        elif tc.find("error") is not None:
            cases[name] = "error"
        elif tc.find("skipped") is not None:
            cases[name] = "skipped"
        else:
            cases[name] = "passed"
    vals = list(cases.values())
    return {"passed": vals.count("passed"), "failed": vals.count("failed"), "errors": vals.count("error"),
            "skipped": vals.count("skipped"), "total": len(vals), "cases": cases}


def run_tests(project: Path, candidate: dict[str, str] | None = None, python: str = sys.executable,
              timeout_per_test: int = 60, timeout_total: int = 900) -> dict:
    """``candidate`` maps relative paths to code. ``None`` scores the reference code."""
    project = Path(project)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "proj"
        _copy_tree(project / "proj_with_test", work)
        if candidate is not None:
            for rel in source_files(project):
                f = work / rel
                # empty files (e.g. bare __init__.py) carry no code, so they stay
                if f.exists() and f.read_text(encoding="utf-8", errors="ignore").strip():
                    f.unlink()
            for rel, code in candidate.items():
                f = work / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(code, encoding="utf-8")
        xml = Path(tmp) / "junit.xml"
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(work), str(work / "src")]),
                   MPLBACKEND="Agg", PYTHONDONTWRITEBYTECODE="1")
        env.pop("DISPLAY", None)
        cmd = [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--timeout={timeout_per_test}",
               f"--junitxml={xml}", *test_files(project)]
        try:
            proc = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=timeout_total)
            tail = (proc.stdout + proc.stderr)[-2000:]
        except subprocess.TimeoutExpired:
            tail = "TIMEOUT"
        res = _count(xml)
        res["log_tail"] = tail
        return res
