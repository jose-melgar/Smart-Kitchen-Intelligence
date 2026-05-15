# Smart Kitchen Intelligence (SKI)

**Estado Actual:** Hito 3 (Semana 7) Completado. Pipeline completo implementado: ingesta y simulación de datos → ingeniería de características → reducción de dimensionalidad (PCA/t-SNE) → clustering y segmentación (DBSCAN, Silhouette = 0.6549).

| Hito | Semana | Estado |
| :--- | :--- | :--- |
| Pipeline de datos (ingesta, ETL, esquema) | 3 | ✅ Completado |
| Feature engineering + Reducción dimensional (PCA/t-SNE) | 5 | ✅ Completado |
| Clustering y segmentación de comportamiento | 7 | ✅ Completado |
| Análisis de grafos de co-ocurrencia | 9 | 🔜 Próximo |
| Motor de recomendación híbrido | 11–13 | 🔜 Pendiente |

## 1. Descripción del Proyecto

**Smart Kitchen Intelligence (SKI)** es un prototipo de sistema de datos diseñado para abordar el desperdicio de alimentos y la nutrición ineficiente en el hogar. El sistema ingiere metadatos de productos desde la API de OpenFoodFacts y simula un historial de interacciones de inventario (entradas y salidas) para crear un dataset robusto que sirva de base para análisis avanzados.

El objetivo final no es solo monitorear un inventario, sino construir un motor de recomendación y descubrimiento que responda a la pregunta: *¿Cómo optimizar el consumo de alimentos basándose en la proximidad de vencimiento, el perfil nutricional y la co-ocurrencia histórica de ingredientes?*

## 2. Quick Start: Reproducción del Pipeline Completo

Para ejecutar el pipeline end-to-end (datos → features → clustering), siga estos pasos. Se asume un entorno tipo Unix (Linux/macOS).

```bash
# 1. Clonar el repositorio
git clone https://github.com/jose-melgar/Smart-Kitchen-Intelligence.git
cd Smart-Kitchen-Intelligence

# 2. Configurar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Pipeline de datos (Hito 1)
python src/extract_patterns.py   # Extrae patrones de comportamiento (Kaggle/Instacart)
python src/simulation.py         # Simula movimientos de inventario durante 90 días
python src/ingestion.py          # Enriquece el catálogo con datos nutricionales (USDA)
python src/preprocessing.py      # Consolida y limpia → data/processed/inventory_v1.csv

# 5. Feature engineering y reducción dimensional (Hito 2)
python src/features.py           # Genera matriz de features → data/features/feature_matrix.npy
python src/reduction.py          # PCA + t-SNE → feature_matrix_reduced.npy + figuras

# 6. Clustering y segmentación (Hito 3)
python src/clustering.py         # Benchmark K-Means / DBSCAN / GMM → cluster_labels.npy
python src/clustering_refinement.py  # Refinamiento DBSCAN → cluster_labels_refined.npy
```

Para instrucciones detalladas de cada paso (credenciales, entradas/salidas esperadas y resultados), consulte el [**Runbook de Ejecución (`runbook.md`)**](./runbook.md).

## 3. Arquitectura y Capas del Sistema

El proyecto está estructurado en capas interdependientes que permiten un desarrollo modular y escalable.

*   **Capa de Ingesta y Simulación:**
    *   `src/ingestion.py`: Se conecta a la API de OpenFoodFacts. Incluye una estrategia de *fallback* a datos mock para garantizar la resiliencia del pipeline.
    *   `src/simulation.py`: Genera un log de eventos de inventario (`IN`/`OUT`) basado en el catálogo de productos, creando la capa de interacción necesaria para el filtrado colaborativo y el análisis de comportamiento.

*   **Capa de Procesamiento (ETL):**
    *   `src/preprocessing.py`: Realiza la unión (join) entre los datos de catálogo y los logs de movimiento. Normaliza tipos de datos y prepara el dataset analítico principal (`inventory_v1.csv`) basado en un [Esquema de Estrella](./schema_draft.md) desnormalizado.

