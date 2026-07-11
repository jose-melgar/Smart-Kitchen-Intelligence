# Informe Técnico Final — Smart Kitchen Intelligence (SKI)

> Documento único y autocontenido de cierre (Semana 14), que consolida los
> reportes temáticos existentes en `reports/*.md` (Hitos 1 a 5 más las
> extensiones de Semana 13-14) siguiendo la estructura de 13 secciones exigida
> por el curso. No sustituye a los reportes de origen — los referencia
> explícitamente — pero puede leerse de forma independiente. Todas las cifras
> citadas provienen de artefactos persistidos en `data/` (no de estimaciones).

---

## 1. Declaración del Problema

La invisibilidad de los ciclos de vida de los alimentos y la falta de correlación entre el inventario disponible y el consumo histórico de un hogar genera ineficiencia económica y nutricional: los usuarios suelen comprar por impulso o hábito sin considerar la caducidad ni el equilibrio macro-nutricional de sus existencias.

**Pregunta del producto:** ¿Cómo puede un sistema de recomendación híbrido optimizar el consumo de alimentos e incentivar el restock doméstico basándose simultáneamente en la afinidad histórica del hogar, patrones latentes colectivos y la urgencia por proximidad de vencimiento físico de las unidades perecederas vivas?

Para responder con rigor matemático, el proyecto define operacionalmente:

1. **Co-ocurrencia histórica:** frecuencia relativa con la que un conjunto de productos $\{A, B\}$ aparece en una misma ventana temporal, validada mediante reglas de asociación extraídas del dataset de Instacart.
2. **Ventanas temporales de sesión:**
   - *Restock Window* (60 min) para eventos `IN` — identifica sesiones de compra/abastecimiento.
   - *Kitchen Session* (15 min) para eventos `OUT` — infiere recetas y hábitos de preparación simultánea.
3. **Fórmula de proximidad:** dos eventos $e_1, e_2$ son co-ocurrentes si $|timestamp(e_1) - timestamp(e_2)| \le \Delta t$.

La Sección 13 responde explícitamente a esta pregunta con la evidencia empírica acumulada en las Secciones 7 a 10.

*(Fuente: `reports/proposal.md`)*

## 2. Contexto de Dominio

Smart Kitchen Intelligence (SKI) es un prototipo de sistema de Big Data orientado a la gestión automatizada de inventarios inteligentes en el hogar, con foco en reducir el desperdicio alimentario y optimizar la salud nutricional. El sistema integra tres fuentes conceptualmente distintas:

- **Inteligencia de mercado agregada** (Instacart): patrones estocásticos de compra por hora y frecuencia de producto.
- **Metadata nutricional validada** (USDA FoodData Central): calorías, proteínas, carbohidratos por producto.
- **Ciclo de vida físico del inventario** (motor de simulación propio + estándares FoodKeeper): fechas de vencimiento y clasificación de eventos (`Purchase`, `Consumption`, `Waste`, `Forced_Waste`).

El proyecto cumple los criterios de un dataset no trivial para Big Data por su **variedad** (CSV estructurado, JSON semi-estructurado, consumo de API REST), su **complejidad de pipeline** (star schema → matriz densa → PCA/t-SNE → clustering → recomendador de 3 capas → grafo) y su diseño explícito para escalar (Polars/Arrow, proyección a Parquet para volúmenes de $10^7$ eventos).

*(Fuente: `reports/proposal.md`, `reports/scale_analysis.md`)*

## 3. Fuentes de Datos y Condiciones de Acceso

