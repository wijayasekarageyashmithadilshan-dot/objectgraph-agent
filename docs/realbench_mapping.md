# RealBench → duty graph mapping

RealBench (arXiv 2604.22659) gives each of its 61 Python projects a class
diagram as JSON (`uml_output/<project>_uml.json`, generated with SciTools
Understand) and a file-level import DAG (`dag.json`). `objectgraph/realbench.py`
turns them into the same `ClassDiagram` the Mermaid parser produces, so the
duty graph, the criterion and every baseline run unchanged.

| RealBench element | Duty-graph element |
|---|---|
| class + its methods | one unit; each method is a duty (member-less class → one `<state>` duty) |
| module-level functions of a file | one pseudo-unit `mod_<file>`; each function is a duty (main "full" view only) |
| class `relationships` (all `dependency`) to a declared class | weak relation (0.25) |
| relationship to an undeclared type (`int`, library classes) | ignored, as for DevBench |
| parameter / return type naming a declared class | signature edge (0.5), found by `build_duty_graph` |
| `dag.json` edge A → B | weak relation between every unit of file A and every unit of file B |
| class name declared in two files | qualified as `<file>_<Class>` |

RealBench diagrams contain no inheritance, composition or aggregation, so the
strong weight (0.5) is never used. This is a property of the data.

Two views are reported: **full** (classes + module functions; the whole design
a team must write) and **classes** (classes only; comparable to DevBench).

Run (zero model calls):

    python scripts/run_realbench_structural.py --root <projs_filtered_uml> --out results

The RealBench data and the per-project team lists are not redistributed here
(no licence is stated in the RealBench release); only the per-project counts in
`results/realbench_table.csv` are committed.