*   **Capa de Feature Engineering y Reducción Dimensional (Hito 2):**
    *   `src/features.py`: Construye la matriz de características densa (72.000 filas × 61 features) combinando variables numéricas, categóricas, de texto y temporales.
    *   `src/reduction.py`: Aplica PCA reteniendo el 90% de la varianza en 30 componentes y t-SNE para visualización no lineal. Genera `feature_matrix_reduced.npy` como single source of truth para el clustering.

*   **Capa de Clustering y Segmentación (Hito 3):**
    *   `src/clustering.py`: Benchmark competitivo entre K-Means (k=2–10), DBSCAN (barrido de eps y min_samples) y GMM (2–10 componentes). Selecciona el paradigma ganador por Silhouette Score.
    *   `src/clustering_refinement.py`: Descarta GMM, extiende K-Means hasta k=25, evalúa HDBSCAN y realiza un barrido granular de DBSCAN. Resultado final: **DBSCAN (eps=2.7, min_samples=15), Silhouette = 0.6549, 38 clusters, ruido < 0.3%**.

*   **Capa de Análisis y Modelado (Fases Próximas):**
    *   **Análisis de Grafos:** Construcción de un grafo de co-ocurrencia de productos (basado en eventos `IN` con proximidad temporal) para identificar sustitutos o complementos.
    *   **Sistema de Recomendación:** Motor híbrido que pondera popularidad, perfil nutricional, fecha de vencimiento y señales del grafo.

## 4. Estructura del Repositorio

La estructura de directorios está diseñada para garantizar la separación de conceptos y la reproducibilidad, un pilar fundamental de la ingeniería de datos.

```text
.
├── data/
│   ├── raw/                    # Salida inmutable de los scripts de ingesta/simulación
│   ├── processed/              # Dataset consolidado (inventory_v1.csv)
│   └── features/               # Matrices numéricas para ML y etiquetas de clustering
│       ├── feature_matrix.npy          # Matriz densa original (72k × 61)
│       ├── feature_matrix_reduced.npy  # Matriz reducida por PCA (72k × 30)
│       ├── cluster_labels.npy          # Etiquetas fase exploratoria
│       └── cluster_labels_refined.npy  # Etiquetas definitivas DBSCAN refinado
├── src/                        # Scripts Python ejecutables (pipeline secuencial)
├── notebooks/                  # Jupyter Notebooks para EDA y prototipado
├── reports/
│   ├── figures/                # Visualizaciones generadas automáticamente
│   └── *.md                    # Reportes técnicos por hito
├── runbook.md                  # Manual de ejecución completo (pasos 1–8)
└── requirements.txt            # Dependencias del proyecto
```

## 5. Documentación Clave del Proyecto

La toma de decisiones de ingeniería y el diseño del sistema están documentados en los siguientes reportes:

| Documento | Hito | Propósito |
| :--- | :---: | :--- |
| **`proposal.md`** | 1 | Define el problema, la pregunta de producto y la idoneidad del proyecto. |
| **`source_inventory.md`** | 1 | Cataloga las fuentes de datos y la estrategia de resiliencia. |
| **`schema_draft.md`** | 1 | Justifica la elección del esquema de datos y su impacto en el rendimiento. |
| **`scale_analysis.md`** | 1 | Analiza la escalabilidad del pipeline e identifica cuellos de botella. |
| **`data_dictionary.md`** | 1 | Proporciona una definición precisa de cada variable en el dataset procesado. |
| **`ethics_note.md`** | 1 | Aborda el origen de los datos y las medidas de mitigación de riesgos. |
| **`dimensionality_reduction_report.md`** | 2 | Documenta la metodología PCA/t-SNE, energía retenida y selección de componentes. |
| **`clustering_experiments.md`** | 3 | Registro de los experimentos de clustering: benchmark y cuadro comparativo final. |
| **`final_model_selection.md`** | 3 | Declaración del modelo ganador (DBSCAN) con justificación técnica y métricas. |

---
**Curso:** Big Data | **Universidad:** UPC | **Track:** B (Build-Your-Own Dataset)