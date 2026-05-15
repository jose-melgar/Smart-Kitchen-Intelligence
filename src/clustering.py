import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
import os
import warnings

warnings.filterwarnings('ignore')

def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error: El archivo {filepath} no existe. Ejecute reduction.py primero.")
    return np.load(filepath)

def evaluate_kmeans(X):
    print("\n--- Ejecutando Paradigma de Centroides (K-Means) ---")
    best_k = 2
    best_silhouette = -1
    best_inertia = None
    best_labels = None

    for k in range(2, 11):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        silhouette = silhouette_score(X, labels)

        print(f"  -> Probando K-Means (k={k}): Silhouette = {silhouette:.4f} | Inercia = {kmeans.inertia_:.2f}")
        
        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_k = k
            best_inertia = kmeans.inertia_
            best_labels = labels

    print(f"Resumen K-Means: Mejor configuración encontrada para k={best_k}. Silhouette: {best_silhouette:.4f}, Inercia: {best_inertia:.2f}")
    
    return {
        "Paradigma": "K-Means", 
        "Hiperparámetros": f"k={best_k}", 
        "Silhouette_Score": best_silhouette, 
        "Métrica_Específica": f"Inercia: {best_inertia:.2f}", 
        "labels": best_labels
    }

def evaluate_dbscan(X):
    print("\n--- Ejecutando Paradigma de Densidad (DBSCAN) ---")
    best_eps = 0.5
    best_min_samples = 5
    best_silhouette = -1
    best_noise_ratio = 1.0
    best_labels = None
    best_n_clusters = 0

    eps_values = np.arange(0.5, 3.5, 0.5)
    min_samples_values = [15, 30, 45, 60]

    for eps in eps_values:
        for min_samples in min_samples_values:
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            labels = dbscan.fit_predict(X)
            
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            noise_ratio = np.sum(labels == -1) / len(labels)
            
            if n_clusters > 1 and noise_ratio < 0.6:
                silhouette = silhouette_score(X, labels)

                print(f"  -> Probando DBSCAN (eps={eps}, min={min_samples}): Clusters={n_clusters} | Ruido={noise_ratio*100:.2f}% | Silhouette={silhouette:.4f}")

                if silhouette > best_silhouette:
                    best_silhouette = silhouette
                    best_eps = eps
                    best_min_samples = min_samples
                    best_noise_ratio = noise_ratio
                    best_labels = labels
                    best_n_clusters = n_clusters
            else:
                print(f"  -> Probando DBSCAN (eps={eps}, min={min_samples}): [DESCARTADO] Clusters={n_clusters} | Ruido={noise_ratio*100:.2f}%")

    if best_silhouette == -1:
         print("Resumen DBSCAN: El algoritmo no logró formar clusters consistentes o el nivel de ruido fue superior al 60%.")
         return {
             "Paradigma": "DBSCAN", 
             "Hiperparámetros": "N/A", 
             "Silhouette_Score": -1, 
             "Métrica_Específica": "Ruido: >60%", 
             "labels": None
         }

    print(f"Resumen DBSCAN: Mejor configuración eps={best_eps}, min_pts={best_min_samples}. Clusters: {best_n_clusters}, Ruido: {best_noise_ratio*100:.2f}%, Silhouette: {best_silhouette:.4f}")
    
    return {
        "Paradigma": "DBSCAN", 
        "Hiperparámetros": f"eps={best_eps}, min_pts={best_min_samples}", 
        "Silhouette_Score": best_silhouette, 
        "Métrica_Específica": f"Ruido: {best_noise_ratio*100:.2f}%", 
        "labels": best_labels
    }

def evaluate_gmm(X):
    print("\n--- Ejecutando Paradigma Probabilístico (GMM) ---")
    best_n = 2
    best_silhouette = -1
    best_bic = float('inf')
    best_labels = None

    for n in range(2, 11):
        gmm = GaussianMixture(n_components=n, random_state=42, covariance_type='full')
        labels = gmm.fit_predict(X)
        bic = gmm.bic(X)
        silhouette = silhouette_score(X, labels)

        print(f"  -> Probando GMM (componentes={n}): Silhouette = {silhouette:.4f} | BIC = {bic:.2f}")
        
        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_n = n
            best_bic = bic
            best_labels = labels

    print(f"Resumen GMM: Mejor configuración componentes={best_n}. Silhouette: {best_silhouette:.4f}, BIC: {best_bic:.2f}")
    
    return {
        "Paradigma": "GMM", 
        "Hiperparámetros": f"components={best_n}", 
        "Silhouette_Score": best_silhouette, 
        "Métrica_Específica": f"BIC: {best_bic:.2f}", 
        "labels": best_labels
    }

def main():
    print("Iniciando Pipeline de Experimentación y Validación (Hito 3)")
    matrix_path = "data/features/feature_matrix_reduced.npy"
    
    try:
        X = load_data(matrix_path)
    except FileNotFoundError as e:
        print(e)
        return

    print(f"Matriz de datos cargada. Dimensiones operativas: {X.shape}")

    res_kmeans = evaluate_kmeans(X)
    res_dbscan = evaluate_dbscan(X)
    res_gmm = evaluate_gmm(X)

    resultados = [res_kmeans, res_dbscan, res_gmm]
    df_resultados = pd.DataFrame(resultados).drop(columns=['labels'])
    
    print("\n=========================================================================================")
    print("                        CUADRO COMPARATIVO DE PARADIGMAS DE CLUSTERING                   ")
    print("=========================================================================================")
    print(df_resultados.to_string(index=False, justify='center'))
    print("=========================================================================================\n")

    ganador = max(resultados, key=lambda x: x['Silhouette_Score'])
    
    print(">>> DECLARACIÓN DEL MODELO GANADOR <<<")
    if ganador['Silhouette_Score'] == -1:
         print("Error crítico: Ningún paradigma logró segmentar los datos de forma estadísticamente significativa.")
    else:
        print(f"El modelo ganador para la implementación es: {ganador['Paradigma']}")
        print(f"Justificación Técnica: Presentó el mayor coeficiente de Silhouette ({ganador['Silhouette_Score']:.4f}).")
        print("Esto indica la mejor relación matemática entre la cohesión interna de los grupos y la separación externa frente a otros clusters de comportamiento alimentario.")
        
        output_dir = "data/features"
        os.makedirs(output_dir, exist_ok=True)
        np.save(f"{output_dir}/cluster_labels.npy", ganador['labels'])
        print(f"Las etiquetas generadas han sido guardadas en '{output_dir}/cluster_labels.npy' para el análisis de perfilamiento.")

if __name__ == "__main__":
    main()