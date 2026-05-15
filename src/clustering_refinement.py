import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN, HDBSCAN
from sklearn.metrics import silhouette_score
import os
import warnings

warnings.filterwarnings('ignore')

def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error: El archivo {filepath} no existe.")
    return np.load(filepath)

def discard_gmm():
    print("\n--- Evaluando Paradigma Probabilístico (GMM) ---")
    print("Decisión: DESCARTADO.")
    print("Justificación: La experimentación previa demostró un Silhouette máximo de 0.19 y datos que no se ajustan a distribuciones gaussianas. No se requiere refinamiento adicional.")

def refine_kmeans(X):
    print("\n--- Refinamiento de Paradigma de Centroides (K-Means) ---")
    print("Objetivo: Evaluar si k=9 fue un máximo local o si existen mejores agrupaciones en k > 10.")
    best_k = 0
    best_silhouette = -1
    best_inertia = None
    best_labels = None

    for k in range(10, 26):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        silhouette = silhouette_score(X, labels)
        
        print(f"  -> Probando K-Means (k={k}): Silhouette = {silhouette:.4f} | Inercia = {kmeans.inertia_:.2f}")

        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_k = k
            best_inertia = kmeans.inertia_
            best_labels = labels

    # Criterio de utilidad: Si el mejor K-Means refinado sigue siendo muy inferior al baseline de DBSCAN (0.65), se descarta.
    is_useful = best_silhouette >= 0.50
    
    if not is_useful:
        print(f"Resumen K-Means: La mejor configuración extendida fue k={best_k} (Silhouette: {best_silhouette:.4f}).")
        print("Decisión: DESCARTADO para el cuadro comparativo final debido a que no presenta mejoras competitivas frente a los modelos basados en densidad.")
        return None

    print(f"Resumen K-Means: Configuración útil encontrada para k={best_k}. Silhouette: {best_silhouette:.4f}")
    return {
        "Paradigma": "K-Means Refinado", 
        "Hiperparámetros": f"k={best_k}", 
        "Silhouette_Score": best_silhouette, 
        "Métrica_Específica": f"Inercia: {best_inertia:.2f}", 
        "labels": best_labels
    }

def refine_dbscan(X):
    print("\n--- Refinamiento de Paradigma de Densidad (DBSCAN) ---")
    print("Objetivo: Búsqueda granular alrededor del óptimo previo (eps=2.5, min_pts=15).")
    best_eps = 2.5
    best_min_samples = 15
    best_silhouette = -1
    best_noise_ratio = 1.0
    best_labels = None
    best_n_clusters = 0

    eps_values = [2.3, 2.4, 2.5, 2.6, 2.7]
    min_samples_values = [10, 15, 20]

    for eps in eps_values:
        for min_samples in min_samples_values:
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            labels = dbscan.fit_predict(X)
            
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            noise_ratio = np.sum(labels == -1) / len(labels)
            
            if n_clusters > 1 and noise_ratio < 0.20:
                silhouette = silhouette_score(X, labels)
                print(f"  -> Probando DBSCAN (eps={eps:.1f}, min={min_samples}): Clusters={n_clusters} | Ruido={noise_ratio*100:.2f}% | Silhouette={silhouette:.4f}")
                
                if silhouette > best_silhouette:
                    best_silhouette = silhouette
                    best_eps = eps
                    best_min_samples = min_samples
                    best_noise_ratio = noise_ratio
                    best_labels = labels
                    best_n_clusters = n_clusters
            else:
                print(f"  -> Probando DBSCAN (eps={eps:.1f}, min={min_samples}): [DESCARTADO] Clusters={n_clusters} | Ruido={noise_ratio*100:.2f}%")

    print(f"Resumen DBSCAN: Mejor configuración eps={best_eps:.1f}, min_pts={best_min_samples}. Clusters: {best_n_clusters}, Ruido: {best_noise_ratio*100:.2f}%, Silhouette: {best_silhouette:.4f}")
    
    return {
        "Paradigma": "DBSCAN Refinado", 
        "Hiperparámetros": f"eps={best_eps:.1f}, min_pts={best_min_samples}", 
        "Silhouette_Score": best_silhouette, 
        "Métrica_Específica": f"Ruido: {best_noise_ratio*100:.2f}%", 
        "labels": best_labels
    }

