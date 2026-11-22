import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from objectgraph.llm import LLM, CacheMiss, BudgetExceeded            # noqa: E402
from objectgraph.orchestrator import merge_fragments, parse_blocks   # noqa: E402
from objectgraph.uml import parse_class_diagram                      # noqa: E402
from objectgraph.graph import build_duty_graph                       # noqa: E402
from objectgraph.criterion import select_k                           # noqa: E402
from objectgraph.team import build_team                              # noqa: E402
from tests.test_criterion import DIAGRAM                             # noqa: E402


def test_cache_records_and_replays(tmp_path):
    calls = []
    llm = LLM("fake", "m", tmp_path, fake_fn=lambda s, u: calls.append(u) or f"reply to {u}")
    assert llm.call("sys", "hello", tag="a") == "reply to hello"
    replay = LLM("fake", "m", tmp_path, offline=True)
    assert replay.call("sys", "hello", tag="a") == "reply to hello"
    assert replay.usage.cached_calls == 1 and len(calls) == 1
    with pytest.raises(CacheMiss):
        replay.call("sys", "new prompt")


def test_run_id_separates_repeats(tmp_path):
    llm = LLM("fake", "m", tmp_path, fake_fn=lambda s, u: "x")
    assert llm.key("s", "u", 0) != llm.key("s", "u", 1)


def test_budget(tmp_path):
    llm = LLM("fake", "m", tmp_path, token_budget=1, fake_fn=lambda s, u: "x" * 100)
    llm.call("s", "u")
    with pytest.raises(BudgetExceeded):
        llm.call("s", "u2")


def test_parse_and_merge_python():
    text = "### FILE: pkg/a.py\n```python\nimport os\nclass A:\n    pass\n```\n"
    assert parse_blocks(text) == [("pkg/a.py", "import os\nclass A:\n    pass\n")]
    merged = merge_fragments("pkg/a.py", ["import os\nclass A:\n    pass\n",
                                          "import os\nimport re\nclass B(A):\n    pass\n"])
    assert merged.count("import os") == 1
    assert merged.index("class A") < merged.index("class B")


def test_team_owns_every_duty_once():
    d = parse_class_diagram(DIAGRAM)
    g = build_duty_graph(d)
    k, lab, _ = select_k(g.W)
    team = build_team("criterion", lab, g, d)
    owned = [x for a in team.agents for x in a.duties]
    assert sorted(owned) == sorted(g.duties)
    assert set(team.order) == {a.agent_id for a in team.agents}
    # Payment uses Order, so Payment's agent may not run before Order's agent
    owner = {c: a.agent_id for a in team.agents for c in a.classes}
    if owner["Payment"] != owner["Order"]:
        assert team.order.index(owner["Order"]) < team.order.index(owner["Payment"])


def test_parsers_for_devbench_runners(tmp_path):
    from objectgraph.testparse import counts, junit_counts, strip_reporting
    g = "[==========] 7 tests ran.\n[  PASSED  ] 5 tests.\n[  FAILED  ] 2 tests, listed below:\n"
    assert counts(g)["passed"] == 5 and counts(g)["failed"] == 2
    sh = "Test 0: [PASSED]. ok\nTest 1: [FAILED]. no\nTest 2: [PASSED]."
    assert counts(sh)["passed"] == 2 and counts(sh)["failed"] == 1
    js = "Tests:       1 failed, 4 passed, 5 total"
    assert counts(js)["passed"] == 4 and counts(js)["failed"] == 1
    d = tmp_path / "build" / "test-results" / "test"
    d.mkdir(parents=True)
    (d / "TEST-x.xml").write_text('<testsuite tests="3" failures="1" errors="0" skipped="0"></testsuite>')
    assert junit_counts(tmp_path / "build") == {"passed": 2, "failed": 1, "errors": 0, "skipped": 0}
    assert strip_reporting("make test -f makefile_test; make coverage -f makefile_test") == "make test -f makefile_test"


def test_conditions_cover_every_duty_and_random_differs():
    from objectgraph.conditions import build_conditions, same_partition
    g = build_duty_graph(parse_class_diagram(DIAGRAM))
    c = build_conditions(g)
    for name in ("G2", "G4", "GC", "G6", "G7"):
        assert len(c[name]["labels"]) == g.n
    assert not same_partition(c["G4"]["labels"], c["G7"]["labels"]) or c["_meta"]["k_star"] == 1