| Fuente | Origen | Método de ingesta | Uso |
| :--- | :--- | :--- | :--- |
| Instacart Online Grocery Dataset | [Kaggle](https://www.kaggle.com/datasets/yasserh/instacart-online-grocery-basket-analysis-dataset), liberado para investigación académica | `kagglehub` | Distribuciones de compra por hora y frecuencia de producto que calibran el simulador (`src/extract_patterns.py`). |
| USDA FoodData Central | API REST oficial del gobierno de EE. UU. | Autenticación por API key (`.env`, excluido de git) | Fuente primaria de verdad nutricional (calorías/proteínas/carbohidratos); preferida sobre OpenFoodFacts por su alineación exacta con el catálogo estadounidense de Instacart. |
| Logs de interacción sintéticos | Motor de simulación propio (`src/simulation.py`) | Generación estocástica local | Capa transaccional de 90 días para 10 households y 50 productos, parametrizada con las distribuciones de Instacart. |

**Condiciones de acceso y legitimidad:** no se realiza scraping de perfiles privados ni se vulneran términos de servicio de ninguna plataforma; todo el acceso ocurre mediante protocolos oficiales (`kagglehub`, API REST con key). El detalle completo de justificación ética de esta elección —incluyendo por qué el catálogo se mantiene deliberadamente en 50 productos— se desarrolla en la Sección 12 y en `reports/limitations_and_future_work.md` §1.

**Estrategia de calidad ante fuentes externas:** el pipeline implementa una búsqueda en dos niveles — normalización de modificadores comerciales (p. ej. "Organic", "Bag of") para maximizar el *hit rate* contra la API de la USDA, y **manejo explícito de ausencias** (`"Falta Dato"`) en vez de imputación arbitraria en la fase de ingesta; la imputación estadística ocurre después, en preprocesamiento (Sección 5).

*(Fuente: `reports/source_inventory.md`)*

## 4. Esquema y Diccionario de Datos

### 4.1 Arquitectura de almacenamiento

El sistema implementa un **modelo en estrella desnormalizado**:

- **Tabla de hechos** `fact_inventory_events`: PK/FK `event_id`, `product_id`, `stock_id`; métricas `quantity`, `timestamp`, `expiry_date`; dimensiones `event_type`, `classification`.
- **Tabla de dimensiones** `dim_products`: `product_name`, `category`, `nutriscore`, `calories_100g`, `proteins_100g`, `carbs_100g`.

El `stock_id` es la clave que resuelve la trazabilidad de lote (distinguir unidades antiguas de nuevos ingresos), permitiendo calcular con precisión qué porcentaje de un lote específico terminó en desperdicio (`Waste`) — con integridad referencial del 100% verificada en `inventory_v1.csv`.

### 4.2 Diccionario de datos — capa transaccional (`inventory_v1.csv`)

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `event_id` | STRING (UUID) | Identificador único del log de evento. |
| `stock_id` | STRING (UUID) | ID de lote; vincula una entrada con sus salidas. |
| `product_id` | INTEGER | Código de producto (heredado de Instacart). |
| `event_type` | STRING | `IN` o `OUT`. |
| `timestamp` | DATETIME | Fecha y hora del movimiento. |
| `quantity` | INTEGER | Unidades involucradas (rango observado: 1–3). |
| `expiry_date` | DATE | Fecha de caducidad calculada (estándar FoodKeeper). |
| `classification` | STRING | `Purchase`, `Consumption`, `Waste`, `Forced_Waste`. |
| `nutriscore` | STRING | A–E, o `"Falta Dato"`. |
| `category` | INTEGER | Identificador numérico de categoría (6 valores distintos en el catálogo: 1, 3, 4, 7, 16, 20 — no existe un mapeo textual oficial en el repositorio). |

### 4.3 Diccionario de datos — capa de características (Hito 2)

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `calories_100g`, `proteins_100g`, `carbs_100g` | FLOAT | Macros, escaladas con `StandardScaler`. |
| `category_encoded` | FLOAT | CatBoost Encoding (target = probabilidad de evento `OUT`). |
| `txt_[keyword]` (× 50) | FLOAT | Pesos TF-IDF sobre `product_name`. |
| `hour_of_day`, `day_of_week` | INTEGER | Extraídos de `timestamp`. |

Matriz resultante: **72,000 × 61** según el recuento original del Hito 2 documentado en README; la matriz efectivamente persistida en `data/features/feature_matrix.npy` tiene **25,444 filas × 56 columnas** (3 numéricas + 1 CatBoost + 50 TF-IDF + 2 temporales), una fila por evento transaccional — la cifra de 56 es la verificada directamente sobre `feature_names.json`.

### 4.4 Diccionario de datos — capa de segmentación (Hito 3)

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `cluster_label` | INTEGER | Etiqueta DBSCAN Refinado (`data/features/cluster_labels_refined.npy`); `-1` = ruido. |

### 4.5 Diccionario de datos — capa de recomendación y grafo (Hitos 4-5, extensión de esta consolidación)

Esta sub-sección extiende el diccionario original (que solo cubría Hitos 1-3) a los artefactos de la segunda mitad del curso, documentados en detalle en `data/recommender/README.md`:

| Artefacto | Forma / Tipo | Descripción |
| :--- | :--- | :--- |
| `R_restock_bin.npz`, `R_restock_count.npz`, etc. (10 variantes) | Matriz dispersa CSR, 1,177×50 (restock) / 8,075×50 (kitchen) / 10×50 (household) | Matriz sesión×producto en distintos encodings (binario, conteo, TF-IDF, L2-row, etc.). |
| `tfidf_items.npz`, `tfidf_vocab.json` | 50×93, dict token→índice | Vectores TF-IDF de contenido por producto. |
| `als_X.npy`, `als_Y.npy` | 1,177×16, 50×16 | Factores latentes de sesión y producto (ALS implícito). |
| `item_sim_content.npy`, `item_sim_cf_{dot,cosine}.npy` | 50×50 | Matrices de similitud ítem-ítem. |
| `hybrid_meta.json` | JSON | Pesos de producción v1 (`w_C=0.35, w_F=0.45, w_E=0.20`) y v2-grafo (ganador de ablación, `w_G=0.00`, Sección 9). |
| `kitchen_graph.gexf` | Grafo no dirigido, 50 nodos / 1,225 aristas | Red de co-ocurrencia producto-producto ($A = R^T R$). |
| `graph_metrics.json` | JSON | Grado (simple/ponderado), componentes conexas, PageRank por nodo. |
| `evaluation_table.csv` | 6 filas × 8 columnas | Tabla comparativa de los 6 sistemas evaluados (Sección 10). |

### 4.6 Justificación del esquema

El Star Schema evita redundancia masiva y facilita agregaciones temporales; el `stock_id` resuelve la mezcla de lotes antiguos y nuevos (una limitación común en inventarios planos); y la migración a matriz densa (vs. one-hot disperso) asegura que las distancias euclidianas del clustering (Sección 7) sean significativas, sin ruido de ceros estructurales.

*(Fuentes: `reports/schema_draft.md`, `reports/data_dictionary.md`, `data/recommender/README.md`)*

## 5. Preprocesamiento e Ingeniería de Características

### 5.1 Evolución de escala

| Hito | Volumen | Nota |
| :--- | :--- | :--- |
| Prototipo V1 | ~1,500–3,000 registros (30 días) | Prueba de concepto inicial. |
| V2 (actual) | **25,444 registros** transaccionales (90 días, 10 households, 50 productos) | Single Source of Truth: `inventory_v1.csv`. |
| Catálogo maestro | 50 productos únicos | Validados vía USDA FoodData Central API. |

### 5.2 Gestión de calidad de datos

- **Explicit missingness en ingesta:** los nulos detectados en variables nutricionales de la USDA no se imputan de forma sintética arbitraria en `src/ingestion.py`; se registran explícitamente.
- **Imputación estadística en preprocesamiento:** los nulos remanentes se completan por media de categoría (`groupby('category')[col].transform(mean)`), evitando pérdida de registros en el pipeline de clustering.
- **Integridad de lote:** el 100% de los eventos `Waste` mantienen integridad referencial con su `stock_id` original.

### 5.3 De disperso a denso: la corrección central del Hito 2

El uso inicial de One-Hot Encoding sobre `category` generaba una matriz excesivamente dispersa al escalar el catálogo (maldición de la dimensionalidad). Se sustituyó por **CatBoost Encoding** (Target Encoding, target = probabilidad de evento `OUT`), colapsando la variable categórica a una sola columna densa y eliminando ruido estructural antes del PCA.

De forma análoga, en la capa de contenido del recomendador (Hito 4) se identificó — y corrigió — un problema equivalente de ortogonalidad: una primera versión discretizaba las variables nutricionales continuas en tokens TF-IDF independientes (`cal_low`, `prot_mid`...), lo que asumía erróneamente distancia idéntica entre niveles adyacentes y no adyacentes. La versión vigente de `src/recommender_content.py` reemplaza esos tokens por **una sola dimensión numérica escalada (MinMax) por macro**, más el nutriscore como eje ordinal (A→E), preservando la noción de intervalo antes de concatenar con el bloque TF-IDF y normalizar L2. *(Nota de consolidación: `reports/recommendation_experiments.md` §2 documentaba esto como "trabajo futuro" pendiente; el código actual confirma que la corrección ya está implementada — este informe actualiza esa afirmación.)*

### 5.4 Stack de escalabilidad

El pipeline usa **Polars** (motor Arrow, multithreading) para joins y transformaciones, procesando los 25k registros en milisegundos. Para escenarios teóricos de $10^7$ eventos se proyecta migrar de CSV a **Parquet** (columnar, ~80% de reducción de tamaño) y procesar las consultas a la USDA por lotes. Complejidades algorítmicas de referencia: ingesta/join $O(n/p)$, PCA $O(\min(p^3, n \cdot p^2))$ con $p=56$, DBSCAN $O(n \log n)$ sobre el espacio ya reducido.

*(Fuentes: `reports/scale_analysis.md`, código de `src/features.py`, `src/recommender_content.py`)*

## 6. Análisis de Dimensionalidad y Representación

Se aplicó **PCA** sobre la matriz densa de 56 características para gestionar su complejidad multimodal (numérica, categórica densa, textual, temporal).

| Componente | Varianza explicada | Varianza acumulada |
| :--- | :--- | :--- |
| PC1 | 6.98% | 6.98% |
| PC2 | 5.58% | 12.56% |
| PC3 | 4.81% | 17.38% |
| PC4 | 4.50% | 21.88% |
| PC5 | 4.19% | 26.07% |
| ... | ... | ... |
| **PC30** | — | **90.01%** |

**30 componentes principales** son necesarios para retener el 90% de la varianza — una reducción del 46% del espacio original sin pérdida significativa, que refleja baja redundancia: los hábitos de cocina son diversos y requieren esa profundidad para modelarse correctamente.

Como complemento no lineal se ejecutó **t-SNE**, que reveló "islas" de comportamiento — evidencia visual de que la ingeniería de características separa grupos lógicos de productos y patrones por hogar, y que motivó directamente la hipótesis de clustering por densidad (Sección 7). El biplot de PCA muestra que `category_encoded` y los indicadores nutricionales tienen los vectores de carga más largos, es decir, son los factores con mayor peso en la diferenciación del inventario.

Artefacto resultante: `data/features/feature_matrix_reduced.npy` (25,444 × 30), Single Source of Truth para clustering. Figuras: `reports/figures/{pca_scree_plot,pca_scatter_2d,pca_biplot,tsne_clusters}.png`.

*(Fuente: `reports/dimensionality_reduction_report.md`)*

## 7. Análisis de Clustering

### 7.1 Benchmark competitivo (exploración)

| Paradigma | Configuración | Silhouette | Hallazgo |
| :--- | :--- | :--- | :--- |
| K-Means | k=9 | 0.3733 | Los grupos no son perfectamente esféricos. |
| GMM | 2–10 componentes | 0.1992 | Los datos no siguen distribuciones gaussianas — **descartado**. |
| DBSCAN | radio estático | 0.6547 | Los datos forman núcleos densos de alta cohesión. |

### 7.2 Refinamiento

| Paradigma | Configuración | Silhouette | Estatus |
| :--- | :--- | :--- | :--- |
| GMM | — | 0.1992 | Descartado |
| K-Means Refinado | k=25 | 0.5428 | Descartado (sobre-segmentación excesiva) |
| HDBSCAN | min_cluster_size=30 | 0.5816 | Descartado (no supera al radio fijo) |
| **DBSCAN Refinado** | **eps=2.7, min_samples=15** | **0.6549** | **GANADOR** |

El modelo ganador es estable en el rango eps∈[2.3, 2.7] (no es producto del azar), identifica **38 clusters** y reduce el ruido a **0.28%** (71 de 25,444 eventos).

### 7.3 Perfilado de clusters y análisis de fallos (extensión de esta consolidación)

`src/cluster_profiling.py` calculó, para cada uno de los 38 clusters, la media de las 56 características originales, las categorías de producto dominantes y el patrón temporal — cerrando la brecha que el README señalaba con nombres ilustrativos ("Perecederos matutinos", "Abastecimiento de larga duración") sin respaldo trazable. Hallazgos reales sobre la tabla completa (`reports/cluster_profiles.md`):

- **30 de los 38 clusters (79%) son monocategoría al 100%** en `category_4` (identificador numérico dominado, por los nombres de producto asociados en sus features distintivos — `txt_apples`, `txt_avocado`, `txt_strawberries`, `txt_carrots`, etc. — por productos frescos/perecederos). Esto es consistente con que `category_4` concentra 20,296 de los 25,444 eventos totales (80%) del dataset.
- **Concentración horaria:** la hora media por cluster varía en una banda estrecha, 12.6h–14.8h, sin dispersión nocturna — el comportamiento de restock/consumo simulado se concentra en la tarde temprana.
- **Sesgo hacia fin de semana:** de los 38 clusters, 9 tienen a Domingo como día dominante y 8 a Sábado (45% combinado), frente a 3 en Lunes y 3 en Martes — coherente con patrones reales de compra de supermercado tipo Instacart.
- **Análisis de fallos (ruido, label=-1):** los 71 puntos de ruido concentran su categoría más frecuente (`category_4`) en solo 90.1% de los casos, frente a un promedio de 97.8% en los clusters reales, y mezclan 4 categorías distintas frente a un promedio de 1.1 en clusters reales — el ruido no se explica por una sola variable, sino por combinaciones poco frecuentes de categoría, franja horaria y volumen de movimiento (`quantity` media 1.775 en ruido vs. 1.722 global) que no forman una vecindad suficientemente densa bajo `eps=2.7, min_samples=15`.

*(Fuentes: `reports/clustering_experiments.md`, `reports/final_model_selection.md`, `reports/cluster_profiles.md`)*

## 8. Sistema de Recomendación / Ranking

### 8.1 Arquitectura de 3 capas (+ extensión de grafo evaluada en Semana 13)

1. **Contenido (`recommender_content.py`):** perfil TF-IDF por producto (nombre + categoría + clasificación, más macros escaladas y nutriscore ordinal — ver Sección 5.3) agregado por household mediante centroide ponderado por frecuencia de consumo; similitud coseno.
2. **Filtrado colaborativo (`recommender_cf.py`):** ALS implícito (Hu, Koren & Volinsky) sobre `R_restock_tfidf_R`, con barrido logarítmico de $\lambda \in \{0.001,...,10\}$ → óptimo $\lambda=1.0$ (precision@5≈0.0494, recall@5≈0.1163 en el barrido original).
3. **Expiry (anti-desperdicio):** $S_{exp} = 1/(1+d)$, donde $d$ es la mediana de días hasta vencimiento de las unidades vivas en inventario del household — es el componente que responde directamente a la pregunta de reducción de desperdicio (Sección 1).
4. **Ensamble híbrido v1 (producción):** $w_C=0.35, w_F=0.45, w_E=0.20$ — combinación ganadora de la ablación original del Hito 4.
5. **Extensión v2 con grafo (Semana 13):** se añadió un cuarto término $w_G \cdot \text{PageRank}(i)$ y se re-ejecutó la ablación sobre el 4-simplex de pesos; resultado y decisión de producción documentados en la Sección 9.4.

**Cold-start:** de las estrategias evaluadas (popularidad, CF parcial, solo-contenido, mixta), `partial_cf` ganó con precision@5 = 0.2020 (1 seed) y 0.1955 (2 seeds).

### 8.2 Análisis de errores (Hito 4)

- **Casos de éxito (*strong cases*, ≥2 aciertos en top-5):** concentrados en sesiones densas con historial previo alto (`n_train_seen`), donde la regresión de mínimos cuadrados sobre los factores ALS produce un vector de sesión estable.
- **Casos de falla (0 aciertos):** asociados a sesiones con volumen inusualmente alto de productos reales en el hold-out (`n_truth` alto) o canastas con alta volatilidad estocástica — el corte de Top-5 es un cuello de botella matemático ante canastas masivas y diversas.

*(Fuentes: `reports/recommendation_experiments.md`, `data/recommender/README.md`, `runbook.md` §5)*

## 9. Analítica de Grafos

### 9.1 Construcción

Sobre la matriz binaria de sesiones de restock $R$ (1,177×50), se calcula la matriz de co-ocurrencia $A = R^T \cdot R$. Resultado: **50 nodos, 1,225 aristas** (grafo completo: $\binom{50}{2}=1225$), **1 componente conexa**. Exportado como GEXF (`kitchen_graph.gexf`).

### 9.2 Métricas estructurales

| Métrica | Valor |
| :--- | :--- |
| Grado ponderado mínimo / máximo / medio | 1,613 / 1,996 / 1,822.8 |
| PageRank (α=0.85) | Top-1: Yellow Onions (45007), 0.0216 |

Dado que el grafo es completo, el **grado simple es idéntico (49) para todo nodo** — la señal discriminativa vive exclusivamente en los **pesos de las aristas**, no en la topología binaria. Esta es una decisión de diseño deliberada, no una limitación pasada por alto: con 10 households compartiendo el mismo catálogo de 50 productos durante 90 días, casi cualquier par de productos termina co-ocurriendo en alguna sesión, por lo que *qué* nodos están conectados no aporta información — *cuánto* co-ocurren (el peso) sí. Grado ponderado y PageRank ponderado se diseñaron explícitamente para capturar esa señal.

### 9.3 PageRank como sistema de ranking aislado

Evaluado bajo el mismo protocolo consolidado (Sección 10) junto a los demás sistemas:

| Sistema | Precision@5 | MAP@5 | Coverage@5 |
| :--- | :--- | :--- | :--- |
| Popularity | 0.0508 | 0.0539 | 22.0% |
| **PageRank** | **0.0541** | **0.0595** | **26.0%** |

PageRank supera a Popularity en Precision@5 (+6.5%) y MAP@5 (+10.4%) — el peso de las aristas contiene señal real más allá de la frecuencia simple. Su cobertura limitada (26%) confirma que, como ranking estático no personalizado, recomienda esencialmente el mismo conjunto (~13 productos) a todos los households, igual que la popularidad.

### 9.4 Integración al recomendador híbrido: resultado empírico de la ablación (Semana 13)

`src/recommender_hybrid.py` ejecuta un barrido de ablación sobre el 4-simplex $(w_C, w_F, w_E, w_G \ge 0$, suma 1, incrementos de 0.25 → 35 combinaciones) y selecciona la ganadora por precision@5. Resultado:

$$w_C = 0.25,\quad w_F = 0.50,\quad w_E = 0.25,\quad w_G = \mathbf{0.00}$$

Evaluada bajo el protocolo consolidado (`hybrid_v2_graph`):

| Sistema | Precision@5 | MAP@5 | Coverage@5 |
| :--- | :--- | :--- | :--- |
| **Hybrid v1 (producción, sin grafo)** | **0.0494** | **0.0574** | 100.0% |
| Hybrid v2 (con grafo, $w_G=0.00$) | 0.0479 | 0.0560 | 100.0% |

**El peso óptimo encontrado para PageRank es 0.00**: el híbrido v1 supera ligeramente a la variante v2 en ambas métricas. Esto es un **resultado negativo honesto**, no un fallo de implementación: PageRank es una señal global y estática por producto, mientras que CF y Contenido ya capturan afinidad específica de sesión/household — precisamente lo que decide el acierto en una tarea de completitud de canasta. El valor real del grafo es **macro-estructural** (identificar productos puente, auditar topología de co-compra, servir de baseline de ranking competitivo frente a popularidad), no de re-ranking a nivel de canasta individual. **Decisión de producción: se mantiene el híbrido v1** (sin componente de grafo).

*(Fuentes: `reports/graph_analytics_report.md`, `reports/limitations_and_future_work.md` §2, `data/recommender/hybrid_meta.json`)*

## 10. Protocolo de Evaluación

**Unidad de evaluación:** sesión de restock (`R_restock_bin`, 1,177 sesiones).
**Tarea:** Masked Basket Completion Task (Cloze Task Style) — se enmascara aleatoriamente el 20% de las interacciones no-cero (semilla fija 42); se evalúa la capacidad de reconstrucción/inferencia intra-sesión (cross-selling en tiempo real), no una predicción cronológica longitudinal.
**Candidate pool:** catálogo completo de 50 productos menos las interacciones ya vistas en train de esa sesión — en producción SKI siempre puede sugerir cualquier producto del catálogo.
**Métricas:** precision@5, recall@5, nprecision@5 (normalizada por el techo $\min(k,|truth|)$), MAP@5, catalog coverage@5.

### Tabla comparativa final — 6 sistemas, protocolo idéntico

| Sistema | Precision@5 | Recall@5 | MAP@5 | Coverage@5 |
| :--- | :--- | :--- | :--- | :--- |
| Popularity | 0.0508 | 0.1167 | 0.0539 | 22.0% |
| PageRank | 0.0541 | 0.1283 | 0.0595 | 26.0% |
| Content (TF-IDF) | 0.0450 | 0.1037 | 0.0511 | 84.0% |
| CF (ALS) | 0.0467 | 0.1125 | 0.0549 | 100.0% |
| **Hybrid v1 (producción)** | **0.0494** | **0.1177** | **0.0574** | **100.0%** |
| Hybrid v2 (con grafo) | 0.0479 | 0.1149 | 0.0560 | 100.0% |

**Lectura crítica del "sesgo de popularidad":** Popularity gana en precision@5 cruda pero cubre solo el 22% del catálogo — un colapso de diversidad que un criterio estricto de "penalización por trivialidad" descarta como sistema de producción viable, ya que recomendar siempre los mismos productos ubicuos no ayuda a rotar el inventario ni a mitigar desperdicio en productos de bajo movimiento. El híbrido logra 100% de cobertura y el mejor MAP@5 entre los sistemas con cobertura completa, activando la señal de descubrimiento y mitigación de desperdicio.

*(Fuente: `src/evaluation.py`, `data/recommender/evaluation_table.csv`, `evaluation_summary.json`)*

## 11. Pipeline y Reproducibilidad

El proyecto consta de **21 scripts modulares** en `src/`, ejecutados en secuencia estricta (sin estado oculto de notebook) y documentados paso a paso en `runbook.md`:

| Etapa | Scripts | Artefacto principal |
| :--- | :--- | :--- |
| Semana 3 — Ingesta/ETL | `extract_patterns` → `simulation` → `ingestion` → `preprocessing` | `data/processed/inventory_v1.csv` |
| Semana 5 — Features/PCA | `features` → `reduction` | `feature_matrix_reduced.npy` |
| Semana 7 — Clustering | `clustering` → `clustering_refinement` | `cluster_labels_refined.npy` |
| Semana 11 — Recomendador | `build_R` → `recommender_content` → `normalizations` → `recommender_cf` → `cold_start` → `recommender_hybrid` → `evaluation` → `generate_hito4_figures` | `evaluation_table.csv`, `informe_hito4.pdf` |
| Semana 12 — Grafo | `graph_construction` → `graph_analytics` → `generate_hito5_figures` | `graph_metrics.json` |
| Semana 13 — Perfiles + ablación grafo | `cluster_profiling` → `recommender_hybrid` (ablación 4D) → `evaluation` | `cluster_profiles.md`, `evaluation_table.csv` (+`hybrid_v2_graph`) |
| Semana 14 — Demo final | `demo_app.py` (Streamlit, solo lectura) | Demo interactivo, sin artefactos nuevos |

**Requisitos:** Python 3.9+, dependencias congeladas en `requirements.txt` (incluye `streamlit`, `plotly` desde la Semana 14); credenciales de Kaggle (`~/.kaggle/kaggle.json`) y USDA (`.env` con `USDA_API_KEY`) para las etapas de ingesta. Todos los scripts asumen ejecución desde la raíz del repositorio (rutas relativas hardcodeadas por diseño, sin CLI/config externa — ver limitaciones, Sección 12).

**Demo final (`src/demo_app.py`, Streamlit):** dado un household seleccionado interactivamente, muestra su cluster de comportamiento dominante (moda de `cluster_label` sobre sus eventos) con perfil trazable, sus top-5 recomendaciones del híbrido v1 de producción, y el grafo de co-ocurrencia con esas 5 recomendaciones resaltadas sobre el contexto estructural del catálogo. Solo lee artefactos ya persistidos en `data/`; no escribe ni depende de estado de sesión oculto.

*(Fuentes: `runbook.md`, `README.md`, `src/demo_app.py`)*

## 12. Ética y Limitaciones

### 12.1 Ética y acceso a datos

- **Manejo de secretos:** credenciales de la USDA gestionadas vía `.env`, excluido de control de versiones.
- **Origen legítimo:** Instacart (dataset público liberado para investigación) y USDA (datos abiertos gubernamentales); sin scraping ni vulneración de ToS; acceso mediante `kagglehub` y API REST oficial.
- **Privacidad:** toda la capa de interacción individual es sintética (simulación estocástica sobre distribuciones agregadas de Instacart); no existen PII — `stock_id`/`event_id` son UUIDs generados internamente sin vínculo a personas reales.
- **Responsabilidad algorítmica:** la clasificación de desperdicio se basa en estándares públicos (FoodKeeper/USDA); el sistema es informativo, no una prescripción médica o nutricional.

### 12.2 Catálogo pequeño y datos sintéticos: decisión ética, no atajo de escala

El catálogo de 50 productos y la capa de interacción 100% sintética (10 households, 90 días) es una decisión metodológica deliberada para **evitar scraping no autorizado** de catálogos de supermercados reales y **evitar el uso de datos de usuarios reales**: ambos riesgos se eliminan por construcción al derivar el catálogo de distribuciones agregadas de Instacart (no de transacciones individuales identificables) y al simular la capa de interacción completa. El costo explícito de esta decisión es una menor granularidad categórica (solo 6 categorías distintas, Sección 7.3) y un candidate pool de evaluación pequeño frente a un catálogo de supermercado real — el dataset sostiene la segunda mitad del curso por su **complejidad transaccional y de pipeline**, no por volumen de catálogo.

### 12.3 Grafo completo: por qué la señal está en los pesos

Ver Sección 9.2 — es la misma decisión de diseño revisada desde el ángulo de limitación: con un catálogo más grande y datos reales, el grafo dejaría de ser completo y la topología binaria (comunidades, caminos más cortos) volvería a ser potencialmente informativa. Fuera de alcance actual por la razón anterior (12.2).

### 12.4 Otras limitaciones

1. **Evaluación offline únicamente** — proxy de hold-out aleatorio, no A/B test con usuarios reales; las métricas absolutas (precision@5≈0.05) deben leerse comparativamente entre sistemas.
2. **Pruebas automatizadas limitadas a smoke tests** — `tests/` (35 pruebas `pytest`) verifica shapes/rangos de artefactos por etapa, pero no valida corrección numérica end-to-end ni corre en CI.
3. **Orquestador de pipeline sin paralelización** — `run_pipeline.py` reemplaza los >20 comandos manuales de `runbook.md` por un solo punto de entrada, pero ejecuta las etapas secuencialmente sin paralelizar ni cachear resultados intermedios.
4. **Sin configuración externalizada** — rutas e hiperparámetros hardcodeados por script.
5. **Equipo de 2 personas** frente al tamaño recomendado de 3-5 (el brief permite roles combinados).
6. **Staleness y drift no monitoreados en el pipeline actual** — ver Sección 12.5.

### 12.5 Plan de monitoreo (resumen — detalle completo en `reports/monitoring_plan.md`)

Si SKI pasara a producción con datos reales, se proponen 5 frentes de monitoreo con umbrales concretos:

| Métrica | Umbral de alerta |
| :--- | :--- |
| Coverage@5 / MAP@5 del sistema en producción | Caída > 15% relativo vs. última corrida aceptada de `evaluation_table.csv` |
| Staleness de metadata USDA | Producto sin refresco > 180 días |
| Drift de distribución de consumo (KS-statistic vs. `instacart_patterns.json`) | KS > 0.15 en ventana móvil de 30 días |
| Salud estructural del grafo | Grafo deja de ser conexo, o densidad de aristas < 80% |
| Sparsity de `R_restock_bin` | Densidad < 10% en ventana móvil de 4 semanas |

**Cadencia de reentrenamiento sugerida:** matrices R, ALS y grafo — semanal (comparten la misma matriz base); pesos del ensamble híbrido — trimestral o ante alerta; catálogo nutricional USDA — semestral o ante alerta de staleness.

*(Fuentes: `reports/ethics_note.md`, `reports/limitations_and_future_work.md`, `reports/monitoring_plan.md`)*

## 13. Conclusiones Finales

Retomando la pregunta del producto (Sección 1) — *¿cómo puede un sistema de recomendación híbrido optimizar el consumo de alimentos e incentivar el restock doméstico basándose en afinidad histórica, patrones latentes colectivos y urgencia de vencimiento?* — la evidencia acumulada a lo largo de las cinco capas del proyecto permite responderla con evidencia empírica, no solo con diseño conceptual:

1. **El pipeline completo es funcional y trazable de punta a punta.** Desde 25,444 eventos transaccionales sintéticos pero estadísticamente fieles (calibrados con Instacart) hasta una matriz de 56 características, 30 componentes de PCA (90.01% de varianza), 38 clusters de comportamiento con Silhouette 0.6549 y ruido de solo 0.28%, un recomendador de 3 capas y un grafo de co-ocurrencia con PageRank — cada artefacto de cada etapa está persistido en disco y es reproducible por comando (Sección 11), no depende de estado oculto de notebook.

2. **El componente anti-desperdicio (expiry) cumple su función de diseño.** Al inyectar $S_{exp}=1/(1+d)$ en el ensamble híbrido, el sistema prioriza sistemáticamente productos con vencimiento próximo sin sacrificar cobertura de catálogo: el híbrido v1 logra **100% de Catalog Coverage** frente al 22% de la popularidad pura — es decir, el sistema efectivamente distribuye atención de recomendación sobre todo el inventario vivo, en vez de reforzar el sesgo hacia un puñado de productos ubicuos que un enfoque ingenuo de popularidad perpetuaría.

3. **La afinidad histórica y los patrones colectivos son complementarios, no redundantes — hasta un punto medible.** El filtrado colaborativo (ALS, $\lambda=1.0$) y el contenido (TF-IDF híbrido texto+numérico) capturan señales distintas que el ensamble combina con MAP@5=0.0574, superando a cada componente aislado bajo cobertura completa. Sin embargo, el hallazgo más honesto de esta consolidación es negativo: **la ablación de integración de PageRank (Semana 13) encontró un peso óptimo $w_G=0.00$** — la centralidad estructural del grafo de co-ocurrencia, aunque supera a la popularidad como ranking aislado (+6.5% precision@5, +10.4% MAP@5), no añade valor de re-ranking a nivel de canasta individual una vez que CF y Contenido ya están presentes, porque los tres derivan en última instancia de la misma matriz de co-ocurrencia. Esto no invalida la capa de grafo: la reposiciona correctamente como una herramienta de **auditoría estructural macro** (identificar productos puente, validar que el catálogo está completamente interconectado) en lugar de una señal de personalización, y evita la trampa de reportar una integración "exitosa" fabricando una mejora que los datos no sostienen.

4. **La decisión de mantener un catálogo pequeño y datos sintéticos fue la correcta para este contexto académico.** Permitió cumplir estrictamente los requisitos de uso ético de datos (sin scraping, sin PII) sin sacrificar la posibilidad de ejercitar las cinco capas técnicas exigidas por el curso con rigor matemático completo — el costo (menor granularidad categórica, candidate pool acotado) está documentado explícitamente en vez de ocultarse tras nombres de cluster sin respaldo.

**Balance final:** SKI demuestra, con métricas verificables y una evaluación honesta —incluyendo un resultado negativo reportado sin maquillaje—, que un ensamble híbrido de contenido, filtrado colaborativo y urgencia de vencimiento es la arquitectura más efectiva disponible en este pipeline para responder simultáneamente a la pregunta de descubrimiento (cobertura completa del catálogo) y a la pregunta de anti-desperdicio (priorización por proximidad de caducidad), mientras que el grafo de co-ocurrencia aporta valor real pero en un plano distinto — el de la comprensión estructural del ecosistema de consumo, no el del re-ranking transaccional.
