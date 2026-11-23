import json
from objectgraph.realbench import load_realbench
from objectgraph.graph import build_duty_graph


def test_loader_maps_classes_functions_and_edges(tmp_path):
    uml = {"modules": [
        {"name": "a.py", "functions": [{"name": "helper", "parameters": [{"name": "s", "type": "Store"}], "returnType": None}],
         "variables": [], "classes": [
            {"name": "Store", "attributes": [{"name": "items", "type": "list"}],
             "methods": [{"name": "add", "parameters": [{"name": "self", "type": "Any"}], "returnType": None},
                         {"name": "get", "parameters": [{"name": "self", "type": "Any"}], "returnType": "Item"}],
             "relationships": [{"type": "dependency", "source": "Store", "target": "Item"},
                               {"type": "dependency", "source": "Store", "target": "int"}]}]},
        {"name": "b.py", "functions": [], "variables": [], "classes": [
            {"name": "Item", "attributes": [], "methods": [], "relationships": []}]}]}
    dag = {"edges": [{"source": "a.py", "target": "b.py", "type": "dependency"}]}
    (tmp_path / "u.json").write_text(json.dumps(uml))
    (tmp_path / "dag.json").write_text(json.dumps(dag))
    d, s = load_realbench(tmp_path / "u.json", tmp_path / "dag.json")
    assert set(d.classes) == {"Store", "Item", "mod_a"}
    assert s["class_dependencies_kept"] == 1 and s["class_dependencies_external"] == 1
    assert s["file_edges"] == 1
    g = build_duty_graph(d)
    assert set(g.duties) == {"Store.add", "Store.get", "Item.<state>", "mod_a.helper"}
    i, j = g.duties.index("mod_a.helper"), g.duties.index("Store.add")
    assert g.W[i, j] > 0                         # signature reference + import edge
    d2, _ = load_realbench(tmp_path / "u.json", tmp_path / "dag.json", include_functions=False)
    assert "mod_a" not in d2.classes
