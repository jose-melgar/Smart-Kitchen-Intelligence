# Guía de Ejecución y Reproducibilidad (Runbook) - SKI Project

Este documento detalla los pasos necesarios para reproducir el pipeline de datos completo del proyecto, desde la ingesta de datos crudos hasta la segmentación por clustering (Entregas Semanas 3, 5 y 7).

## 1. Configuración del Entorno

### 1.1. Dependencias del Sistema
El pipeline requiere Python 3.9+ y las dependencias listadas en `requirements.txt`.

```bash
# Crear y activar un entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar las dependencias de Python
pip install -r requirements.txt
```

### 1.2. Configuración de Credenciales (Obligatorio)

El pipeline utiliza dos APIs que requieren autenticación:

1.  **Kaggle API:** Para descargar el dataset de Instacart. Asegúrate de tener tu archivo `kaggle.json` en `~/.kaggle/kaggle.json`. Consulta la [guía de Kaggle](https://www.kaggle.com/docs/api) para obtener tus credenciales.

2.  **USDA FoodData Central API:** Para enriquecer los datos con información nutricional.
    *   Crea un archivo llamado `.env` en la raíz del proyecto.
    *   Añade tu clave de API de la USDA (puedes obtener una [aquí](https://fdc.nal.usda.gov/api-key.html)) dentro del archivo de la siguiente manera:

    ```.env
    USDA_API_KEY="TU_CLAVE_API_AQUI"
    ```

## 2. Ejecución Completa del Pipeline de Datos

El pipeline se ejecuta en una secuencia de scripts. Cada uno genera artefactos que son consumidos por el siguiente. Ejecútalos en el orden indicado.

### Paso 1: Extracción de Patrones de Comportamiento
Este script descarga un dataset público de Instacart para extraer patrones realistas de compra (distribución por horas, productos más comunes).

```bash
python src/extract_patterns.py
```
*   **Entrada:** Dataset `yasserh/instacart-online-grocery-basket-analysis-dataset` de Kaggle.
*   **Salida:** `data/raw/instacart_patterns.json`

### Paso 2: Simulación Masiva de Movimientos
Usando los patrones extraídos, este script simula el comportamiento de múltiples hogares durante 90 días para generar un volumen de datos transaccionales significativo.

```bash
python src/simulation.py
```
*   **Entrada:** `data/raw/instacart_patterns.json`
*   **Salida:** `data/raw/movements_raw.csv`

### Paso 3: Enriquecimiento del Catálogo con Datos Nutricionales
Este script toma los productos de la simulación y consulta la API de USDA para obtener datos nutricionales reales, construyendo el catálogo de productos.

```bash
python src/ingestion.py
```
*   **Entradas:** `data/raw/movements_raw.csv`, API de USDA.
*   **Salida:** `data/raw/catalog_raw.csv`

### Paso 4: Preprocesamiento y Consolidación
Unifica los movimientos simulados con la información del catálogo en un único dataset limpio y listo para el análisis. Utiliza Polars para un alto rendimiento.

```bash
python src/preprocessing.py
```
*   **Entradas:** `data/raw/movements_raw.csv`, `data/raw/catalog_raw.csv`.
*   **Salida:** `data/processed/inventory_v1.csv`

## 3. Generación de Artefactos para Machine Learning (Semana 5)

Una vez que el dataset procesado está listo, se pueden ejecutar los scripts de análisis.

### Paso 5: Ingeniería de Características (Feature Engineering)
Convierte el dataset tabular en una matriz numérica de características lista para ser usada por algoritmos de Machine Learning.

```bash
python src/features.py
```
*   **Entrada:** `data/processed/inventory_v1.csv`
*   **Salidas:** `data/features/feature_matrix.npy`, `data/features/feature_names.json`

### Paso 6: Análisis de Reducción de Dimensionalidad
Ejecuta PCA sobre la matriz de características para analizar su estructura latente y generar un reporte visual.

```bash
python src/reduction.py
```
*   **Entradas:** `data/features/feature_matrix.npy`, `data/processed/inventory_v1.csv`.
*   **Salidas:** Gráficos `pca_scree_plot.png`, `pca_scatter_2d.png`, `pca_biplot.png` y `tsne_clusters.png` en `reports/figures/`; matriz reducida `data/features/feature_matrix_reduced.npy`.

## 4. Clustering y Segmentación de Comportamiento (Semana 7 / Hito 3)

Con la matriz reducida lista, se ejecutan los dos scripts de clustering en secuencia. El primero realiza un benchmark competitivo entre tres paradigmas; el segundo refina los hiperparámetros del mejor candidato para obtener el modelo definitivo.

### Paso 7: Benchmark de Paradigmas de Clustering (Exploración)
Evalúa K-Means (k=2 a 10), DBSCAN (barrido de eps y min_samples) y GMM (2 a 10 componentes). Imprime en consola el cuadro comparativo de Silhouette Score y guarda las etiquetas del modelo ganador preliminar.

```bash
python src/clustering.py
```
*   **Entrada:** `data/features/feature_matrix_reduced.npy`
*   **Salidas:**
    *   `data/features/cluster_labels.npy` — etiquetas del modelo ganador de la fase exploratoria.
    *   Cuadro comparativo impreso en consola (K-Means vs DBSCAN vs GMM).

> **Resultado esperado:** DBSCAN con Silhouette ≈ 0.65 supera a K-Means (≈ 0.37) y GMM (≈ 0.20). El script declara el ganador automáticamente.

### Paso 8: Refinamiento del Modelo Ganador (DBSCAN)
Descarta GMM formalmente, extiende la búsqueda de K-Means hasta k=25 para verificar que no fue un mínimo local, evalúa HDBSCAN y realiza un barrido granular alrededor del óptimo de DBSCAN (eps ≈ 2.5). Guarda las etiquetas definitivas.

```bash
python src/clustering_refinement.py
```
*   **Entrada:** `data/features/feature_matrix_reduced.npy`
*   **Salidas:**
    *   `data/features/cluster_labels_refined.npy` — etiquetas finales del modelo DBSCAN optimizado (eps=2.7, min_samples=15).
    *   Cuadro de decisión final impreso en consola.

> **Resultado esperado:** DBSCAN refinado (eps=2.7, min_samples=15) obtiene Silhouette = 0.6549, identifica ~38 clusters y reduce el ruido al 0.28%. Este artefacto es el **Single Source of Truth** para la fase de recomendación.

## 5. Recomendador (Semana 11 / Hito 4)

Pipeline de recomendación de tres capas: contenido (TF-IDF), filtrado colaborativo (ALS implícito) e híbrido con señal anti-desperdicio. Todos los artefactos se guardan en `data/recommender/` (ver `data/recommender/README.md`).

### Paso 9: Construcción de la matriz R

Define la unidad de "sesión" (restock 60 min / kitchen 15 min) y produce 4 encodings de R en cada unidad más el caso base household × producto.

```bash
python src/build_R.py
```
*   **Entrada:** `data/processed/inventory_v1.csv`
*   **Salidas:** `data/recommender/R_*.npz` (10 matrices), `sparsity_report.json`, `products.json`, `sessions_*.json`

### Paso 10: Recomendador basado en contenido (TF-IDF)

Construye el catálogo, ajusta TF-IDF, calcula similitud ítem-ítem por contenido y demuestra recomendación para `household=0` con hold-out 20%.

```bash
python src/recommender_content.py
```
*   **Entrada:** `data/processed/inventory_v1.csv`
*   **Salidas:** `data/recommender/tfidf_items.npz`, `tfidf_vocab.json`, `product_catalog.csv`, `item_sim_content.npy`

### Paso 11: Normalizaciones de R

Genera 5 variantes normalizadas de `R_restock_count` (raw, mean-center, log1p, tfidf_R, l2_row) con métricas comparativas.

```bash
python src/normalizations.py
```
*   **Entrada:** `data/recommender/R_restock_count.npz`
*   **Salidas:** `data/recommender/R_restock_{raw,row_mean_center,log1p,tfidf_R,l2_row}.npz`, `normalization_summary.json`

### Paso 12: Filtrado colaborativo + lambda iteration

Similitud ítem-ítem (dot y cosine) y ALS implícito con barrido de λ ∈ {0.001, ..., 10}. Selecciona el λ óptimo por precision@5 en hold-out 20%.

```bash
python src/recommender_cf.py
```
*   **Entrada:** `data/recommender/R_restock_tfidf_R.npz`, `R_restock_bin.npz`
*   **Salidas:** `item_sim_cf_{dot,cosine}.npy`, `als_X.npy`, `als_Y.npy`, `als_meta.json`, `lambda_sweep.csv`

> **Resultado esperado:** λ óptimo = 1.0; precision@5 ≈ 0.0494, recall@5 ≈ 0.1163.

### Paso 13: Cold-start

Evalúa popularity / partial_cf / content_only / mixed sobre sesiones cold con 1 y 2 seeds.

```bash
python src/cold_start.py
```
*   **Entradas:** `R_restock_bin.npz`, `item_sim_cf_cosine.npy`, `item_sim_content.npy`
*   **Salidas:** `cold_start_session{,_2seed}.csv`, `cold_start_product.csv`, `cold_start_summary.json`

> **Resultado esperado:** `partial_cf` gana con precision@5 = 0.2020 (1 seed) y 0.1955 (2 seeds).

### Paso 14: Recomendador híbrido

Combina contenido + CF + señal de proximidad de vencimiento. Genera top-10 para `household=0` y ablación de pesos.

```bash
python src/recommender_hybrid.py
```
*   **Entradas:** `tfidf_items.npz`, `als_Y.npy`, `product_catalog.csv`, `data/processed/inventory_v1.csv`
*   **Salidas:** `hybrid_top10_hh0.csv`, `hybrid_ablation.csv`, `hybrid_meta.json`

### Paso 15: Evaluación consolidada (Week 10 milestone)

Aplica el protocolo único de hold-out a los 4 sistemas (popularity, content_tfidf, cf_als, hybrid) con las mismas métricas y candidate pool. Produce la tabla del informe.

```bash
python src/evaluation.py
```
*   **Entradas:** todos los artefactos previos del recomendador.
*   **Salidas:** `evaluation_table.csv`, `evaluation_summary.json`, `error_analysis.csv`

> **Resultado esperado:** popularity gana precision@5 (0.0508) pero solo cubre 22% del catálogo; hybrid logra coverage 100% y MAP@5 = 0.0539.

### Paso 16: Figuras del informe

```bash
python src/generate_hito4_figures.py
```
*   **Salidas:** 6 PNG en `reports/figures/hito4/` (sparsity, tfidf_idf, normalización, lambda sweep, cold-start, ablación).

### Paso 17: Compilar el informe LaTeX

```bash
xelatex -interaction=nonstopmode informe_hito4.tex
xelatex -interaction=nonstopmode informe_hito4.tex   # segunda pasada para refs
```
*   **Salida:** `informe_hito4.pdf` (≈19 páginas).

## 6. Analítica de Grafos y Centralidad (Semana 12 / Hito 5)

Construye un grafo de co-ocurrencia producto-producto a partir de la matriz de sesiones de restock y calcula métricas estructurales y de centralidad PageRank.

### Paso 18: Construcción del grafo

Calcula la matriz de adyacencia mediante $A = R^T \cdot R$ sobre la matriz binaria de sesiones de restock y exporta la red no dirigida ponderada.

```bash
python src/graph_construction.py
```
*   **Entradas:** `data/recommender/R_restock_bin.npz`, `data/recommender/product_catalog.csv`
*   **Salida:** `data/recommender/kitchen_graph.gexf`

> **Resultado esperado:** 50 nodos, 1,225 aristas (grafo completo), 1 componente conexa.

### Paso 19: Analítica de grafo y PageRank

Calcula componentes conectadas, grado (simple y ponderado) y centralidad PageRank ($\alpha=0.85$) sobre el grafo de co-ocurrencia.

```bash
python src/graph_analytics.py
```
*   **Entrada:** `data/recommender/kitchen_graph.gexf`
*   **Salida:** `data/recommender/graph_metrics.json`

> **Resultado esperado:** grado ponderado medio ≈ 1,822.8 (mín 1,613 / máx 1,996); top-10 PageRank documentado en `reports/graph_analytics_report.md`.

### Paso 20 (opcional): Figuras del informe de Hito 5

```bash
python src/generate_hito5_figures.py
```

> **Nota:** tras generar el grafo y sus métricas, se recomienda volver a ejecutar `python src/evaluation.py` para comparar el ranking por PageRank contra el Recomendador Híbrido bajo el mismo protocolo de evaluación.

## 7. Perfilado de Clusters (deuda técnica de Hito 3)

### Paso 21: Perfiles de cluster y análisis de fallos

```bash
python src/cluster_profiling.py
```
*   **Entradas:** `data/features/cluster_labels_refined.npy`, `data/features/feature_matrix.npy`, `data/features/feature_names.json`, `data/processed/inventory_v1.csv`
*   **Salida:** `reports/cluster_profiles.md` (38 perfiles de cluster + failure analysis del ruido)

## 8. Extensión de Grafo al Híbrido y Demo Final (Semana 13-14)

### Paso 22: Ablación de pesos con PageRank y evaluación de `hybrid_v2_graph`

```bash
python src/recommender_hybrid.py   # barrido 4D (w_C, w_F, w_E, w_G) -> hybrid_meta.json, hybrid_ablation.csv
python src/evaluation.py           # re-evalúa los 6 sistemas, incluyendo hybrid_v2_graph -> evaluation_table.csv
```
*   **Resultado esperado:** óptimo empírico $w_G=0.00$ (el híbrido v1 sin grafo sigue siendo superior). Ver `reports/graph_analytics_report.md` §5.

### Paso 23: Demo final interactivo (Streamlit)

```bash
streamlit run src/demo_app.py
```
*   **Entradas:** todos los artefactos de `data/features/` y `data/recommender/` (solo lectura, sin escritura de artefactos).
*   Permite elegir un household, ver su cluster de comportamiento dominante, sus top-5 recomendaciones híbridas v1 y el grafo de co-ocurrencia con esas 5 recomendaciones resaltadas.

### Resumen de artefactos generados por hito

| Hito | Script(s) | Artefacto principal |
| :--- | :--- | :--- |
| Semana 3 | `extract_patterns` → `simulation` → `ingestion` → `preprocessing` | `data/processed/inventory_v1.csv` |
| Semana 5 | `features` → `reduction` | `data/features/feature_matrix_reduced.npy` |
| Semana 7 | `clustering` → `clustering_refinement` | `data/features/cluster_labels_refined.npy` |
| Semana 11 | `build_R` → `recommender_content` → `normalizations` → `recommender_cf` → `cold_start` → `recommender_hybrid` → `evaluation` → `generate_hito4_figures` | `data/recommender/evaluation_table.csv` + `informe_hito4.pdf` |
| Semana 12 | `graph_construction` → `graph_analytics` → `generate_hito5_figures` | `data/recommender/graph_metrics.json` |
| Semana 13 | `cluster_profiling` → `recommender_hybrid` (ablación 4D) → `evaluation` | `reports/cluster_profiles.md`, `evaluation_table.csv` (+ `hybrid_v2_graph`) |
| Semana 14 | `demo_app.py` (Streamlit) | Demo final integrado (sin artefactos nuevos, solo lectura) |