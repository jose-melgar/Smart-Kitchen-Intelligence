"""
Módulo de Analítica de Grafos y Centralidad (Hito 5)
Este script analiza la topología del grafo de la cocina,
calculando grados ponderados y la centralidad de PageRank.
"""

import networkx as nx
import json
import os

def analyze_kitchen_graph(graph_path, output_metrics_path):
    print(f"Cargando grafo desde: {graph_path}")
    G = nx.read_gexf(graph_path)
    
    print("Ejecutando cálculos de topología y centralidad...")
    
    # 1. Componentes conectadas
    # Permite saber si hay productos totalmente aislados
    components = list(nx.connected_components(G))
    num_components = len(components)
    largest_component_size = len(max(components, key=len)) if num_components > 0 else 0
    
    # 2. Cálculos de Grado
    degrees = dict(G.degree())
    weighted_degrees = dict(G.degree(weight='weight'))
    
    # 3. Cálculo de PageRank (Ponderado por las frecuencias de compra cruzada)
    pagerank = nx.pagerank(G, weight='weight')
    
    # Estructurar las métricas a exportar
    metrics = {
        "network_overview": {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "connected_components": num_components,
            "largest_component_size": largest_component_size
        },
        "top_10_pagerank": sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10],
        "top_10_weighted_degree": sorted(weighted_degrees.items(), key=lambda x: x[1], reverse=True)[:10],
        "node_metrics": {}
    }
    
    # Consolidar métricas por cada nodo (producto)
    for node in G.nodes():
        metrics["node_metrics"][node] = {
            "degree": degrees[node],
            "weighted_degree": weighted_degrees.get(node, 0),
            "pagerank": pagerank.get(node, 0)
        }
        
    # Exportar resultados
    os.makedirs(os.path.dirname(output_metrics_path), exist_ok=True)
    with open(output_metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)
        
    print("-" * 40)
    print("Análisis de Grafo Completado")
    print(f"Componentes Conectadas: {num_components}")
    print(f"Métricas exportadas en: {output_metrics_path}")
    print("\nTop 3 Productos Centrales (PageRank):")
    for i, (prod, pr) in enumerate(metrics["top_10_pagerank"][:3]):
        print(f" {i+1}. Producto ID {prod} -> PR Score: {pr:.4f}")
    print("-" * 40)

if __name__ == "__main__":
    # Definición de rutas
    GRAPH_INPUT = "data/recommender/kitchen_graph.gexf"
    METRICS_OUTPUT = "data/recommender/graph_metrics.json"
    
    analyze_kitchen_graph(GRAPH_INPUT, METRICS_OUTPUT)