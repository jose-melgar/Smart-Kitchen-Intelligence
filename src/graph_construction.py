"""
Módulo de Construcción de Grafos (Hito 5)
Utiliza la matriz dispersa R para construir un grafo exacto 
mediante la multiplicación de R transpuesta por R.
"""

import scipy.sparse as sp
import networkx as nx
import pandas as pd
import os

def build_cooccurrence_graph():
    R_path = "data/recommender/R_restock_bin.npz"
    catalog_path = "data/recommender/product_catalog.csv"
    out_path = "data/recommender/kitchen_graph.gexf"
    
    print("Cargando matriz de interacciones y catálogo...")
    # R tiene tamaño (1177 sesiones, 50 productos)
    R = sp.load_npz(R_path)
    catalog = pd.read_csv(catalog_path)
    product_ids = catalog["product_id"].tolist()
    
    print("Calculando co-ocurrencia matemática (R^T @ R)...")
    # Multiplicación matricial: da una matriz de (50, 50)
    adjacency = (R.T @ R).toarray()
    
    G = nx.Graph()
    n_products = adjacency.shape[0]
    
    print("Construyendo red de productos...")
    # 1. Añadir los 50 nodos con su ID real de catálogo
    for i in range(n_products):
        G.add_node(str(product_ids[i]))
        
    # 2. Añadir aristas basadas en co-ocurrencia
    for i in range(n_products):
        for j in range(i + 1, n_products): # i < j evita contar la diagonal y duplicados
            weight = adjacency[i, j]
            if weight > 0: # Solo si se compraron juntos alguna vez
                G.add_edge(str(product_ids[i]), str(product_ids[j]), weight=int(weight))
                
    # Guardar el grafo procesado
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    nx.write_gexf(G, out_path)
    
    print("-" * 40)
    print("Construcción del Grafo Completada")
    print(f"Total de Nodos (Productos): {G.number_of_nodes()}")
    print(f"Total de Aristas (Relaciones): {G.number_of_edges()}")
    print(f"Grafo exportado exitosamente en: {out_path}")
    print("-" * 40)

if __name__ == "__main__":
    build_cooccurrence_graph()