from objectgraph.orchestrator import merge_fragments


def test_base_class_first_and_owner_version_kept():
    sub = "class PnF(Instrument):\n    def a(self):\n        return 1\n"
    stub = "class Instrument:\n    pass\n"
    owner = "import os\nclass Instrument:\n    def __init__(self, df):\n        self.df = df\n"
    m = merge_fragments("p/x.py", [sub, stub, owner], [{"PnF.a"}, {"Renko.x"}, {"Instrument.__init__"}])
    assert m.index("class Instrument") < m.index("class PnF")
    assert m.count("class Instrument") == 1 and "self.df = df" in m
    ns = {}
    exec(compile(m, "m", "exec"), ns)
    assert issubclass(ns["PnF"], ns["Instrument"])


def test_unparsable_fragment_falls_back_to_concatenation():
    m = merge_fragments("p/x.py", ["import os\nx = 1\n", "def broken(:\n"])
    assert "import os" in m and "def broken(:" in m


def test_bare_duty_marker_becomes_comment():
    from objectgraph.orchestrator import fix_duty_markers
    code = "class Renko:\n    duty: Renko.get_ohlc_data\n    def get_ohlc_data(self):\n        return 1  # duty: keep\n"
    fixed = fix_duty_markers("s/indicators.py", code)
    assert "    # duty: Renko.get_ohlc_data" in fixed
    exec(compile(fixed, "m", "exec"), {})
    assert fix_duty_markers("A.java", "  duty: A.b\n") == "  // duty: A.b\n"


def test_class_split_across_agents_keeps_every_method():
    a = "class C:\n    X = 1\n    # duty: C.f\n    def f(self):\n        return 'f'\n    def g(self):\n        raise NotImplementedError\n"
    b = "class C:\n    def g(self):\n        return 'g'\n"
    m = merge_fragments("p/x.py", [a, b], [{"C.f"}, {"C.g"}])
    ns = {}
    exec(compile(m, "m", "exec"), ns)
    c = ns["C"]()
    assert c.f() == "f" and c.g() == "g" and ns["C"].X == 1 and "# duty: C.f" in m


def test_merge_v2_orders_by_import_time_need_and_keeps_properties():
    import objectgraph.orchestrator as o
    o.MERGE_V2 = True
    try:
        a = "from typing import List\ndef f() -> List[B]:\n    return []\nclass T:\n    @property\n    def c(self):\n        return self._c\n\n    @c.setter\n    def c(self, v):\n        self._c = v\n"
        b = "class B:\n    TEXT = '''x\ny'''\n"
        out = o.merge_fragments("m.py", [a, b], [{"mod_m.f", "T.c"}, {"B.<state>"}])
        assert out.index("class B") < out.index("def f(")
        assert "@c.setter" in out and "TEXT = '''x\ny'''" in out
        ns = {}
        exec(out, ns)
    finally:
        o.MERGE_V2 = False


def test_block_ends_only_at_fence_line():
    from objectgraph.orchestrator import parse_blocks
    text = '### FILE: a.py\n```python\ndef f():\n    """Use ```code``` here."""\n    return 1\n```\n'
    (path, code), = parse_blocks(text)
    assert path == "a.py" and "return 1" in code
