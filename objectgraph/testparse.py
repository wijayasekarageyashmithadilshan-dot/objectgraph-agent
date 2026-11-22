"""Count passed/failed tests from the output of the test runners DevBench uses."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


def counts(output: str) -> dict:
    c = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    # pytest: "==== 3 passed, 1 failed in 0.12s ===="
    for m in re.finditer(r"=+ (.*?) in [\d.]+s", output):
        for n, kind in re.findall(r"(\d+) (passed|failed|errors?|skipped)", m.group(1)):
            c["errors" if kind.startswith("error") else kind] += int(n)
    # unittest: "Ran 5 tests" + "FAILED (failures=1, errors=1)"
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
    # GoogleTest: "[  PASSED  ] 7 tests." and "[  FAILED  ] 2 tests, listed below:"
    for n in re.findall(r"\[\s+PASSED\s+\]\s+(\d+) tests?", output):
        c["passed"] += int(n)
    for n in re.findall(r"\[\s+FAILED\s+\]\s+(\d+) tests?,", output):
        c["failed"] += int(n)
    # DevBench shell acceptance scripts: "Test 3: [PASSED]" / "[FAILED]"
    if not re.search(r"\[\s+PASSED\s+\]\s+\d+ tests?", output):
        c["passed"] += len(re.findall(r"\[PASSED\]", output))
        c["failed"] += len(re.findall(r"\[FAILED\]", output))
    # Jest: "Tests:       1 failed, 4 passed, 5 total"
    for line in re.findall(r"^Tests:\s+(.*)$", output, flags=re.M):
        for n, kind in re.findall(r"(\d+) (passed|failed|skipped)", line):
            c[kind] += int(n)
    return c


def junit_counts(root: Path) -> dict:
    """Gradle/Maven JUnit XML reports under build/test-results/."""
    c = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for f in Path(root).rglob("TEST-*.xml"):
        try:
            s = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        t, fl, er, sk = (int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped"))
        c["failed"] += fl
        c["errors"] += er
        c["skipped"] += sk
        c["passed"] += t - fl - er - sk
    return c


def strip_reporting(cmd: str) -> str:
    """Drop coverage/JSON-report flags and coverage make targets: they measure
    coverage, not correctness."""
    cmd = re.sub(r"--cov\S*", "", cmd)
    cmd = re.sub(r"--json-report\S*", "", cmd)
    cmd = re.sub(r";\s*make coverage[^;]*", "", cmd)
    return re.sub(r"\s+", " ", cmd).strip()
