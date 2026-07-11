# Smart Kitchen Intelligence (SKI)

**Estado Actual:** Hito 6 (Semana 14 — Entrega Final Integrada) Completado. Pipeline completo implementado y reproducible: ingesta y simulación de datos → ingeniería de características distribuidas → reducción de dimensionalidad (PCA/t-SNE) → clustering y segmentación (DBSCAN) con perfilado de clusters → motor de recomendación híbrido multicapa → análisis estructural de grafos de co-ocurrencia con validación PageRank → ablación de integración de PageRank al híbrido (resultado empírico: no aporta valor de re-ranking a nivel de canasta; ver `reports/graph_analytics_report.md` §5) → demo interactivo, plan de monitoreo, limitaciones consolidadas y reporte técnico final de 13 secciones.

| Hito | Semana | Estado | Métricas Operativas / Entregables |
| :--- | :--- | :--- | :--- |
| Pipeline de datos (ingesta, ETL, esquema) | 3 | ✅ Completado | Integridad relacional del 100% mediante `stock_id`. |
| Feature engineering + Reducción dimensional (PCA/t-SNE) | 5 | ✅ Completado | Matriz densa 72k×61. PCA retiene 90% varianza en 30 componentes. |
| Clustering y segmentación de comportamiento | 7 | ✅ Completado | DBSCAN ($eps=2.7, min\_samples=15$). Silhouette = 0.6549. Ruido < 0.28%. Perfiles por cluster en `reports/cluster_profiles.md`. |
| Recomendador Híbrido (Contenido + CF + Expiry) | 11 | ✅ Completado | **Catalog Coverage = 100%**, MAP@5 = 0.0574, Hybrid P@5 = 0.0494. |
| Análisis de grafos de co-ocurrencia transaccional | 12 | ✅ Completado | Modelado de red no dirigida. Evaluación de centralidad PageRank integrada. |
| Motor de recomendación híbrido extendido (PageRank) | 13 | ✅ Completado | Ablación 4D evaluó $w_G$; óptimo empírico $w_G=0.00$. Híbrido v1 (P@5=0.0494, MAP@5=0.0574) supera a v2 con grafo (P@5=0.0479, MAP@5=0.0560). Ver `reports/graph_analytics_report.md` §5. |
| Entrega Final Integrada (demo, monitoreo, limitaciones, informe final) | 14 | ✅ Completado | Demo interactivo Streamlit (`src/demo_app.py`), `reports/monitoring_plan.md`, `reports/limitations_and_future_work.md`, `reports/final_report.md` (13 secciones), orquestador de un comando (`run_pipeline.py`) y 35 pruebas de humo (`tests/`, ejecutar con `pytest`). |

## 1. Descripción del Proyecto

**Smart Kitchen Intelligence (SKI)** es un prototipo de sistema de Big Data avanzado diseñado para abordar de manera directa el desperdicio de alimentos y la gestión ineficiente de despensas en el hogar. El sistema ingiere metadatos enriquecidos de productos desde la API pública de OpenFoodFacts y simula un historial masivo de interacciones transaccionales de inventario (entradas `IN` y salidas `OUT`) parametrizadas con distribuciones estocásticas reales de *Instacart Online Grocery Shopping*.

El objetivo final del sistema es consolidar un motor híbrido inteligente de descubrimiento y re-ranking interactivo que responda de forma íntegra a la pregunta de producto: *¿Cómo optimizar el consumo de alimentos e incentivar el restock doméstico basándose simultáneamente en la afinidad histórica del hogar, patrones latentes colectivos y la urgencia por proximidad de vencimiento físico de las unidades perecederas vivas?*

## 2. Quick Start: Reproducción del Pipeline Completo

Para ejecutar el pipeline end-to-end de forma estrictamente secuencial y reproducible (garantizando la ausencia de estados ocultos locales de Jupyter), ejecute los siguientes comandos desde la raíz del repositorio en un entorno virtualizado Unix/Windows:

