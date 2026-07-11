"""
Test unitario de `analyze_kitchen_graph` en `src/graph_analytics.py`.
Construye un grafo de co-ocurrencia sintetico pequeno (no el real de 50
productos), lo exporta a GEXF y verifica el contrato de la funcion: que
metricas calcula, con que forma, y que las propiedades matematicas basicas
de PageRank y de componentes conexas se cumplan.
"""

from __future__ import annotations

import json

import networkx as nx
import pytest

from graph_analytics import analyze_kitchen_graph


@pytest.fixture
def toy_graph_path(tmp_path):
    G = nx.Graph()
    G.add_weighted_edges_from([
        ("A", "B", 10.0),
        ("B", "C", 1.0),
        # "D" queda desconectado a proposito -> debe verse en connected_components
    ])
    G.add_node("D")
    path = tmp_path / "toy_graph.gexf"
    nx.write_gexf(G, path)
    return path


def test_analyze_kitchen_graph_detects_disconnected_component(toy_graph_path, tmp_path):
    out_path = tmp_path / "out" / "metrics.json"
    analyze_kitchen_graph(str(toy_graph_path), str(out_path))

    assert out_path.exists()
    with open(out_path, encoding="utf-8") as f:
        metrics = json.load(f)

    overview = metrics["network_overview"]
    assert overview["num_nodes"] == 4
    assert overview["num_edges"] == 2
    # A-B-C conectados + D aislado = 2 componentes.
    assert overview["connected_components"] == 2
    assert overview["largest_component_size"] == 3


def test_analyze_kitchen_graph_pagerank_sums_to_approximately_one(toy_graph_path, tmp_path):
    out_path = tmp_path / "metrics.json"
    analyze_kitchen_graph(str(toy_graph_path), str(out_path))
    with open(out_path, encoding="utf-8") as f:
        metrics = json.load(f)

    pagerank_values = [m["pagerank"] for m in metrics["node_metrics"].values()]
    # PageRank es una distribucion de probabilidad sobre los nodos.
    assert sum(pagerank_values) == pytest.approx(1.0, abs=1e-6)
    assert all(v >= 0 for v in pagerank_values)


def test_analyze_kitchen_graph_weighted_degree_reflects_edge_weights(toy_graph_path, tmp_path):
    out_path = tmp_path / "metrics.json"
    analyze_kitchen_graph(str(toy_graph_path), str(out_path))
    with open(out_path, encoding="utf-8") as f:
        metrics = json.load(f)

    node_metrics = metrics["node_metrics"]
    # B esta conectado a A (peso 10) y C (peso 1) -> grado ponderado = 11.
    assert node_metrics["B"]["weighted_degree"] == pytest.approx(11.0)
    # D esta aislado -> grado simple y ponderado = 0.
    assert node_metrics["D"]["degree"] == 0
    assert node_metrics["D"]["weighted_degree"] == 0
