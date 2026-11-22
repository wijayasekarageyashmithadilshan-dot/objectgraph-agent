import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from objectgraph.uml import parse_class_diagram, method_name  # noqa: E402
from objectgraph.graph import build_duty_graph               # noqa: E402
from objectgraph.criterion import (mq, cut_weight, select_k,   # noqa: E402
                                   expected_random_cut)

DIAGRAM = """
```mermaid
classDiagram
  class Cart {
    +add(item Product)
    +total() float
  }
  class Product {
    -price float
  }
  class Order {
    +place(cart Cart)
    +cancel()
  }
  class Payment {
    +charge(order Order)
    +refund(order Order)
  }
  Order --> Cart : uses
  Payment --> Order : uses
  Product "1" -- "0..*" Cart
```
"""


def test_method_name_styles():
    assert method_name("+vector~VertexType~ bfs(VertexType)") == "bfs"
    assert method_name("+parse_args() ArgumentParser") == "parse_args"
    assert method_name("output_json(json_struct, json_filepath)") == "output_json"


def test_parse_counts():
    d = parse_class_diagram(DIAGRAM)
    assert set(d.classes) == {"Cart", "Product", "Order", "Payment"}
    assert d.classes["Payment"].method_names() == ["charge", "refund"]
    assert len(d.relations) == 3


def test_graph_symmetric_and_normalised():
    g = build_duty_graph(parse_class_diagram(DIAGRAM))
    assert g.n == 7  # 2 + 1 state duty + 2 + 2
    assert np.allclose(g.W, g.W.T)
    assert np.isclose(g.W.max(), 1.0)
    assert np.all(np.diag(g.W) == 0)


def test_mq_two_cliques():
    W = np.zeros((6, 6))
    for block in ([0, 1, 2], [3, 4, 5]):
        for i, j in itertools.combinations(block, 2):
            W[i, j] = W[j, i] = 1
    W[2, 3] = W[3, 2] = 0.1
    k, lab, curve = select_k(W)
    assert k == 2
    assert len(set(lab[:3])) == 1 and len(set(lab[3:])) == 1
    assert curve[2] > curve[1] and curve[2] > curve[3]
    assert np.isclose(cut_weight(W, lab), 0.1)


def test_closed_form_matches_sampling():
    rng = np.random.default_rng(0)
    A = rng.random((12, 12))
    W = np.triu(A, 1)
    W = W + W.T
    labels = np.array([0] * 5 + [1] * 4 + [2] * 3)
    draws = [cut_weight(W, rng.permutation(labels)) for _ in range(4000)]
    assert abs(np.mean(draws) - expected_random_cut(W, [5, 4, 3])) / np.mean(draws) < 0.01


def test_single_class_gives_one_agent():
    W = np.ones((4, 4)) - np.eye(4)
    assert select_k(W)[0] == 1
    assert np.isclose(mq(W, np.zeros(4, dtype=int)), 12 / 16)
