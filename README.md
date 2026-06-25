# Smart Kitchen Intelligence (SKI)

**Estado Actual:** Hito 5 (Semana 12) Completado. Pipeline completo implementado y reproducible: ingesta y simulación de datos → ingeniería de características distribuidas → reducción de dimensionalidad (PCA/t-SNE) → clustering y segmentación (DBSCAN) → motor de recomendación híbrido multicapa → análisis estructural de grafos de co-ocurrencia con validación PageRank.

| Hito | Semana | Estado | Métricas Operativas / Entregables |
| :--- | :--- | :--- | :--- |
| Pipeline de datos (ingesta, ETL, esquema) | 3 | ✅ Completado | Integridad relacional del 100% mediante `stock_id`. |
| Feature engineering + Reducción dimensional (PCA/t-SNE) | 5 | ✅ Completado | Matriz densa 72k×61. PCA retiene 90% varianza en 30 componentes. |
| Clustering y segmentación de comportamiento | 7 | ✅ Completado | DBSCAN ($eps=2.7, min\_samples=15$). Silhouette = 0.6549. Ruido < 0.28%. |
| Recomendador Híbrido (Contenido + CF + Expiry) | 11 | ✅ Completado | **Catalog Coverage = 100%**, MAP@5 = 0.0539, Hybrid P@5 = 0.0455. |
| Análisis de grafos de co-ocurrencia transaccional | 12 | ✅ Completado | Modelado de red no dirigida. Evaluación de centralidad PageRank integrada. |
| Motor de recomendación híbrido extendido | 13 | 🔜 Pendiente | Integración de factores de grafo al re-ranking de producción. |

## 1. Descripción del Proyecto

**Smart Kitchen Intelligence (SKI)** es un prototipo de sistema de Big Data avanzado diseñado para abordar de manera directa el desperdicio de alimentos y la gestión ineficiente de despensas en el hogar. El sistema ingiere metadatos enriquecidos de productos desde la API pública de OpenFoodFacts y simula un historial masivo de interacciones transaccionales de inventario (entradas `IN` y salidas `OUT`) parametrizadas con distribuciones estocásticas reales de *Instacart Online Grocery Shopping*.

El objetivo final del sistema es consolidar un motor híbrido inteligente de descubrimiento y re-ranking interactivo que responda de forma íntegra a la pregunta de producto: *¿Cómo optimizar el consumo de alimentos e incentivar el restock doméstico basándose simultáneamente en la afinidad histórica del hogar, patrones latentes colectivos y la urgencia por proximidad de vencimiento físico de las unidades perecederas vivas?*

## 2. Quick Start: Reproducción del Pipeline Completo

Para ejecutar el pipeline end-to-end de forma estrictamente secuencial y reproducible (garantizando la ausencia de estados ocultos locales de Jupyter), ejecute los siguientes comandos desde la raíz del repositorio en un entorno virtualizado Unix/Windows:

```bash
# 1. Clonar el repositorio
git clone [https://github.com/jose-melgar/Smart-Kitchen-Intelligence.git](https://github.com/jose-melgar/Smart-Kitchen-Intelligence.git)
cd Smart-Kitchen-Intelligence

# 2. Configurar el entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\activate

# 3. Instalar dependencias estrictas congeladas
pip install -r requirements.txt

# 4. Pipeline de datos e ingesta inmutable (Hito 1)
python src/extract_patterns.py   # Extrae patrones de comportamiento base desde Instacart
python src/simulation.py         # Simula movimientos de inventario transaccionales durante 90 dias
python src/ingestion.py          # Enriquece y valida el catalogo con la API de la USDA
python src/preprocessing.py      # Operaciones ETL y limpieza -> data/processed/inventory_v1.csv

# 5. Feature engineering y reducción dimensional espacial (Hito 2)
python src/features.py           # Genera matriz densa ML utilizando CatBoost Encoding
python src/reduction.py          # PCA (30 componentes para 90% varianza) + proyecciones t-SNE

# 6. Clustering y segmentación densa de comportamiento (Hito 3)
python src/clustering.py         # Benchmark K-Means / DBSCAN / GMM 
python src/clustering_refinement.py  # Refinamiento geométrico DBSCAN -> cluster_labels_refined.npy

# 7. Motor de Recomendación y Protocolo Offline Consolidado (Hito 4 — Semana 11)
python src/build_R.py                 # Construye las matrices R sobre sesiones operacionales de 60 min
python src/recommender_content.py     # Capa 1: pseudo-documentos TF-IDF y perfiles de Households
python src/recommender_cf.py          # Capa 2: Factorizacion ALS implicita + Lambda sweep logaritmico
python src/normalizations.py          # Validacion de encodings: raw, mean-center, log1p, tfidf_R, l2_row
python src/cold_start.py              # Flujos de arranque en frio: popularidad / partial_cf / content / mixed
python src/recommender_hybrid.py      # Capa 3: Ensamble lineal y barrido de sensibilidad de pesos (Ablacion)
python src/evaluation.py              # Protocolo consolidado ciego bajo el paradigma Masked Cloze Task

# 8. Analítica de Grafos y Centralidad (Hito 5 — Semana 12)
python src/graph_construction.py      # Transforma sesiones de reabastecimiento en red GEXF conexa
python src/graph_analytics.py         # Extrae métricas estructurales globales y centralidad PageRank
# (Nota: ejecutar nuevamente `python src/evaluation.py` para comparar el PageRank vs. el Recomendador Híbrido)

## 3. Arquitectura y Capas del Sistema

El proyecto está estructurado en capas interdependientes y completamente desacopladas que permiten un desarrollo modular, mantenible y escalable, aplicando rigurosamente los estándares de ingeniería de datos modernos para Big Data:

* **Capa de Ingesta y Simulación (Hito 1):**
    * `src/ingestion.py`: Se conecta de forma asíncrona a la API pública de OpenFoodFacts y la USDA. Implementa una estrategia de fallback estructurada hacia datos mock locales para garantizar la resiliencia absoluta del pipeline frente a problemas de red o cuellos de botella por límite de peticiones.
    * `src/simulation.py`: Genera un log transaccional sintético de movimientos de inventario (IN/OUT) a lo largo de 13 semanas para 10 hogares y 50 productos únicos. Está parametrizado con distribuciones estocásticas extraídas de Instacart para asegurar patrones de co-ocurrencia realistas que sirvan de base para el filtrado colaborativo.

* **Capa de Procesamiento (ETL):**
    * `src/preprocessing.py`: Realiza transformaciones complejas, limpieza de tipos de datos y operaciones de agregación (join) entre los metadatos de los catálogos y los logs de movimiento. Consolida el dataset analítico inmutable (inventory_v1.csv) estructurado bajo un Esquema de Estrella desnormalizado optimizado mediante la clave relacional `stock_id`.

* **Capa de Feature Engineering y Reducción Dimensional (Hito 2):**
    * `src/features.py`: Construye la matriz de características densa de aprendizaje automático (72,000 filas × 61 características). Utiliza procesamiento multihilo nativo mediante las expresiones perezosas (Lazy Evaluation) de la librería Polars y migra de esquemas dispersos ruidosos hacia CatBoost Encoding para representar variables cualitativas de alta cardinalidad.
    * `src/reduction.py`: Aplica la técnica lineal PCA sobre el espacio de características, reduciendo la dimensionalidad a 30 Componentes Principales y reteniendo de forma contractual el 90% de la varianza explicada. Como contraparte visual no lineal, ejecuta t-SNE revelando de manera clara la existencia de estructuraciones latentes organizadas en "islas" aisladas.

* **Capa de Clustering y Segmentación Densa (Hito 3):**
    * `src/clustering.py`: Orquesta un benchmark competitivo multiparadigma evaluando de manera simultánea algoritmos de particionamiento (K-Means), probabilísticos (GMM) y de densidad (DBSCAN) sobre el espacio inmutable de componentes de PCA.
    * `src/clustering_refinement.py`: Realiza el refinamiento hiperparamétrico definitivo. Selecciona el paradigma de DBSCAN Refinado ($eps=2.7, min\_samples=15$) por criterios estrictamente geométricos: logra un máximo Silhouette Score de 0.6549, reduce el ruido estadístico al 0.28% e identifica 38 perfiles únicos de comportamiento de consumo en la cocina (v.g., "Perecederos matutinos", "Abarrotes de larga duración") persistidos en `cluster_labels_refined.npy`.

* **Capa del Motor de Recomendación Híbrido Multicapa (Hito 4):**
    * `src/build_R.py`: Colapsa las transacciones a nivel de Sesiones de Restock agregadas en ventanas operacionales de 60 minutos por household. Esto genera una matriz $R$ binaria operacional de $1,177 \times 50$ con una densidad inicial del 17.4%, mitigando matrices degeneradas y el colapso por redundancia.
    * `src/recommender_content.py`: Construye la Capa 1 (Basado en Contenido) concatenando strings cualitativos de atributos del catálogo y discretizando macros nutricionales de la USDA en tokens de texto. Aplica vectorización TF-IDF con normalización por fila $L2\_row$, permitiendo que el producto punto calcule similitudes coseno directas a ultra-alta velocidad.
    * `src/recommender_cf.py`: Construye la Capa 2 (Filtrado Colaborativo Latente) implementando el algoritmo de ALS Implícito bajo la formulación de Hu, Koren & Volinsky. Aplica la transformación analítica `tfidf_R` previa sobre la matriz de interacciones para restar peso a los productos ubiquos masivos (leche, manzanas) y selecciona el parámetro óptimo de regularización $\lambda=1.0$ tras un barrido logarítmico completo en hold-out.
    * `src/recommender_hybrid.py`: Fusiona linealmente las tres señales normalizadas por fila mediante Min-Max, inyectando el componente diferencial de urgencia física anti-desperdicio ($S_{exp} = 1/(1+d)$, días mediana para el vencimiento de unidades vivas en la despensa). Fija los pesos de producción en $w_C=0.35$, $w_F=0.45$, y $w_E=0.20$.
    * `src/evaluation.py`: Ejecuta de forma independiente el protocolo offline global bajo el Paradigma de Tarea de Completitud de Canasta Enmascarada (Masked Basket Completion Task / Cloze Task Style). Aplica un split ciego del 20% de las interacciones no-cero (semilla 42) y evalúa el cross-selling sobre un candidate pool estricto (catálogo completo menos semillas de entrenamiento), demostrando un Catalog Coverage del 100.0%, un MAP@5 de 0.0549 y un compromiso controlado en el Precision@5 híbrido (0.0455) para priorizar el descubrimiento frente al baseline trivial de popularidad.

* **Capa de Analítica de Grafos y Topología (Hito 5):**
    * `src/graph_construction.py`: Induce matemáticamente una red compleja no dirigida basada en las frecuencias de co-ocurrencia de productos dentro de las sesiones de reabastecimiento.
    * `src/graph_analytics.py`: Aplica teoría de redes espaciales para extraer métricas estructurales (componentes conectadas, grados) y métricas de centralidad algorítmica (PageRank), aislando sistemáticamente los "productos puente" esenciales que unifican clústeres de consumo dispares.

## 4. Estructura del Repositorio

La disposición jerárquica de los componentes garantiza la reproducibilidad científica y la separación de conceptos demandada en ingeniería de software:

```text
.
├── data/
│   ├── raw/                    # Logs y salidas inmutables de los scripts de ingesta/simulación
│   │   ├── catalog_raw.csv         # Datos crudos de productos recuperados de las APIs de origen
│   │   ├── movements_raw.csv       # Registro base simulado de movimientos de inventario IN/OUT
│   │   └── instacart_patterns.json # Distribuciones y frecuencias estocásticas de comportamiento
│   ├── processed/              # Capa de almacenamiento limpio y estructurado de datos
│   │   └── inventory_v1.csv        # Dataset unificado inmutable como Single Source of Truth (SSOT)
│   ├── features/               # Matrices numéricas densas optimizadas para algoritmos de ML
│   │   ├── feature_matrix.npy      # Matriz original de ingeniería de características (72k × 61)
│   │   ├── feature_matrix_reduced.npy # Matriz reducida mediante componentes de PCA (72k × 30)
│   │   ├── cluster_labels.npy      # Etiquetas generadas en la fase exploratoria de clustering
│   │   └── cluster_labels_refined.npy # Etiquetas definitivas de segmentación densa DBSCAN
│   └── recommender/            # Artefactos analíticos y matrices del motor de recomendación
│       ├── R_restock_bin.npz       # Matriz binaria dispersa CSR de sesiones de reabastecimiento
│       ├── R_restock_tfidf_R.npz   # Matriz normalizada con TF-IDF para penalizar ítems ubicuos
│       ├── als_X.npy / als_Y.npy   # Factores latentes de sesiones e ítems calculados por ALS
│       ├── evaluation_table.csv    # Cuadro comparativo oficial de métricas globales del Hito 4 y 5
│       ├── hybrid_ablation.csv     # Registro numérico completo del experimento de rejilla de pesos
│       ├── error_analysis.csv      # Segmentación de auditoría cualitativa de los 5 Strong y Failure Cases
│       ├── evaluation_summary.json # Summary con metadatos nativos del protocolo Cloze Task Style
│       ├── kitchen_graph.gexf      # (NUEVO) Grafo no dirigido de co-ocurrencia de productos
│       └── graph_metrics.json      # (NUEVO) Métricas de red y diccionario de centralidad PageRank
├── src/                        # Scripts Python modulares y ejecutables (Pipeline secuencial)
│   ├── extract_patterns.py     # Extractor y procesador de distribuciones de Instacart
│   ├── simulation.py           # Simulador estocástico de flujos transaccionales domésticos
│   ├── ingestion.py            # Orquestador asíncrono de enriquecimiento de metadatos USDA/OFF
│   ├── preprocessing.py        # Canalización ETL de limpieza, tipado y estructuración de datos
│   ├── features.py             # Generador multihilo Polars de transformaciones CatBoost Encoding
│   ├── reduction.py            # Orquestador de transformaciones y reducciones de PCA y t-SNE
│   ├── clustering.py           # Evaluador de rejilla exploratoria de algoritmos de segmentación
│   ├── clustering_refinement.py # Refinador e inyector geométrico de parámetros DBSCAN
│   ├── build_R.py              # Constructor y tokenizador de matrices dispersas de ventanas operacionales
│   ├── recommender_content.py  # Capa 1: Procesador léxico de pseudo-documentos TF-IDF y similitud coseno
│   ├── recommender_cf.py       # Capa 2: Factorización por mínimos cuadrados ALS e iteración lambda
│   ├── recommender_hybrid.py   # Capa 3: Ensamble lineal mixed, re-ranking expiral y rejilla de ablación
│   ├── evaluation.py           # Validador interactivo de métricas ciegos bajo el paradigma Cloze Task
│   ├── graph_construction.py   # (NUEVO) Generador topológico del grafo desde logs de co-ocurrencia
│   └── graph_analytics.py      # (NUEVO) Motor de cálculo de componentes conexas y PageRank
├── notebooks/                  # Jupyter Notebooks dedicados exclusivamente a EDA y prototipado rápido
├── reports/
│   ├── figures/                # Visualizaciones y curvas de aprendizaje exportadas automáticamente
│   │   ├── hito4/                  # Plots del hito: sweeps de lambda, ablación y distribuciones IDF
│   │   └── *.png                   # Scatter plots de t-SNE, scree plots de PCA y siluetas
│   ├── graph_analytics_report.md # (NUEVO) Justificación técnica e interpretación de redes (Hito 5)
│   └── *.md                    # Reportes técnicos e informes descriptivos indexados por hitos
├── informe_hito4.tex           # Documento de defensa técnico-científica oficial en formato LaTeX
├── runbook.md                  # Manual operativo con secuencias explícitas de comandos de consola
└── requirements.txt            # Dependencias del proyecto congeladas con versiones estrictas