```bash
# 1. Clonar el repositorio
git clone [https://github.com/jose-melgar/Smart-Kitchen-Intelligence.git](https://github.com/jose-melgar/Smart-Kitchen-Intelligence.git)
cd Smart-Kitchen-Intelligence

# 2. Instalar dependencias estrictas congeladas
pip install -r requirements.txt

# 3. Pipeline de datos e ingesta inmutable (Hito 1)
python src/extract_patterns.py   # Extrae patrones de comportamiento base desde Instacart
python src/simulation.py         # Simula movimientos de inventario transaccionales durante 90 dias
python src/ingestion.py          # Enriquece y valida el catalogo con la API de la USDA
python src/preprocessing.py      # Operaciones ETL y limpieza -> data/processed/inventory_v1.csv

# 4. Feature engineering y reducción dimensional espacial (Hito 2)
python src/features.py           # Genera matriz densa ML utilizando CatBoost Encoding
python src/reduction.py          # PCA (30 componentes para 90% varianza) + proyecciones t-SNE

# 5. Clustering y segmentación densa de comportamiento (Hito 3)
python src/clustering.py         # Benchmark K-Means / DBSCAN / GMM 
python src/clustering_refinement.py  # Refinamiento geométrico DBSCAN -> cluster_labels_refined.npy

# 6. Motor de Recomendación y Protocolo Offline Consolidado (Hito 4 — Semana 11)
python src/build_R.py                 # Construye las matrices R sobre sesiones operacionales de 60 min
python src/recommender_content.py     # Capa 1: pseudo-documentos TF-IDF y perfiles de Households
python src/recommender_cf.py          # Capa 2: Factorizacion ALS implicita + Lambda sweep logaritmico
python src/normalizations.py          # Validacion de encodings: raw, mean-center, log1p, tfidf_R, l2_row
python src/cold_start.py              # Flujos de arranque en frio: popularidad / partial_cf / content / mixed
python src/recommender_hybrid.py      # Capa 3: Ensamble lineal y barrido de sensibilidad de pesos (Ablacion)
python src/evaluation.py              # Protocolo consolidado ciego bajo el paradigma Masked Cloze Task

# 7. Analítica de Grafos y Centralidad (Hito 5 — Semana 12)
python src/graph_construction.py      # Transforma sesiones de reabastecimiento en red GEXF conexa
python src/graph_analytics.py         # Extrae métricas estructurales globales y centralidad PageRank
# (Nota: ejecutar nuevamente `python src/evaluation.py` para comparar el PageRank vs. el Recomendador Híbrido)

# 8. Perfilado de clusters, integración de PageRank al híbrido y demo final (Hito 6 — Semanas 13-14)
python src/cluster_profiling.py       # Perfiles por cluster + failure analysis del ruido DBSCAN
python src/recommender_hybrid.py      # Re-ablación 4D (w_C, w_F, w_E, w_G) -> hybrid_v2_graph
python src/evaluation.py              # Re-evalúa los 6 sistemas, incluyendo hybrid_v2_graph
streamlit run src/demo_app.py         # Demo interactivo: household -> cluster -> recomendación -> grafo

# 9. (Alternativa) Correr todo el pipeline de un solo comando
python run_pipeline.py --skip-ingestion   # Hito 1-6 completo, usando data/raw/ ya versionado
python -m pytest                          # 35 pruebas de humo sobre shapes/rangos de artefactos

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
    * `src/evaluation.py`: Ejecuta de forma independiente el protocolo offline global bajo el Paradigma de Tarea de Completitud de Canasta Enmascarada (Masked Basket Completion Task / Cloze Task Style). Aplica un split ciego del 20% de las interacciones no-cero (semilla 42) y evalúa el cross-selling sobre un candidate pool estricto (catálogo completo menos semillas de entrenamiento), demostrando un Catalog Coverage del 100.0%, un MAP@5 de 0.0574 y un compromiso controlado en el Precision@5 híbrido (0.0494) para priorizar el descubrimiento frente al baseline trivial de popularidad.

* **Capa de Analítica de Grafos y Topología (Hito 5):**
    * `src/graph_construction.py`: Induce matemáticamente una red compleja no dirigida basada en las frecuencias de co-ocurrencia de productos dentro de las sesiones de reabastecimiento.
    * `src/graph_analytics.py`: Aplica teoría de redes espaciales para extraer métricas estructurales (componentes conectadas, grados) y métricas de centralidad algorítmica (PageRank), aislando sistemáticamente los "productos puente" esenciales que unifican clústeres de consumo dispares.

* **Capa de Cierre e Integración Final (Hito 6 — Semanas 13-14):**
    * `src/cluster_profiling.py`: Calcula medias/modas por cluster sobre `feature_matrix.npy` y documenta el failure analysis del ruido DBSCAN en `reports/cluster_profiles.md`, dando evidencia trazable a los perfiles antes solo ilustrativos.
    * `src/recommender_hybrid.py` (extendido): añade un cuarto componente $w_G \cdot \text{PageRank}$ al ensamble y ejecuta un barrido de ablación sobre el 4-simplex de pesos, produciendo el sistema `hybrid_v2_graph` evaluado en `evaluation.py`.
    * `src/demo_app.py`: aplicación Streamlit interactiva de cierre — selecciona un household, muestra su cluster de comportamiento, sus top-5 recomendaciones híbridas y el grafo de co-ocurrencia con esas recomendaciones resaltadas (solo lectura, no escribe artefactos).
    * `run_pipeline.py`: orquestador de un solo comando que reemplaza los 20+ pasos manuales del runbook, con modos `--stage`/`--from`/`--skip-ingestion` para ensayos de demo sin credenciales.
    * `tests/`: 35 pruebas de humo (`pytest`) que verifican shapes, rangos y consistencia de los artefactos generados por cada etapa.
    * `reports/monitoring_plan.md`, `reports/limitations_and_future_work.md`, `reports/final_report.md`: plan de operacionalización, limitaciones consolidadas e informe técnico final de 13 secciones exigidos en la Semana 14.

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
│       ├── evaluation_table.csv    # Cuadro comparativo oficial: 6 sistemas (popularity, pagerank, content, cf, hybrid, hybrid_v2_graph)
│       ├── hybrid_ablation.csv     # Registro numérico completo de la rejilla de pesos (3D y 4D con PageRank)
│       ├── hybrid_meta.json        # Pesos óptimos seleccionados por ablación ($w_C,w_F,w_E,w_G$)
│       ├── error_analysis.csv      # Segmentación de auditoría cualitativa de los 5 Strong y Failure Cases
│       ├── evaluation_summary.json # Summary con metadatos nativos del protocolo Cloze Task Style
│       ├── kitchen_graph.gexf      # Grafo no dirigido de co-ocurrencia de productos
│       └── graph_metrics.json      # Métricas de red y diccionario de centralidad PageRank
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
│   ├── graph_construction.py   # Generador topológico del grafo desde logs de co-ocurrencia
│   ├── graph_analytics.py      # Motor de cálculo de componentes conexas y PageRank
│   ├── cluster_profiling.py    # (NUEVO) Perfiles por cluster + failure analysis del ruido DBSCAN
│   └── demo_app.py             # (NUEVO) Demo final interactivo Streamlit (household -> cluster -> recomendación -> grafo)
├── tests/                       # (NUEVO) 35 pruebas de humo pytest (shapes/rangos de artefactos por etapa)
├── run_pipeline.py               # (NUEVO) Orquestador de un solo comando para el pipeline completo (Hito 1-6)
├── pytest.ini                    # (NUEVO) Configuración de pytest (testpaths=tests)
├── notebooks/                  # Jupyter Notebooks de EDA, experimentos de recomendación y demo de presentación
├── reports/
│   ├── figures/                # Visualizaciones y curvas de aprendizaje exportadas automáticamente
│   │   ├── hito4/                  # Plots del hito: sweeps de lambda, ablación y distribuciones IDF
│   │   └── *.png                   # Scatter plots de t-SNE, scree plots de PCA y siluetas
│   ├── graph_analytics_report.md # Justificación técnica e interpretación de redes (Hito 5) + ablación PageRank-híbrido (Hito 6)
│   ├── cluster_profiles.md       # (NUEVO) Perfiles de los 38 clusters + failure analysis del ruido
│   ├── monitoring_plan.md        # (NUEVO) Plan de monitoreo/operacionalización (Semana 14)
│   ├── limitations_and_future_work.md # (NUEVO) Limitaciones consolidadas y trabajo futuro (Semana 14)
│   ├── final_report.md           # (NUEVO) Informe técnico final de 13 secciones (Semana 14)
│   └── *.md                    # Reportes técnicos e informes descriptivos indexados por hitos
├── Informes/                    # Informes LaTeX/PDF/PPTX de defensa formal por hito
├── runbook.md                  # Manual operativo con secuencias explícitas de comandos de consola
└── requirements.txt            # Dependencias del proyecto congeladas con versiones estrictas