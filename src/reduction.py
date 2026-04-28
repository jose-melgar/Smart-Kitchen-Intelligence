import numpy as np
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
import os
import json

def run_dimensionality_reduction():
    print("Iniciando Análisis de Reducción de Dimensionalidad (PCA)...")

    # 1. Carga de artefactos
    matrix_path = "data/features/feature_matrix.npy"
    names_path = "data/features/feature_names.json"
    metadata_path = "data/processed/inventory_v1.csv"

    if not os.path.exists(matrix_path):
        print(f"Error: No se encontró {matrix_path}")
        return

    X = np.load(matrix_path)
    
    # Cargamos el dataset original para usar sus etiquetas (categorías/eventos) en los gráficos
    df_meta = pl.read_csv(metadata_path).to_pandas()

    # ==========================================
    # PUNTO 2: APLICACIÓN DEL ALGORITMO (PCA)
    # ==========================================
    # Calculamos todos los componentes para analizar la energía retenida
    pca_full = PCA()
    pca_full.fit(X)

    cumulative_variance = np.cumsum(pca_full.explained_variance_ratio_)
    
    # Calculamos el número óptimo de componentes para retener el 90% de la información
    n_90 = np.argmax(cumulative_variance >= 0.90) + 1

    # ==========================================
    # PUNTO 3: TABLA COMPARATIVA (Retained Energy)
    # ==========================================
    print("\n--- TABLA DE VARIANZA EXPLICADA (Top 5 Componentes) ---")
    print(f"Dimensión original: {X.shape[1]} características")
    print(f"Componentes para retener 90% de información: {n_90}\n")
    print("| Componente | Varianza Explicada | Varianza Acumulada |")
    print("| :--- | :--- | :--- |")
    for i in range(5):
        print(f"| PC{i+1} | {pca_full.explained_variance_ratio_[i]*100:.2f}% | {cumulative_variance[i]*100:.2f}% |")
    print("-------------------------------------------------------")

    # ==========================================
    # PUNTO 4: SET DE VISUALIZACIONES
    # ==========================================
    os.makedirs("reports/figures", exist_ok=True)

    # Gráfico A: Scree Plot (El "Codo" de la varianza)
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(cumulative_variance) + 1), cumulative_variance, marker='o', linestyle='--', color='b', markersize=4)
    plt.axhline(y=0.90, color='r', linestyle='-', label='Umbral 90% Información')
    plt.axvline(x=n_90, color='r', linestyle='--')
    plt.title('Scree Plot: Varianza Acumulada vs Componentes (PCA)')
    plt.xlabel('Número de Componentes Principales')
    plt.ylabel('Varianza Acumulada (Energía Retenida)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig("reports/figures/pca_scree_plot.png", dpi=300, bbox_inches='tight')
    plt.close()

    # Gráfico B: Scatter Plot 2D de Agrupamiento
    # Reducimos estrictamente a 2 dimensiones para poder dibujarlo en un plano X-Y
    pca_2d = PCA(n_components=2)
    X_2d = pca_2d.fit_transform(X)

    plt.figure(figsize=(12, 8))
    # Coloreamos los puntos según el tipo de evento (IN/OUT) para ver si el comportamiento separa los datos
    sns.scatterplot(
        x=X_2d[:, 0], y=X_2d[:, 1],
        hue=df_meta['event_type'], 
        palette="viridis", alpha=0.6, edgecolor=None, s=15
    )
    plt.title('Proyección PCA 2D: Estructura Latente de Movimientos')
    plt.xlabel(f'Componente Principal 1 ({pca_2d.explained_variance_ratio_[0]*100:.1f}%)')
    plt.ylabel(f'Componente Principal 2 ({pca_2d.explained_variance_ratio_[1]*100:.1f}%)')
    plt.legend(title='Tipo de Evento')
    plt.savefig("reports/figures/pca_scatter_2d.png", dpi=300, bbox_inches='tight')
    plt.close()

    print("\n✅ Reporte de Reducción Finalizado.")
    print("📁 Visualizaciones guardadas en: 'reports/figures/'")

if __name__ == "__main__":
    run_dimensionality_reduction()