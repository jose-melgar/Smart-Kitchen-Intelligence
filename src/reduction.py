import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import os
import json

def run_dimensionality_reduction():
    print("Iniciando Análisis de Reducción y Visualización (PCA & t-SNE)...")

    # 1. Carga de datos
    matrix_path = "data/features/feature_matrix.npy"
    names_path = "data/features/feature_names.json"
    metadata_path = "data/processed/inventory_v1.csv"

    if not os.path.exists(matrix_path):
        print(f"Error: No se encontró {matrix_path}")
        return

    X = np.load(matrix_path)
    with open(names_path, "r") as f:
        feature_names = json.load(f)
        
    df_meta = pd.read_csv(metadata_path)

    # ==========================================
    # PUNTO 2: COMPRESIÓN TÉCNICA (PCA / SVD)
    # ==========================================
    pca_full = PCA()
    pca_full.fit(X)

    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    n_90 = np.argmax(cumulative_variance >= 0.90) + 1

    print("\n--- TABLA DE ENERGÍA RETENIDA (SVD / PCA) ---")
    print(f"Dimensión original (Densa): {X.shape[1]} características")
    print(f"Componentes para retener 90% de información: {n_90}\n")
    print("| Componente | Varianza Explicada | Varianza Acumulada |")
    print("| :--- | :--- | :--- |")
    for i in range(min(5, X.shape[1])):
        print(f"| PC{i+1} | {pca_full.explained_variance_ratio_[i]*100:.2f}% | {cumulative_variance[i]*100:.2f}% |")
    print("-------------------------------------------------------")

    # Guardar el dataset comprimido para la Semana 7 (Clustering)
    pca_final = PCA(n_components=n_90)
    X_reduced = pca_final.fit_transform(X)
    np.save("data/features/feature_matrix_reduced.npy", X_reduced)
    print("✅ Dataset reducido (Single Source of Truth) guardado exitosamente.")

    # ==========================================
    # PUNTO 4: VISUALIZACIONES E INTERPRETACIÓN
    # ==========================================
    os.makedirs("reports/figures", exist_ok=True)

    # Gráfico 1: Scree Plot (Error de Reconstrucción)
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, marker='o', linestyle='--', color='b', markersize=4)
    plt.axhline(y=0.90, color='r', linestyle='-', label='Umbral 90% Energía')
    plt.axvline(x=n_90, color='r', linestyle='--')
    plt.title('Scree Plot: Energía Retenida vs Dimensionalidad')
    plt.xlabel('Número de Componentes Principales')
    plt.ylabel('Varianza Acumulada')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("reports/figures/pca_scree_plot.png", dpi=300, bbox_inches='tight')
    plt.close()

    # Gráfico 2: t-SNE (Topología No Lineal para visualizar Clusters)
    print("Calculando t-SNE para visualización... (esto tomará unos segundos)")
    tsne = TSNE(n_components=2, perplexity=30, random_state=42)
    # Por eficiencia computacional, aplicamos t-SNE sobre los datos ya limpios de ruido (PCA 90%)
    X_tsne = tsne.fit_transform(X_reduced) 

    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        x=X_tsne[:, 0], y=X_tsne[:, 1],
        hue=df_meta['event_type'], 
        palette="magma", alpha=0.6, s=15, edgecolor=None
    )
    plt.title('t-SNE: Mapa Topológico de Comportamiento de Inventario (Perplexity=30)')
    plt.xlabel('Dimensión t-SNE 1')
    plt.ylabel('Dimensión t-SNE 2')
    plt.legend(title='Tipo de Evento')
    plt.savefig("reports/figures/tsne_clusters.png", dpi=300, bbox_inches='tight')
    plt.close()

    # Gráfico 3: PCA Biplot (Interpretación de Variables)
    pca_2d = PCA(n_components=2)
    X_pca_2d = pca_2d.fit_transform(X)
    loadings = pca_2d.components_.T * np.sqrt(pca_2d.explained_variance_)

    plt.figure(figsize=(12, 10))
    sns.scatterplot(x=X_pca_2d[:, 0], y=X_pca_2d[:, 1], color='lightgray', alpha=0.3, s=10)
    
    # Extraemos las 6 variables más importantes para dibujarlas
    top_features_idx = np.argsort(np.linalg.norm(loadings, axis=1))[-6:]
    for i in top_features_idx:
        plt.arrow(0, 0, loadings[i, 0]*4, loadings[i, 1]*4, color='darkred', alpha=0.8, head_width=0.08)
        plt.text(loadings[i, 0]*4.2, loadings[i, 1]*4.2, feature_names[i], color='black', fontsize=10, weight='bold')

    plt.title('PCA Biplot: Impacto de Variables Originales (Vectores)')
    plt.xlabel(f'PC1 ({pca_2d.explained_variance_ratio_[0]*100:.1f}%)')
    plt.ylabel(f'PC2 ({pca_2d.explained_variance_ratio_[1]*100:.1f}%)')
    plt.grid(True, alpha=0.3)
    plt.savefig("reports/figures/pca_biplot.png", dpi=300, bbox_inches='tight')
    plt.close()

    print("\n✅ Reporte de Reducción Finalizado.")
    print("📁 Figuras guardadas: Scree Plot, t-SNE Clusters, y PCA Biplot en 'reports/figures/'")

if __name__ == "__main__":
    run_dimensionality_reduction()