def evaluate_hdbscan(X):
    print("\n--- Ejecutando Paradigma de Densidad Jerárquica (HDBSCAN) ---")
    print("Objetivo: Evaluar si el agrupamiento por densidad variable supera al radio fijo de DBSCAN.")
    best_min_cluster_size = 0
    best_silhouette = -1
    best_noise_ratio = 1.0
    best_labels = None
    best_n_clusters = 0

    min_cluster_sizes = [10, 15, 20, 30]

    for mcs in min_cluster_sizes:
        hdbscan_model = HDBSCAN(min_cluster_size=mcs)
        labels = hdbscan_model.fit_predict(X)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_ratio = np.sum(labels == -1) / len(labels)
        
        if n_clusters > 1:
            silhouette = silhouette_score(X, labels)
            print(f"  -> Probando HDBSCAN (min_cluster_size={mcs}): Clusters={n_clusters} | Ruido={noise_ratio*100:.2f}% | Silhouette={silhouette:.4f}")
            
            if silhouette > best_silhouette:
                best_silhouette = silhouette
                best_min_cluster_size = mcs
                best_noise_ratio = noise_ratio
                best_labels = labels
                best_n_clusters = n_clusters
        else:
            print(f"  -> Probando HDBSCAN (min_cluster_size={mcs}): [DESCARTADO] Clusters={n_clusters} | Ruido={noise_ratio*100:.2f}%")

    print(f"Resumen HDBSCAN: Mejor configuración min_cluster_size={best_min_cluster_size}. Clusters: {best_n_clusters}, Ruido: {best_noise_ratio*100:.2f}%, Silhouette: {best_silhouette:.4f}")
    
    return {
        "Paradigma": "HDBSCAN", 
        "Hiperparámetros": f"min_cluster_size={best_min_cluster_size}", 
        "Silhouette_Score": best_silhouette, 
        "Métrica_Específica": f"Ruido: {best_noise_ratio*100:.2f}%", 
        "labels": best_labels
    }

def main():
    print("Iniciando Pipeline de Refinamiento de Clustering (Hito 3)")
    matrix_path = "data/features/feature_matrix_reduced.npy"
    
    try:
        X = load_data(matrix_path)
    except FileNotFoundError as e:
        print(e)
        return

    print(f"Matriz de datos cargada. Dimensiones operativas: {X.shape}")

    discard_gmm()
    
    resultados = []
    
    res_kmeans = refine_kmeans(X)
    if res_kmeans is not None:
        resultados.append(res_kmeans)
        
    res_dbscan = refine_dbscan(X)
    resultados.append(res_dbscan)
    
    res_hdbscan = evaluate_hdbscan(X)
    resultados.append(res_hdbscan)

    df_resultados = pd.DataFrame(resultados).drop(columns=['labels'])
    
    print("\n=========================================================================================")
    print("                    CUADRO DE DECISIÓN FINAL DE PARADIGMAS (REFINAMIENTO)                ")
    print("=========================================================================================")
    print(df_resultados.to_string(index=False, justify='center'))
    print("=========================================================================================\n")

    ganador = max(resultados, key=lambda x: x['Silhouette_Score'])
    
    print(">>> DECLARACIÓN DEL MODELO GANADOR DEFINITIVO <<<")
    print(f"El modelo ganador para la implementación es: {ganador['Paradigma']}")
    print(f"Justificación Técnica: Presentó el mayor coeficiente de Silhouette ({ganador['Silhouette_Score']:.4f}) tras el proceso de refinamiento de hiperparámetros.")
    print("Esto asegura la separación matemática óptima de los perfiles de inventario y consumo en la cocina.")
    
    output_dir = "data/features"
    os.makedirs(output_dir, exist_ok=True)
    np.save(f"{output_dir}/cluster_labels_refined.npy", ganador['labels'])
    print(f"Las etiquetas definitivas han sido guardadas en '{output_dir}/cluster_labels_refined.npy'.")

if __name__ == "__main__":
    main()