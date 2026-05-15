# Reporte de Experimentación de Clustering (Hito 3)

## 1. Fase 1: Exploración Inicial
Se evaluaron tres paradigmas para identificar la topología de los datos de inventario.

- **K-Means (Centroides):** Probado de $k=2$ a $10$.
    - *Resultado:* Mejor $k=9$ con Silhouette de **0.3733**. 
    - *Hallazgo:* Los grupos no son perfectamente esféricos.
- **GMM (Probabilístico):** Probado de 2 a 10 componentes.
    - *Resultado:* Silhouette máximo de **0.1992**.
    - *Hallazgo:* Los datos no siguen distribuciones gaussianas. **Paradigma descartado**.
- **DBSCAN (Densidad):** Evaluación de radio estático.
    - *Resultado:* Silhouette de **0.6547**.
    - *Hallazgo:* Los datos forman núcleos densos de alta cohesión.

**Visualización comparativa:** `reports/figures/clustering_benchmark_silhouette.png`

## 2. Fase 2: Refinamiento Técnico
Se buscaron los límites de precisión mediante un barrido granular de hiperparámetros.

- **K-Means Refinado:** Se extendió el rango hasta $k=25$.
    - *Resultado:* Se logró un Silhouette de **0.5428** en $k=25$.
    - *Conclusión:* Aunque mejora, requiere una sobre-segmentación excesiva para igualar a los modelos de densidad.
- **HDBSCAN (Densidad Jerárquica):** Evaluación de densidad variable.
    - *Resultado:* Silhouette de **0.5816** con `min_cluster_size=30`.
    - *Conclusión:* No superó al modelo de radio fijo, indicando una densidad uniforme en los clusters.
- **DBSCAN Refinado:** Ajuste fino en el entorno de $eps=2.5$.
    - *Resultado:* **Óptimo en eps=2.7, min_pts=15** con Silhouette de **0.6549**.
    - *Resultado adicional:* 38 clusters identificados, 71 puntos de ruido (0.28% del total).

**Proyección 2D de clusters:** `reports/figures/clustering_scatter_2d.png`  
**Distribución de eventos por cluster:** `reports/figures/clustering_distribution.png`

## 3. Cuadro Comparativo Final

| Paradigma | Configuración | Silhouette Score | Estatus |
| :--- | :--- | :--- | :--- |
| **GMM** | components=4 | 0.1992 | Descartado |
| **K-Means Refinado** | k=25 | 0.5428 | Descartado |
| **HDBSCAN** | size=30 | 0.5816 | Descartado |
| **DBSCAN Refinado** | **eps=2.7, min=15** | **0.6549** | **GANADOR** |