from objectgraph.orchestrator import merge_fragments


def test_base_class_first_and_owner_version_kept():
    sub = "class PnF(Instrument):\n    def a(self):\n        return 1\n"
    stub = "class Instrument:\n    pass\n"
    owner = "import os\nclass Instrument:\n    def __init__(self, df):\n        self.df = df\n"
    m = merge_fragments("p/x.py", [sub, stub, owner], [{"PnF"}, {"Renko"}, {"Instrument"}])
    assert m.index("class Instrument") < m.index("class PnF")
    assert m.count("class Instrument") == 1 and "self.df = df" in m
    ns = {}
    exec(compile(m, "m", "exec"), ns)
    assert issubclass(ns["PnF"], ns["Instrument"])


def test_unparsable_fragment_falls_back_to_concatenation():
    m = merge_fragments("p/x.py", ["import os\nx = 1\n", "def broken(:\n"])
    assert "import os" in m and "def broken(:" in m
