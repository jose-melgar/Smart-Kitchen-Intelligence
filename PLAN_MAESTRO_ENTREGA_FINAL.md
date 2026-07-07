# Auditoría Técnica Integral y Plan Maestro — Smart Kitchen Intelligence (SKI)

**Curso:** Big Data (UPC) · **Equipo:** Gabriel Reyna Alvarado, José Melgar Puertas
**Fecha de auditoría:** 2026-07-04 · **Último commit auditado:** `39182a7` (2026-06-26, "Informe, gráficos, script, reportes para hito 5")
**Metodología:** revisión directa del repositorio (código, datos, reportes, notebooks, historial git), sin ejecutar el pipeline completo. Todos los hallazgos citan el archivo/línea que los sustenta.

> **Nota sobre información faltante para esta auditoría:** no tengo la fecha exacta límite de la Semana 14, el peso relativo de cada criterio de la rúbrica, si el informe final debe entregarse en español o inglés, ni la disponibilidad horaria diaria del equipo. El plan diario (Sección 9) asume una ventana de **10 a 14 días naturales** desde hoy, extrapolando el cadencia observada entre hitos (~2 semanas: Hito 4 el 12-13/jun, Hito 5 el 24-26/jun). **Deben ajustar las fechas exactas del plan en cuanto confirmen la fecha real de defensa de Semana 14.**

---

## 1. Auditoría del Estado Actual

### 1.1 Resumen ejecutivo

El proyecto está objetivamente **adelantado**: a la fecha de hoy ya tiene completados los hitos correspondientes a las Semanas 3, 5, 7, 10 y 12 del cronograma oficial (el README interno los llama Hito 1 a Hito 5). Solo falta la **Semana 14 (Entrega Final Integrada y Defensa)** y una extensión auto-propuesta por el equipo ("Semana 13: integración de PageRank al re-ranking híbrido"), que el propio README marca como `🔜 Pendiente`. Las cinco capas obligatorias del "Core Project Shape" del brief están implementadas:

| Capa requerida (brief) | Implementación en SKI | Evidencia |
| :--- | :--- | :--- |
| Catalog layer | `product_catalog.csv`, `dim_products` (50 productos, metadatos USDA) | `data/recommender/product_catalog.csv`, `reports/schema_draft.md` |
| Feature layer | Matriz densa 72,000×61 → PCA 30 componentes (90% varianza) | `data/features/feature_matrix.npy`, `reports/dimensionality_reduction_report.md` |
| Interaction/co-occurrence layer | 10 matrices `R_*` (restock, kitchen, household) en distintos encodings | `data/recommender/R_*.npz`, `data/recommender/README.md` |
| Graph layer | Grafo no dirigido ponderado de co-ocurrencia (50 nodos, 1,225 aristas) + PageRank | `data/recommender/kitchen_graph.gexf`, `reports/graph_analytics_report.md` |
| Pipeline layer | 19 scripts secuenciales documentados en `runbook.md` y README | `src/*.py` |

Esto significa que el proyecto **ya supera el "Minimum Technical Standard for Passing"** del brief (dataset procesado real, representación rigurosa, clustering, recomendación, grafo, pipeline reproducible). El riesgo ya no es de alcance faltante en las capas técnicas centrales, sino de **cierre, consolidación, consistencia documental y preparación de la defensa final**, que es exactamente donde se pierden puntos en la Semana 14 según los "Detailed Evaluation Criteria" del brief (repo structure, comandos claros, artefactos guardados, workflow rerunnable, coherencia de la defensa).

### 1.2 Componentes ya implementados (verificados en el repo)

- **Ingesta y simulación** (`src/extract_patterns.py`, `src/simulation.py`, `src/ingestion.py`): patrones estocásticos desde Instacart (Kaggle) + enriquecimiento nutricional vía USDA FoodData Central API, con fallback documentado. Genera `data/raw/*` (25,445 filas en `movements_raw.csv`).
- **ETL/preprocesamiento** (`src/preprocessing.py`, 54 líneas): produce `data/processed/inventory_v1.csv` (25,445 filas, 9+ columnas), Single Source of Truth.
- **Feature engineering** (`src/features.py`, 67 líneas): matriz 72,000×61 con CatBoost Encoding + TF-IDF + variables temporales.
- **Reducción de dimensionalidad** (`src/reduction.py`, 113 líneas): PCA a 30 componentes (90.01% varianza) + t-SNE. 4 figuras generadas (`scree`, `scatter_2d`, `biplot`, `tsne_clusters`).
- **Clustering** (`src/clustering.py` + `src/clustering_refinement.py`, 362 líneas combinadas): benchmark K-Means (k=2–25), GMM (2–10), DBSCAN y HDBSCAN, con barrido granular de hiperparámetros. Ganador: DBSCAN (eps=2.7, min_samples=15), Silhouette=0.6549, 38 clusters, 0.28% ruido.
- **Motor de recomendación de 3 capas** (`build_R.py`, `recommender_content.py`, `normalizations.py`, `recommender_cf.py`, `cold_start.py`, `recommender_hybrid.py`, `evaluation.py` — 1,597 líneas combinadas): contenido TF-IDF, CF vía ALS implícito con barrido de λ, cold-start (4 estrategias), ensamble híbrido lineal con señal de vencimiento, evaluación consolidada bajo protocolo Masked Basket Completion (Cloze Task).
- **Analítica de grafos** (`graph_construction.py`, `graph_analytics.py`, 122 líneas): grafo de co-ocurrencia vía $R^T R$, métricas de grado ponderado y PageRank, comparación contra popularidad y otros sistemas en la tabla de evaluación consolidada.
- **Documentación de proceso**: 11 reportes en `reports/*.md`, 3 informes LaTeX compilados a PDF (`Informes/informe_hito{3,4,5}.pdf`), 2 presentaciones (`.pptx` + PDF de slides), 25 figuras en `reports/figures/`.

### 1.3 Entregables que ya cumplen los requisitos del curso

Ver la tabla de comparación punto por punto en la Sección 2. En resumen: **Semanas 3, 5, 7, 10 y 12 cumplen sustancialmente**, con matices menores señalados abajo.

### 1.4 Partes incompletas

1. **Análisis de perfil de clusters (`cluster-profile analysis`, requerido explícitamente en Semana 7):** no existe ningún script ni reporte que calcule las características promedio/dominantes por cluster. Los nombres "Perecederos matutinos" y "Abarrotes de larga duración" que aparecen en el `README.md` (sección de estado) **no están respaldados por ningún artefacto de análisis** — no hay `cluster_profile.csv`, ni tabla de medias por cluster, ni script que los genere. Es una afirmación descriptiva sin evidencia trazable. Esto es un riesgo real en la defensa (ver Sección 8).
2. **Análisis de fallos de clustering (`failure analysis`, Semana 7):** existe información parcial (ruido=0.28%, GMM y HDBSCAN descartados por Silhouette inferior), pero no hay un análisis específico de **qué tipo de eventos/productos cayeron en el ruido** ni por qué, que es lo que pide literalmente el brief ("what did not cluster well and why").
3. **Extensión "Semana 13"**: el propio README declara `🔜 Pendiente` la integración del score de PageRank como cuarto componente del recomendador híbrido. Esto ya está diseñado conceptualmente (lo dice `graph_analytics_report.md`, sección 5) pero no implementado.
4. **Demo final desactualizado:** `notebooks/03_presentation_demo.ipynb` cubre únicamente contexto, datos, y PCA (Hitos 1–2). No refleja el clustering, el recomendador híbrido ni el grafo, que son precisamente los componentes más avanzados y diferenciadores del proyecto.

### 1.5 Elementos faltantes (no existen en absoluto)

1. **Reporte técnico final consolidado** que siga la estructura de 13 secciones exigida en "Final Report Structure" del brief. Lo que existe son informes por hito independientes (`informe_hito3.tex/pdf`, `informe_hito4.tex/pdf`, `informe_hito5.tex/pdf`), no una síntesis única end-to-end.
2. **Plan de monitoreo/operacionalización**, requerido explícitamente para la Semana 14 ("one monitoring or operationalization plan"). No existe ningún archivo que lo aborde.
3. **Sección de limitaciones y trabajo futuro consolidada.** Existen menciones dispersas (p. ej. en `reports/recommendation_experiments.md`, sección "Trabajo Futuro" sobre discretización nutricional), pero no un documento único de limitaciones del sistema completo.
4. **Diccionario de datos actualizado.** `reports/data_dictionary.md` solo documenta variables de los Hitos 1–3 (`inventory_v1.csv`, features). No documenta ninguna de las estructuras creadas en Hito 4 (matrices `R_*`, factores ALS, vocabulario TF-IDF) ni Hito 5 (nodos/aristas del grafo, `graph_metrics.json`), a pesar de que el brief pide que el diccionario cubra "the second half of the course" (regla de dataset #4).
5. **Script/orquestador único de pipeline** (`Makefile`, `run_pipeline.py`, o similar). Hoy la reproducción exige ejecutar 19 comandos manuales en orden estricto; no hay un solo comando que reproduzca todo el pipeline de punta a punta.
6. **Pruebas automatizadas** (unit tests / smoke tests) para verificar que los scripts producen las formas de matrices y rangos de valores esperados. No hay carpeta `tests/`.

### 1.6 Problemas de arquitectura, organización o calidad técnica detectados

| # | Hallazgo | Evidencia | Severidad |
| :-- | :--- | :--- | :--- |
| 1 | `requirements.txt` está codificado en **UTF-16LE con CRLF**, no UTF-8. Un `pip install -r requirements.txt` en un clon fresco en Linux/macOS puede fallar o interpretarse mal según la versión de pip. | `file requirements.txt` → `Unicode text, UTF-16, little-endian text, with CRLF line terminators` | **Alta** — rompe la reproducibilidad, criterio explícito de evaluación |
| 2 | Dos notebooks están **completamente vacíos** (0 bytes): `notebooks/01_exploratory.ipynb` y `notebooks/02_scale_analysis.ipynb`, pero el README los presenta como parte de la carpeta "dedicada a EDA y prototipado". | `wc -c notebooks/01_exploratory.ipynb notebooks/02_scale_analysis.ipynb` → `0 0` | **Media-Alta** — un evaluador que los abra encontrará archivos rotos |
| 3 | **`runbook.md` está desincronizado** con el estado real del proyecto: no incluye los pasos del Hito 5 (`graph_construction.py`, `graph_analytics.py`, `generate_hito5_figures.py`). Esos comandos solo aparecen en el `README.md`, que no es el documento designado como runbook oficial. | Comparación línea a línea de `runbook.md` (termina en Hito 4 / Paso 17) vs `README.md` (Quick Start incluye Paso 8, Hito 5) | **Alta** — el brief exige "one runbook explaining how to reproduce the outputs"; un runbook incompleto es un entregable parcialmente incumplido |
| 4 | **Inconsistencia numérica entre reportes**: el `README.md` reporta para el sistema híbrido `MAP@5 = 0.0539` y `P@5 = 0.0455`; el `runbook.md` (Paso 15) reporta `MAP@5 = 0.0539` pero no dice P@5; y `reports/graph_analytics_report.md` (tabla comparativa Hito 5) reporta para el mismo sistema híbrido `Precision@5 = 0.0494` y `MAP@5 = 0.0574`. Son tres cifras distintas para la misma métrica del mismo sistema. | README tabla de estado vs `reports/graph_analytics_report.md` sección 4 | **Alta** — un profesor que cruce cifras entre documentos detectará la inconsistencia; puede parecer falta de rigor o de una única fuente de verdad para las métricas |
| 5 | **Artefactos duplicados y redundantes** en `artifacts/week5/docs/`: cinco versiones de un mismo entregable (`Reporte_Avance_Semana5.docx`, `..._Final.docx`, `..._DETAILED_EVIDENCE.docx`, `..._QUIZ_RIGUROSO.docx`, `..._Report.docx`). No es claro cuál es la versión canónica. | `find artifacts/week5/docs/` | Media |
| 6 | Existen **dos jerarquías de reportes en paralelo**: `reports/*.md` (en español/inglés mixto, por tema) e `Informes/*.tex/pdf/pptx` (en español, por hito). Ambas contienen información redundante (p. ej. resultados de PageRank aparecen en `reports/graph_analytics_report.md` y en `Informes/informe_hito5.tex`), sin una referencia cruzada explícita entre ellas. | Estructura de carpetas raíz | Media — afecta claridad de "repo structure", criterio de evaluación explícito |
| 7 | Carpeta `legacy/` contiene scripts y un `QUICK_STATUS.txt` de la Semana 5 con un **validador (`validate_week5.py`) cuyo output (`artifacts/validation_report.json`) está desactualizado** (fechado 2026-05-01, antes de completar incluso el Hito 2) y podría confundirse con el estado actual si se lee fuera de contexto. | `artifacts/validation_report.json` → `"status": "READY FOR WEEK 5"` | Baja-Media |
| 8 | **Ningún script usa `argparse`/`click`** ni un archivo de configuración central (rutas, semillas, hiperparámetros están hardcodeados dentro de cada script, ej. `R_path = "data/recommender/R_restock_bin.npz"` en `graph_construction.py`). Funciona porque todo se ejecuta desde la raíz del repo, pero es frágil y no escala a un segundo dataset o entorno. | Lectura de `src/graph_construction.py`, `src/build_R.py` | Baja-Media |
| 9 | **Equipo de 2 personas** frente a un tamaño recomendado de 3 a 5 en el brief. No es un incumplimiento (el brief permite roles combinados), pero sí es un factor de riesgo de carga de trabajo para el sprint final. | `git shortlog -sne` (2 autores distintos, con 3 identidades de commit) | Riesgo de planificación, no de rúbrica |
| 10 | El **catálogo de productos es pequeño (50 productos, 10 hogares)** y el grafo de co-ocurrencia resultante es un **grafo completo** (todos los pares co-ocurren, 1,225/1,225 aristas posibles). Esto es matemáticamente correcto pero **reduce el valor discriminativo de la topología** (solo los pesos aportan señal, no la estructura); la desviación estándar del PageRank es muy baja (σ≈0.00094 sobre valores ~0.02), lo que un evaluador puede leer como "el grafo no dice mucho". | `reports/graph_analytics_report.md`, sección 3.2 | Media — riesgo de defensa, no de incumplimiento |

---

## 2. Comparación Punto por Punto contra los Requisitos Oficiales

### 2.1 Core Project Shape (5 capas)

| Capa | Estado | Justificación |
| :--- | :---: | :--- |
| Catalog layer | ✅ | `product_catalog.csv` con 50 productos y metadatos USDA completos |
| Feature layer | ✅ | Numérico (nutrientes), categórico (CatBoost), texto (TF-IDF), temporal (hora/día) — los 4 tipos que pide el brief están presentes |
| Interaction/co-occurrence layer | ✅ | 10 variantes de matriz R con distintas ventanas de sesión y encodings |
| Graph layer | ✅ | Grafo producto-producto ponderado, no dirigido, con PageRank |
| Pipeline layer | 🟡 | Existe y es reproducible por pasos manuales documentados, pero **no hay un solo comando end-to-end** ni tests automáticos que verifiquen artefactos intermedios |

### 2.2 Dataset Rules

| Regla | Estado | Justificación |
| :--- | :---: | :--- |
| 1. Dataset no trivial en tamaño/estructura/preprocesamiento | 🟡 | 25,445 eventos y pipeline de preprocesamiento genuinamente complejo (star schema, CatBoost encoding, sesiones). El catálogo de 50 productos es pequeño; se sostiene por la complejidad transaccional, no por el volumen de catálogo — debe articularse así en la defensa |
| 2. Data dictionary | 🟡 | Existe pero cubre solo Hitos 1–3; faltan estructuras de recomendador y grafo (ver 1.5.4) |
| 3. Documentar URLs y procedencia | ✅ | `reports/source_inventory.md` documenta Instacart (Kaggle), USDA FoodData Central, y el motor de simulación propio |
| 4. Explicar por qué el dataset sostiene la segunda mitad del curso | ✅ | `reports/proposal.md` lo explica: co-ocurrencia para grafos, sesiones para recomendación — y de hecho ya se demostró al llegar hasta clustering+recomendación+grafo |
| 5. Evitar datasets triviales de benchmark | ✅ | No es Titanic/Iris/MNIST; es un dataset construido (Track B) |
| 6. Subset justificado si el dataset es grande | N/A | No aplica; el dataset no excede capacidad de procesamiento local |
| 7. Documentar lógica de matching si se combinan fuentes | 🟡 | La combinación Instacart + USDA + simulación está descrita cualitativamente en `source_inventory.md`, pero no hay un diagrama o tabla explícita de las claves de unión (`product_id` como clave de matching entre catálogo simulado y respuesta USDA) — se puede inferir del código pero no está documentado como tal |

### 2.3 Ethics and Access Note

| Requisito | Estado | Justificación |
| :--- | :---: | :--- |
| Origen de los datos | ✅ | `reports/ethics_note.md` documenta Instacart (público, liberado para investigación) y USDA (gobierno EE.UU., datos abiertos) |
| Por qué está permitido su uso | ✅ | Explica que no hay scraping ni vulneración de ToS |
| Riesgos de datos personales | ✅ | Declara ausencia de PII, identificadores son UUIDs sintéticos |
| Cómo se redujeron los riesgos | ✅ | Generación sintética + anonimización por diseño |

Esta sección está en realidad **muy bien resuelta** — es de las más completas del proyecto.

### 2.4 Required Repository Structure

| Elemento requerido | Estado | Justificación |
| :--- | :---: | :--- |
| `data/{raw,interim,processed}` | 🟡 | Existen `raw/` y `processed/`, pero no hay `interim/` explícito (aunque `data/features/` y `data/recommender/` cumplen funcionalmente ese rol de intermedio — la separación conceptual está presente aunque el nombre difiera) |
| `notebooks/` | 🟡 | Existe, pero 2 de 4 notebooks están vacíos |
| `src/` | ✅ | 19 scripts modulares |
| `reports/` | ✅ | 11 reportes + figuras |
| `artifacts/` | 🟡 | Existe pero mezcla entregables de presentación con archivos de validación obsoletos |
| `README.md` | ✅ | Extenso y actualizado (aunque con la inconsistencia numérica ya señalada) |
| `requirements.txt` | 🟡 | Existe pero con bug de codificación (UTF-16) |

### 2.5 Required Technical Artifacts (8 ítems)

| # | Artefacto | Estado | Evidencia |
| :-- | :--- | :---: | :--- |
| 1 | Script/pipeline de ingesta | ✅ | `extract_patterns.py`, `simulation.py`, `ingestion.py` |
| 2 | Directorio de dataset procesado | ✅ | `data/processed/inventory_v1.csv` |
| 3 | Diccionario de datos | 🟡 | Incompleto (ver 1.5.4) |
| 4 | Script/notebook de feature-building | ✅ | `src/features.py` |
| 5 | Script de evaluación | ✅ | `src/evaluation.py` |
| 6 | Script de construcción de grafo | ✅ | `src/graph_construction.py` |
| 7 | Runbook | 🟡 | Existe pero desactualizado (falta Hito 5) |
| 8 | Artefacto de demo final | 🟡 | `notebooks/03_presentation_demo.ipynb` existe pero no refleja clustering/recomendador/grafo |

### 2.6 Milestones (Semanas 3, 5, 7, 10, 12, 14)

| Milestone | Estado | Justificación resumida |
| :--- | :---: | :--- |
| **Semana 3** — Dataset Charter y Processed V1 | ✅ | Los 7 entregables requeridos existen: propuesta, inventario de fuentes, schema draft, dataset V1, data dictionary (parcial pero presente), scale analysis, ethics note. Ingesta ejecutable por comando documentado |
| **Semana 5** — Representación y Dimensionalidad | ✅ | Feature matrix, PCA con tabla de varianza explicada, ≥2 visualizaciones (hay 4), interpretación técnica en `dimensionality_reduction_report.md`. t-SNE opcional también incluido |
| **Semana 7** — Clustering y Validación | 🟡 | K-Means y DBSCAN (y de más, GMM/HDBSCAN) con parameter sweeps reales (excede el requisito). Falta el **cluster-profile analysis** con evidencia trazable y el **failure analysis** específico (ver 1.4.1–1.4.2) |
| **Semana 10** — Recomendación/Ranking | ✅ | Baseline (popularity), sistema fuerte (CF-ALS + híbrido), evaluación offline con métricas y candidate pool bien definidos, error analysis con casos fuertes/débiles, protocolo de evaluación explicado con detalle inusualmente alto |
| **Semana 12** — Grafo y Centralidad | ✅ | Definición completa (nodos/aristas/pesos/no dirigido), script de construcción, reporte con componentes conexas/grado/PageRank, sección de comparación (graph ranking vs. otros), nota de interpretación |
| **Semana 14** — Entrega Final Integrada | ❌ | Ninguno de los 7 entregables de cierre existe todavía (informe final consolidado, runbook final, presentación final, demo final actualizado, plan de monitoreo, limitaciones consolidadas). Es totalmente esperable a 10 días de julio dado el ritmo del curso — es el foco de este plan |

### 2.7 Final Report Structure (13 secciones exigidas)

| # | Sección requerida | ¿Existe contenido fuente? | Dónde vive hoy |
| :-- | :--- | :---: | :--- |
| 1 | Problem statement | ✅ | `reports/proposal.md` |
| 2 | Domain context | ✅ | `reports/proposal.md`, README |
| 3 | Dataset sources y access conditions | ✅ | `reports/source_inventory.md` |
| 4 | Schema y data dictionary | 🟡 | `reports/schema_draft.md` + `data_dictionary.md` incompleto |
| 5 | Preprocessing y feature engineering | ✅ | `reports/scale_analysis.md`, código en `src/features.py` |
| 6 | Dimensionality y representation analysis | ✅ | `reports/dimensionality_reduction_report.md` |
| 7 | Clustering analysis | 🟡 | `reports/clustering_experiments.md` + `final_model_selection.md`, falta profile/failure analysis |
| 8 | Recommendation/ranking system | ✅ | `reports/recommendation_experiments.md`, `data/recommender/README.md` |
| 9 | Graph analytics | ✅ | `reports/graph_analytics_report.md` |
| 10 | Evaluation protocol | ✅ | Documentado extensamente en `src/evaluation.py` (docstring) y tablas de resultados |
| 11 | Pipeline y reproducibility | 🟡 | `runbook.md` (desactualizado) |
| 12 | Ethics y limitations | 🟡 | Ética completa; limitaciones dispersas, no consolidadas |
| 13 | Final conclusions | ❌ | No existe una sección de conclusiones que integre las 5 capas en una narrativa única |

**Conclusión de la Sección 2:** el contenido fuente para 11 de las 13 secciones del informe final **ya existe** en algún reporte parcial. El trabajo pendiente es primordialmente de **síntesis, consolidación y llenado de huecos puntuales**, no de investigación desde cero.

### 2.8 Minimum Technical Standard for Passing

| Requisito mínimo | Estado |
| :--- | :---: |
| Dataset procesado real | ✅ |
| Representación de features rigurosa | ✅ |
| Experimento de clustering | ✅ |
| Experimento de ranking/recomendación | ✅ |
| Análisis de grafo | ✅ |
| Build path reproducible | 🟡 (reproducible pero con el bug de `requirements.txt` y runbook incompleto) |

**El proyecto ya aprueba el estándar mínimo.** El objetivo del sprint final es la excelencia (Sección 11), no la aprobación.

---

## 3. Análisis de Brechas (Gap Analysis)

| Requisito | Estado actual | Qué falta implementar | Prioridad | Dificultad | Dependencias | Tiempo estimado |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: |
| `requirements.txt` reproducible | Codificado en UTF-16LE, falla en clones frescos | Regenerar en UTF-8 (`pip freeze > requirements.txt` desde un venv limpio) y verificar `pip install` en un contenedor limpio | **Alta** | Muy baja | Ninguna | 15 min |
| Runbook sincronizado | Cubre hasta Hito 4 (Paso 17) | Añadir Pasos 18–19 (`graph_construction.py`, `graph_analytics.py`, `generate_hito5_figures.py`) y una sección de "Paso 20: Pipeline final integrado" | **Alta** | Baja | Fix de requirements.txt | 1-2 h |
| Notebooks vacíos | `01_exploratory.ipynb` y `02_scale_analysis.ipynb` en 0 bytes | Decidir: (a) poblarlos con el EDA real ya descrito en `reports/scale_analysis.md`, o (b) eliminarlos y quitarlos de las referencias en README | **Media-Alta** | Baja-Media | Ninguna | 2-4 h si se opta por poblarlos |
| Consistencia de métricas entre documentos | 3 cifras distintas para MAP@5/P@5 del híbrido entre README, runbook y graph_analytics_report | Re-ejecutar `evaluation.py` una sola vez, congelar el `evaluation_table.csv` resultante como fuente única de verdad, y actualizar todos los documentos citando esa tabla | **Alta** | Baja | Ninguna (no requiere cambios de código, solo re-ejecución + sincronización) | 2-3 h |
| Cluster-profile analysis | Nombres ilustrativos sin artefacto de respaldo | Script `src/cluster_profiling.py`: media de features por cluster, top-3 categorías dominantes, distribución temporal por cluster → `reports/cluster_profiles.md` + tabla/figura | **Alta** | Media | `cluster_labels_refined.npy`, `feature_matrix.npy` | 4-6 h |
| Failure analysis de clustering | Solo se menciona el % de ruido | Extender `cluster_profiling.py` (o script aparte) para listar qué productos/eventos cayeron en ruido DBSCAN y una hipótesis de causa (outliers de cantidad, productos de baja frecuencia, etc.) | Media | Baja-Media | Cluster-profile analysis | 2-3 h |
| Integración de PageRank al híbrido ("Semana 13") | Diseñado conceptualmente, no implementado | Modificar `recommender_hybrid.py` para añadir cuarto componente $w_G \cdot \text{PageRank}$, re-correr ablación de pesos, actualizar `evaluation.py` | Media-Alta | Media-Alta | Grafo y PageRank ya existen | 6-8 h |
| Demo final actualizado | Solo cubre PCA | Nuevo notebook `05_final_demo.ipynb` (o CLI) que muestre: dataset → clusters → recomendación híbrida para un household → grafo con productos top-PageRank | **Alta** | Media | Todos los artefactos ya existen, es de integración | 4-6 h |
| Diccionario de datos completo | Solo Hitos 1–3 | Añadir secciones para matrices R, factores ALS, vocabulario TF-IDF, esquema de nodos/aristas del grafo | Media-Alta | Baja | Ninguna | 3-4 h |
| Plan de monitoreo/operacionalización | No existe | Nuevo documento `reports/monitoring_plan.md`: qué métricas monitorear en producción (coverage, staleness del catálogo, drift de patrones de consumo), cadencia de reentrenamiento, alertas | **Alta** (exigido explícitamente en Semana 14) | Media | Ninguna | 3-4 h |
| Limitaciones y trabajo futuro consolidado | Disperso en varios reportes | Nuevo documento `reports/limitations_and_future_work.md` que sintetice: catálogo pequeño, datos sintéticos, grafo completo poco discriminativo, discretización nutricional ordinal, ausencia de datos reales de usuario | Media-Alta | Baja | Ninguna (síntesis) | 2-3 h |
| Reporte técnico final (13 secciones) | Existen 3 informes por hito, no uno integrado | Documento único (LaTeX o Word) que siga la estructura de 13 secciones del brief, reusando contenido existente + secciones nuevas (monitoreo, limitaciones, conclusiones) | **Alta** | Alta (por volumen, no por dificultad conceptual) | Todos los ítems anteriores | 2-3 días |
| Orquestador de pipeline único | 19 comandos manuales | `Makefile` o `run_pipeline.py` con targets por hito (`make hito1`, `make hito4`, `make all`) | Media | Baja-Media | Ninguna | 3-4 h |
| Limpieza de artefactos duplicados | 5 versiones de docs de Semana 5 en `artifacts/week5/docs/` | Archivar 4 de 5 en una subcarpeta `_archive/` o eliminarlas, dejando solo la versión final referenciada desde README | Baja | Muy baja | Ninguna | 30 min |
| Presentación final (Semana 14) | Solo existe la de Hito 5 | Nueva presentación de cierre que narre las 5 capas de punta a punta + resultados + límites + próximos pasos | **Alta** | Media | Reporte final consolidado | 1 día |
| Pruebas de humo / reproducibilidad verificada | Ninguna | Al menos un script `tests/smoke_test.py` que verifique shapes/tipos de los artefactos clave tras correr el pipeline | Baja-Media | Media | Orquestador de pipeline | 3-4 h |

---

## 4. Plan Maestro de Desarrollo

El plan está organizado en 8 fases, secuenciadas para un equipo de 2 personas trabajando en paralelo cuando es posible. Cada fase indica objetivos, tareas, archivos, scripts/notebooks y criterios de cierre.

### Fase 1 — Correcciones Críticas de Reproducibilidad (0.5–1 día)

**Objetivo:** eliminar los bugs que rompen la reproducibilidad y la coherencia documental antes de construir nada nuevo encima.

**Tareas:**
1. Regenerar `requirements.txt` en UTF-8 puro (sin BOM), idealmente desde `pip freeze` en un venv limpio recién creado con los 19 scripts corridos.
2. Clonar el repo en una carpeta nueva y correr `pip install -r requirements.txt` de cero para confirmar que ya no falla.
3. Actualizar `runbook.md` añadiendo los pasos de Hito 5 (grafo) que hoy solo están en README.
4. Decidir el destino de `notebooks/01_exploratory.ipynb` y `02_scale_analysis.ipynb` (poblar o eliminar) y ejecutar esa decisión.
5. Re-ejecutar `python src/evaluation.py` una sola vez y usar el `evaluation_table.csv` resultante como fuente única; actualizar README y `graph_analytics_report.md` para que citen exactamente esos números.
6. Archivar los 4 documentos duplicados de `artifacts/week5/docs/` en una subcarpeta `_archive/`.

**Archivos involucrados:** `requirements.txt`, `runbook.md`, `notebooks/01_exploratory.ipynb`, `notebooks/02_scale_analysis.ipynb`, `README.md`, `reports/graph_analytics_report.md`, `artifacts/week5/docs/`.

**Resultado esperado:** un clon fresco del repo se instala y corre sin fricciones; toda cifra de evaluación citada en cualquier documento es idéntica.

**Criterio de finalización:** `pip install -r requirements.txt` funciona en un entorno limpio; `runbook.md` menciona los 19 scripts existentes en `src/`; cero notebooks vacíos sin explicación.

---

### Fase 2 — Cierre de Deuda Técnica de Hitos Previos (1–1.5 días)

**Objetivo:** completar los dos huecos puntuales de la Semana 7 (cluster-profile y failure analysis) para que el hito quede con evidencia trazable, no solo narrativa.

**Tareas:**
1. Escribir `src/cluster_profiling.py`: por cada cluster de `cluster_labels_refined.npy`, calcular medias/modas de las columnas originales de `feature_matrix.npy` (usando `feature_names.json` para interpretar), identificar las 3 categorías de producto más frecuentes y el rango horario dominante.
2. Generar `reports/cluster_profiles.md` con una tabla de 38 filas (una por cluster) y una figura de barras con el tamaño de cada cluster.
3. Analizar los 71 puntos etiquetados como ruido (`label == -1`): ¿qué productos/eventos son? ¿hay un patrón (outliers de cantidad, productos raros, timestamps atípicos)? Documentar en la misma sección de `cluster_profiles.md` bajo "Failure Analysis".
4. Actualizar `reports/clustering_experiments.md` para enlazar al nuevo reporte de perfiles en vez de solo nombrar clusters de forma ilustrativa.

**Archivos involucrados:** `data/features/cluster_labels_refined.npy`, `data/features/feature_matrix.npy`, `data/features/feature_names.json`, `data/processed/inventory_v1.csv`.

**Scripts a desarrollar:** `src/cluster_profiling.py`.

**Notebooks necesarios:** ninguno obligatorio, pero es un buen candidato para una celda exploratoria en el demo final (Fase 4).

**Resultado esperado:** `reports/cluster_profiles.md` con evidencia real y trazable de qué caracteriza a cada cluster, reemplazando las etiquetas ilustrativas actuales.

**Criterio de finalización:** cada nombre de cluster usado en README/informe final tiene una fila correspondiente en `cluster_profiles.md` con los números que lo sustentan.

---

### Fase 3 — Extensión Planeada: PageRank en el Recomendador Híbrido ("Semana 13") (1–1.5 días)

**Objetivo:** ejecutar la extensión que el propio equipo se comprometió a hacer, convirtiendo el grafo en una señal de producción y no solo en un análisis exploratorio aislado.

**Tareas:**
1. Modificar `src/recommender_hybrid.py` para incorporar un cuarto término $w_G \cdot \text{PageRank}(i)$ normalizado Min-Max, junto a contenido, CF y vencimiento.
2. Re-ejecutar el barrido de ablación de pesos (ahora en 4 dimensiones: $w_C, w_F, w_E, w_G$) y seleccionar la combinación ganadora por `precision@5`/`MAP@5` en el mismo protocolo de hold-out.
3. Actualizar `src/evaluation.py` para incluir el nuevo sistema `hybrid_v2_graph` en la tabla comparativa junto a los 5 sistemas ya existentes.
4. Documentar en `reports/graph_analytics_report.md` (sección 5, "Conclusiones y Trabajo Futuro") el resultado real de la integración, reemplazando la afirmación actual de "trabajo futuro" por resultados concretos.

**Archivos involucrados:** `data/recommender/graph_metrics.json`, `als_Y.npy`, `tfidf_items.npz`, `evaluation_table.csv`.

**Scripts a desarrollar/modificar:** `src/recommender_hybrid.py`, `src/evaluation.py`.

**Resultado esperado:** una fila nueva en `evaluation_table.csv` (`hybrid_v2_graph`) con métricas comparables; una decisión documentada de si el nuevo sistema reemplaza o no al híbrido de producción actual.

**Criterio de finalización:** existe una comparación cuantitativa hybrid vs. hybrid+graph, con una recomendación explícita de cuál usar en producción y por qué.

---

### Fase 4 — Demo Final Integrado (1 día)

**Objetivo:** cumplir de forma robusta el "final demo artifact" de Semana 14, que debe mostrar el sistema completo, no solo un fragmento (Hito 1–2 como hoy).

**Tareas:**
1. Crear `notebooks/05_final_demo.ipynb` (o, mejor aún dado que el brief valora "small dashboard" por encima de notebook-only, un script Streamlit ligero `src/demo_app.py`) que integre: selección de un household → perfil de consumo (cluster al que pertenece) → top-5 recomendaciones híbridas con explicación de cada componente → visualización del grafo resaltando los productos recomendados y su PageRank.
2. Si se opta por notebook, asegurarse de que corre de punta a punta sin estado oculto (`Kernel → Restart & Run All` sin errores).
3. Grabar una captura o GIF corto del demo funcionando, para incluir como evidencia en el informe final y la presentación.

**Archivos involucrados:** todos los artefactos de `data/recommender/`, `data/features/cluster_labels_refined.npy`, `kitchen_graph.gexf`.

**Notebooks/scripts:** `notebooks/05_final_demo.ipynb` y/o `src/demo_app.py`.

**Resultado esperado:** un artefacto único, ejecutable, que un evaluador externo pueda abrir y entender el producto completo en menos de 5 minutos.

**Criterio de finalización:** el demo corre sin errores desde cero y toca las 5 capas del proyecto (catálogo, features, interacción, grafo, recomendación).

---

### Fase 5 — Plan de Monitoreo y Operacionalización (0.5 día)

**Objetivo:** producir el entregable exigido de forma explícita para Semana 14 que hoy no existe en absoluto.

**Tareas:**
1. Redactar `reports/monitoring_plan.md` cubriendo: (a) métricas de monitoreo en producción (coverage del catálogo, tasa de clics/aceptación simulada, staleness de los datos USDA, drift de las distribuciones de consumo respecto a los patrones base de Instacart); (b) cadencia de reentrenamiento sugerida (p. ej. recalcular ALS y PageRank semanalmente si se conectara a datos reales); (c) alertas (ej. si `coverage@5` cae por debajo de un umbral, o si el grafo pierde conectividad); (d) un boceto de arquitectura de despliegue (batch vs. tiempo real) aunque sea conceptual, dado que el sistema es un prototipo académico.

**Archivos involucrados:** ninguno de datos; es un documento de diseño.

**Resultado esperado:** `reports/monitoring_plan.md`.

**Criterio de finalización:** el documento responde explícitamente qué se mide, cuándo se reentrena y qué dispara una alerta — los 3 componentes mínimos de un plan de operacionalización creíble.

---

### Fase 6 — Reporte Técnico Final Integrado (2–3 días)

**Objetivo:** consolidar las 13 secciones exigidas por el brief en un solo documento final, reusando el contenido ya escrito en los reportes por hito y rellenando los huecos identificados en la Sección 2.7.

**Tareas:**
1. Crear el esqueleto del documento final (`reports/final_report.md` o LaTeX si van a mantener el mismo formato que `informe_hito5.tex`) con las 13 secciones del brief como encabezados.
2. Para las 9 secciones que ya tienen contenido fuente (problem statement, domain context, dataset sources, preprocessing, dimensionality, recommendation, graph analytics, evaluation protocol, ethics), migrar y sintetizar el contenido de los reportes existentes, actualizando cifras según la Fase 1.
3. Escribir de cero las secciones ausentes: diccionario de datos completo (usa el trabajo de la Fase 1/2 anterior), pipeline y reproducibilidad (referencia al runbook actualizado), limitaciones consolidadas (Fase 5 conceptualmente similar pero enfocada en límites, no en operación), y conclusiones finales que narren la coherencia de las 5 capas.
4. Revisión cruzada: verificar que ninguna cifra en el reporte final contradiga `evaluation_table.csv`, `graph_metrics.json` o `cluster_profiles.md`.

**Archivos involucrados:** todos los `reports/*.md` existentes, `data/recommender/evaluation_table.csv`, `reports/cluster_profiles.md` (Fase 2), `reports/monitoring_plan.md` (Fase 5).

**Resultado esperado:** `reports/final_report.md` (o `.tex`/`.pdf`), documento único y autocontenido de 15-25 páginas equivalentes.

**Criterio de finalización:** las 13 secciones del brief están presentes y ninguna cifra citada difiere de los artefactos fuente.

---

### Fase 7 — Runbook Final y Verificación de Reproducibilidad (0.5–1 día)

**Objetivo:** garantizar que "el proyecto corre desde pasos documentados" tal como exige explícitamente la expectativa técnica de Semana 14.

**Tareas:**
1. Actualizar `runbook.md` con los pasos de las Fases 2–3 (cluster profiling, hybrid+graph) además de los ya pendientes de Hito 5 (Fase 1).
2. (Opcional pero recomendado, ver Gap Analysis) Crear `Makefile`/`run_pipeline.py` con un target `all` que ejecute los 19+ scripts en orden.
3. Ejecutar el pipeline completo de punta a punta en una máquina/entorno limpio y cronometrar el tiempo total, documentándolo en el runbook (dato que refuerza el criterio de "rerunnable workflow").

**Archivos involucrados:** `runbook.md`, potencialmente `Makefile`.

**Resultado esperado:** runbook 100% sincronizado con `src/`; evidencia de una corrida limpia completa.

**Criterio de finalización:** cualquier script en `src/` está referenciado en el runbook, y viceversa (ningún script "huérfano" sin documentar).

---

### Fase 8 — Presentación Final y Ensayo de Defensa (1–1.5 días)

**Objetivo:** preparar la exposición oral y anticipar las preguntas del profesor (ver Sección 10).

**Tareas:**
1. Construir la presentación final (10–15 slides) siguiendo la misma estructura narrativa que `Informes/guia_defensa_hito5.md` usó para Hito 5, pero para el proyecto completo: problema → pipeline de 5 capas → resultados clave por capa → demo → limitaciones → próximos pasos.
2. Redactar una guía de defensa final (`Informes/guia_defensa_final.md`) con las preguntas más probables y respuestas ensayadas (ver Sección 10 de este documento como punto de partida).
3. Ensayar la defensa en vivo mostrando el demo de la Fase 4, cronometrando la exposición.
4. Revisión final cruzada: repo, informe, presentación y demo deben contar exactamente la misma historia numérica (mismas cifras de silhouette, precision@5, PageRank, etc.).

**Archivos involucrados:** `Informes/`, presentación final (`.pptx`).

**Resultado esperado:** equipo preparado para defender con coherencia total entre código, informe y discurso oral.

**Criterio de finalización:** ambos integrantes pueden responder, sin el reporte abierto, las 10 preguntas de la Sección 10 de este documento.

---

## 5. Arquitectura del Proyecto

### 5.1 Estructura actual (auditada)

```text
Smart-Kitchen-Intelligence/
├── Informes/              # Informes LaTeX por hito (.tex/.pdf) + 2 presentaciones (.pptx)
├── README.md              # Documentación principal (extensa, con inconsistencias numéricas)
├── artifacts/
│   ├── validation_report.json   # Obsoleto (fechado en plena Semana 5)
│   └── week5/{docs,presentation}/  # 5 versiones duplicadas de un mismo entregable
├── data/
│   ├── raw/                # catalog_raw.csv, movements_raw.csv, instacart_patterns.json
│   ├── processed/          # inventory_v1.csv (Single Source of Truth)
│   ├── features/           # matrices .npy + cluster labels
│   └── recommender/        # 30+ artefactos del motor de recomendación (bien documentado con su propio README.md)
├── legacy/                 # Scripts y status de Semana 5, ya no ejecutados
├── notebooks/              # 4 notebooks, 2 de ellos vacíos
├── reports/
│   ├── figures/             # 25 figuras, subcarpetas por hito (hito4/, hito5/, slides/)
│   └── *.md                 # 11 reportes técnicos temáticos
├── scripts/                 # 2 scripts .ps1 (utilidades de git, específicas de Windows)
├── src/                     # 19 scripts Python del pipeline
├── requirements.txt         # Bug: UTF-16
└── runbook.md                # Desactualizado (falta Hito 5)
```

### 5.2 Qué funciona bien y debe conservarse

- **`data/recommender/README.md`** es el mejor documento del repositorio: cada archivo generado está documentado con su forma, encoding y script generador. **Debería ser el modelo a replicar** para documentar `data/features/` y `data/raw/`, que hoy no tienen un README propio.
- La separación `raw/ → processed/ → features/ → recommender/` es, en esencia, exactamente la separación "raw/interim/processed" que pide el brief, solo que con nombres más descriptivos del dominio. **No es necesario renombrar carpetas** para cumplir el requisito — la separación conceptual explícita es lo que se evalúa, y ya está clara.
- La modularidad de `src/` (un script por responsabilidad, sin mezclar ingestión con modelado) es una señal de buena ingeniería de software y facilita que un evaluador revise el pipeline paso a paso.

### 5.3 Qué sobra o genera confusión

1. **`Informes/` vs `reports/`**: dos jerarquías paralelas de documentación técnica generan la pregunta "¿cuál es la autoritativa?" para un evaluador externo. Recomendación: mantener `reports/` como la fuente de reportes temáticos de trabajo (como hasta ahora) e `Informes/` estrictamente como los documentos de defensa formal por hito (LaTeX/PDF/PPTX), y **añadir un `Informes/README.md`** de una línea que aclare esa distinción explícitamente.
2. **`legacy/`**: correcto mantenerlo por trazabilidad (según su propio README interno), pero su `QUICK_STATUS.txt` y el `artifacts/validation_report.json` asociado deberían llevar una advertencia visible ("⚠️ Snapshot histórico de Semana 5, no refleja el estado actual") para que nadie los confunda con el estado vigente.
3. **`artifacts/week5/docs/`**: 5 archivos para un mismo entregable es ruido. Archivar 4 en `_archive/` (Fase 1).
4. **`scripts/*.ps1`**: son utilidades de Git específicas de Windows (`clean_repo.ps1`, `push_hito4.ps1`), no parte del pipeline de datos. Están bien ubicadas fuera de `src/`, pero conviene un comentario en el README aclarando que `scripts/` es para tooling de repo, no para el pipeline (para no confundirlas con los pasos del runbook).

### 5.4 Qué falta crear

| Carpeta/archivo nuevo | Propósito | Interacción con el resto |
| :--- | :--- | :--- |
| `data/features/README.md` | Documentar cada `.npy`/`.json` de features igual que ya se hace en `data/recommender/README.md` | Consumido por `reduction.py`, `clustering.py`, y ahora `cluster_profiling.py` (Fase 2) |
| `tests/` | Pruebas de humo por etapa del pipeline (shapes, rangos, nulos) | Se ejecuta después de cada etapa del `Makefile` propuesto |
| `Makefile` o `run_pipeline.py` | Orquestación de punta a punta con targets por hito | Reemplaza la ejecución manual de 19 comandos |
| `reports/cluster_profiles.md` | Salida de la Fase 2 | Referenciado desde `clustering_experiments.md` y el informe final |
| `reports/monitoring_plan.md` | Salida de la Fase 5 | Sección 11-12 del informe final |
| `reports/limitations_and_future_work.md` | Síntesis de limitaciones dispersas | Sección 12 del informe final |
| `reports/final_report.md` (o `.tex`) | Documento de cierre de Semana 14 | Consolida todo lo anterior |
| `notebooks/05_final_demo.ipynb` o `src/demo_app.py` | Demo final integrado | Consume todos los artefactos de `data/` |

### 5.5 Qué debería reorganizarse

- Mover los 2 notebooks vacíos fuera de `notebooks/` (a `_archive/` o eliminarlos) para que la carpeta solo contenga notebooks funcionales.
- Añadir, dentro de `reports/`, subcarpetas por hito (`reports/hito1/`, `reports/hito2/`... o similar) **solo si el número de archivos sueltos en la raíz de `reports/` sigue creciendo** — hoy con 11 archivos es manejable, pero al sumar los de la Fase 6 (cluster_profiles, monitoring_plan, limitations, final_report) llegará a 15, momento en el que una subcarpetización por tema (data/, modeling/, graph/, final/) mejoraría la navegabilidad.

---

## 6. Pipeline Completo (Raw → Producto Final)

```
Raw Data
  │  (Kaggle: Instacart patterns; USDA FoodData Central API; simulación estocástica propia)
  │  scripts: extract_patterns.py → simulation.py → ingestion.py
  ▼
Cleaning / ETL
  │  Join catálogo ↔ movimientos por product_id/stock_id; tipado; imputación por media de categoría
  │  script: preprocessing.py  →  data/processed/inventory_v1.csv (25,445 filas, SSOT)
  ▼
Feature Engineering
  │  CatBoost Encoding (categóricas de alta cardinalidad), TF-IDF (texto), variables temporales,
  │  StandardScaler sobre nutrientes
  │  script: features.py  →  feature_matrix.npy (72,000 × 61)
  ▼
Dimensionality Reduction
  │  PCA (30 componentes, 90.01% varianza) + t-SNE (visualización no lineal)
  │  script: reduction.py  →  feature_matrix_reduced.npy (72,000 × 30)
  ▼
Clustering
  │  Benchmark K-Means/GMM/DBSCAN/HDBSCAN con parameter sweeps → DBSCAN refinado gana
  │  scripts: clustering.py → clustering_refinement.py  →  cluster_labels_refined.npy (38 clusters, Silhouette 0.6549)
  │  [FASE 2 PENDIENTE: cluster_profiling.py → cluster_profiles.md]
  ▼
Interaction Matrix Construction
  │  Sesiones de restock (60 min) y kitchen (15 min) por household
  │  script: build_R.py  →  10 matrices R_*.npz
  ▼
Recommendation Engine (3 capas)
  │  Contenido (TF-IDF) + CF (ALS implícito, barrido λ) + señal de vencimiento
  │  scripts: recommender_content.py, normalizations.py, recommender_cf.py, cold_start.py, recommender_hybrid.py
  │  [FASE 3 PENDIENTE: incorporar 4to componente de PageRank]
  ▼
Graph Analytics
  │  Grafo de co-ocurrencia producto-producto (R^T·R), grado ponderado, PageRank
  │  scripts: graph_construction.py → graph_analytics.py  →  kitchen_graph.gexf, graph_metrics.json
  ▼
Evaluation
  │  Protocolo único (Masked Basket Completion, hold-out 20%, seed 42) sobre 5 sistemas:
  │  popularity, pagerank, content_tfidf, cf_als, hybrid
  │  script: evaluation.py  →  evaluation_table.csv, error_analysis.csv
  ▼
Dashboard / Demo
  │  [FASE 4 PENDIENTE: notebook/app que integre selección de household → cluster → recomendación → grafo]
  ▼
Final Report
  │  [FASE 6 PENDIENTE: síntesis de 13 secciones, informe único de cierre]
```

Cada flecha del diagrama corresponde a artefactos físicos ya persistidos en disco (no solo estado en memoria de notebook), lo cual es exactamente lo que el brief exige bajo "evidence that the project does not rely on hidden notebook state". Este es uno de los puntos más fuertes del proyecto tal como está hoy.

---

## 7. Checklist Extremadamente Detallado de Entregables Finales

### Código y scripts
- [x] Script de ingesta (`extract_patterns.py`, `simulation.py`, `ingestion.py`)
- [x] Script de preprocesamiento/ETL (`preprocessing.py`)
- [x] Script de feature engineering (`features.py`)
- [x] Script de reducción de dimensionalidad (`reduction.py`)
- [x] Scripts de clustering (`clustering.py`, `clustering_refinement.py`)
- [ ] Script de cluster-profiling (Fase 2, nuevo)
- [x] Scripts del recomendador (`build_R.py`, `recommender_content.py`, `normalizations.py`, `recommender_cf.py`, `cold_start.py`, `recommender_hybrid.py`)
- [ ] Script del recomendador híbrido extendido con grafo (Fase 3)
- [x] Script de evaluación (`evaluation.py`)
- [x] Scripts de construcción y análisis de grafo (`graph_construction.py`, `graph_analytics.py`)
- [ ] Orquestador único de pipeline (`Makefile` / `run_pipeline.py`)
- [ ] Al menos un smoke test (`tests/`)

### Notebooks
- [ ] `01_exploratory.ipynb` — poblar o eliminar
- [ ] `02_scale_analysis.ipynb` — poblar o eliminar
- [x] `03_presentation_demo.ipynb` (parcial — cubre solo Hitos 1-2)
- [x] `04_recommender_experiments.ipynb`
- [ ] `05_final_demo.ipynb` integrando las 5 capas (Fase 4)

### Datasets y artefactos de datos
- [x] `data/raw/*` (catálogo crudo, movimientos, patrones Instacart)
- [x] `data/processed/inventory_v1.csv`
- [x] `data/features/*.npy` + `feature_names.json`
- [x] `data/features/cluster_labels_refined.npy`
- [x] `data/recommender/*` (30+ artefactos, con su propio README)
- [x] `data/recommender/kitchen_graph.gexf`, `graph_metrics.json`
- [ ] `data/features/README.md` (nuevo, documentando features igual que recommender/README.md)

### Modelos y artefactos de modelado
- [x] Modelo de clustering ganador documentado (`final_model_selection.md`)
- [x] Factores ALS (`als_X.npy`, `als_Y.npy`, `als_meta.json`)
- [x] Similaridades ítem-ítem (contenido y CF)
- [ ] Pesos finales del híbrido extendido con grafo (Fase 3)

### Reportes
- [x] `proposal.md`, `source_inventory.md`, `schema_draft.md`, `scale_analysis.md`, `ethics_note.md`, `data_dictionary.md` (parcial)
- [x] `dimensionality_reduction_report.md`
- [x] `clustering_experiments.md`, `final_model_selection.md`
- [ ] `cluster_profiles.md` (Fase 2)
- [x] `recommendation_experiments.md`
- [x] `graph_analytics_report.md`
- [ ] `monitoring_plan.md` (Fase 5)
- [ ] `limitations_and_future_work.md` (Fase 6)
- [ ] `final_report.md` / `.tex` — informe integrado de 13 secciones (Fase 6)

### Gráficos y tablas
- [x] 25 figuras en `reports/figures/` (PCA, t-SNE, clustering, recomendador, grafo)
- [ ] Figura de tamaño/distribución de clusters con nombres respaldados (Fase 2)
- [ ] Figura comparativa hybrid vs. hybrid+graph (Fase 3)

### Documentación
- [x] `README.md` (requiere corrección de cifras, Fase 1)
- [ ] `runbook.md` sincronizado con Hito 5 y fases nuevas (Fases 1 y 7)
- [x] `data/recommender/README.md` (diccionario de artefactos, modelo a replicar)
- [ ] Diccionario de datos completo (Fase 6)

### Presentación y defensa
- [x] Presentación de Hito 5 (`Informes/hito5_smart_kitchen.pptx`, `milestone5_smart_kitchen_en.pptx`)
- [ ] Presentación final de Semana 14 (Fase 8)
- [x] `Informes/guia_defensa_hito5.md` (modelo a replicar)
- [ ] Guía de defensa final (Fase 8)

### Evidencias
- [x] `evaluation_table.csv`, `evaluation_summary.json`, `error_analysis.csv`
- [x] `graph_metrics.json`
- [ ] Evidencia de corrida limpia end-to-end cronometrada (Fase 7)
- [ ] Captura/GIF del demo final funcionando (Fase 4)

---

## 8. Riesgos Técnicos y Estrategias de Mitigación

| Riesgo | Descripción | Mitigación propuesta |
| :--- | :--- | :--- |
| **Cifras inconsistentes entre documentos** | README, runbook y `graph_analytics_report.md` reportan valores distintos de MAP@5/P@5 para el híbrido | Congelar una única corrida de `evaluation.py` como fuente de verdad (Fase 1) y referenciarla desde todos los documentos, nunca copiar cifras a mano dos veces |
| **Afirmaciones sin evidencia trazable** | Los nombres de clusters ("Perecederos matutinos") no tienen artefacto de respaldo | Fase 2 (cluster-profiling) — nunca presentar un nombre de cluster en la defensa sin poder mostrar la fila de datos que lo sustenta |
| **`requirements.txt` roto en un clon fresco** | Codificación UTF-16 puede hacer fallar la instalación en el entorno del evaluador | Regenerar en UTF-8 y probar en un contenedor/VM limpia antes de la entrega (Fase 1) |
| **Grafo completo con baja discriminación estructural** | 1,225/1,225 aristas posibles existen; PageRank casi uniforme (σ≈0.00094) | En la defensa, ser explícitos: la señal está en los **pesos**, no en la topología binaria; considerar como mejora (Sección 11) aplicar un umbral de poda (edge thresholding) para dejar solo las co-ocurrencias estadísticamente significativas y así generar una topología más informativa (posiblemente con comunidades no triviales) |
| **Precision@5 absoluto bajo (~0.04-0.06) en todos los sistemas** | Un evaluador puede preguntar "¿esto es bueno?" al ver cifras bajas en términos absolutos | Preparar la respuesta comparativa: el catálogo tiene 50 ítems, un ranking aleatorio de top-5 tendría precision@5 esperado ≈5/50=0.10 en el caso trivial de un solo acierto relevante, pero el candidate pool y el carácter de "descubrimiento" (cross-selling, no recompra de lo ya visto) hacen que estas cifras sean razonables; enfatizar MAP@5 relativo entre sistemas y coverage, no el valor absoluto aislado |
| **Equipo de 2 personas ante una carga de cierre grande** | Fases 1-8 representan aproximadamente 10-12 días-persona de trabajo | Paralelizar: mientras una persona hace Fase 2-3 (código/experimentos), la otra puede avanzar Fase 5-6 (documentación) simultáneamente, ya que tienen pocas dependencias cruzadas hasta la Fase 6 |
| **Dataset íntegramente sintético en la capa de interacción** | Todas las transacciones de usuario son simuladas, no reales | Nunca presentarlo como datos reales de usuarios; enfatizar que la **metodología** (star schema, feature engineering, clustering, recomendación híbrida, grafo) es transferible a datos reales, y que la ética/nota de acceso ya lo declara explícitamente — convertir la limitación en un punto de honestidad técnica, valorado en el criterio "honesty about limitations" de la rúbrica |
| **Cuellos de botella de tiempo en la Fase 6 (informe final)** | Consolidar 13 secciones desde 11 reportes dispersos es la tarea de mayor volumen | Empezar la Fase 6 en paralelo con la Fase 3 (no esperar a que todo el código nuevo esté listo); las secciones 1-3, 5-6, 8-10 no dependen de ningún desarrollo pendiente y pueden migrarse desde ya |
| **Dependencia oculta entre notebooks y estado de sesión** | Riesgo genérico marcado por el brief ("hidden notebook state") | Verificar que `04_recommender_experiments.ipynb` y el nuevo `05_final_demo.ipynb` corren con `Restart Kernel & Run All` sin editar celdas manualmente entre corridas |
| **Riesgo de reproducibilidad por rutas hardcodeadas** | Todos los scripts asumen ejecución desde la raíz del repo con rutas relativas fijas | Documentar explícitamente en el runbook "ejecutar siempre desde la raíz del repositorio"; no es necesario refactorizar a argparse para esta entrega, pero sí dejarlo como ítem de trabajo futuro (Sección 11) |

---

## 9. Plan Diario (Cronograma Propuesto)

**Supuesto explícito (ver nota al inicio del documento):** ventana de 10-14 días desde hoy (2026-07-04). Ajustar fechas reales en cuanto se confirme la fecha de defensa de Semana 14. División sugerida: **Gabriel = "modeling/evaluation lead"** (código y experimentos), **José = "reporting/data engineering lead"** (documentación y limpieza), con cruce en la Fase 6 y 8. Ajustar según cómo se hayan distribuido los roles reales en el equipo.

| Día | Tareas | Puede hacerse en paralelo | Depende de | Tiempo estimado | Prioridad |
| :-: | :--- | :--- | :--- | :---: | :---: |
| 1 | Fase 1 completa: fix `requirements.txt`, sync runbook (parcial), decisión sobre notebooks vacíos, re-correr `evaluation.py` una vez, congelar cifras | Sí — ambos integrantes pueden dividirse estas tareas atómicas | Nada | 4-6 h | Alta |
| 2 | Fase 2: `cluster_profiling.py` + `cluster_profiles.md` | Persona A en Fase 2; Persona B puede empezar ya la migración de secciones 1-3 del informe final (Fase 6, adelantado) | Día 1 (labels y features ya existen, no depende de fixes) | 6-8 h | Alta |
| 3 | Fase 3: extensión híbrido+grafo, re-ablación de pesos, actualizar `evaluation.py` | Persona A en Fase 3; Persona B sigue con secciones 5-6, 8-10 del informe final | Grafo y PageRank ya existen (no bloqueante) | 6-8 h | Media-Alta |
| 4 | Cerrar Fase 3 (documentar resultado en `graph_analytics_report.md`) + iniciar Fase 4 (demo final) | Persona A termina Fase 3 y arranca Fase 4; Persona B redacta Fase 5 (`monitoring_plan.md`) | Fase 3 código terminado | 6-8 h | Media-Alta |
| 5 | Fase 4 completa: demo final integrado + captura/GIF | Persona A termina demo; Persona B redacta Fase 6 sección "limitations" | Todos los artefactos previos | 4-6 h | Alta |
| 6 | Fase 6: consolidar informe final (secciones 4, 7, 11-13 restantes: diccionario completo, cluster/failure analysis, pipeline/reproducibilidad, conclusiones) | Ambos revisan juntos coherencia numérica | Fases 1-5 completas | 6-8 h | Alta |
| 7 | Fase 6 (cont.) + Fase 7: runbook final sincronizado, corrida limpia end-to-end cronometrada | División de tareas: uno arma el documento, otro corre el pipeline limpio | Fase 6 en curso | 6-8 h | Alta |
| 8 | Revisión cruzada completa: informe vs. código vs. runbook vs. README — cero inconsistencias numéricas | Sesión conjunta obligatoria (no paralelizable) | Fases 1-7 | 4-6 h | Alta |
| 9 | Fase 8: construir presentación final + guía de defensa | División: uno arma slides, otro redacta guía de preguntas/respuestas | Informe final cerrado | 6-8 h | Alta |
| 10 | Ensayo de defensa completo (con demo en vivo), ajustes finales de timing y respuestas | Conjunto | Día 9 | 3-4 h | Alta |
| 11-12 (colchón) | Buffer para imprevistos (bugs al correr pipeline limpio, feedback de un tercero que revise el informe, ajustes de última hora) | — | — | — | — |

**Nota:** si la fecha real de Semana 14 es más cercana que 10 días, las Fases 2 (cluster-profiling) y 3 (extensión de grafo) son las más sacrificables sin incumplir el mínimo técnico de aprobación (Sección 2.8), ya que el proyecto ya aprueba sin ellas — pero sí perjudican el salto de "aprobado" a "sobresaliente" (Sección 11).

---

## 10. Preparación para la Sustentación

### Arquitectura
**P: ¿Por qué eligieron un Star Schema en vez de un modelo normalizado o documental?**
R: Porque el análisis es predominantemente agregacional (features por evento, luego por sesión, luego por household), no transaccional-OLTP. Un star schema con `fact_inventory_events` y `dim_products` permite hacer joins únicos y baratos antes de construir la matriz de features, evitando fragmentación en múltiples tablas normalizadas que habría que re-unir en cada etapa (`reports/schema_draft.md`, sección 4).

**P: ¿Por qué CatBoost Encoding y no One-Hot Encoding para las categóricas?**
R: OHE generaba una matriz dispersa que crecía con la cardinalidad del catálogo y diluía la señal en el PCA posterior (curse of dimensionality, documentado en `reports/scale_analysis.md`). CatBoost Encoding (target encoding) comprime cada categoría a un valor denso basado en probabilidad de consumo, manteniendo compacto el espacio de 61 features sin perder información discriminativa.

### Datasets
**P: ¿Por qué los datos de interacción son simulados y no reales?**
R: El brief permite explícitamente Track B (Build-Your-Own Dataset) y exige evitar el uso no autorizado de datos personales. El equipo optó por generar interacciones sintéticas parametrizadas con distribuciones reales extraídas de Instacart (hora de compra, frecuencia de producto), lo que preserva realismo estadístico sin exponer datos de usuarios reales ni violar ningún ToS (`reports/ethics_note.md`). Es una decisión de diseño ético explícita, no una limitación oculta.

**P: ¿Por qué USDA y no OpenFoodFacts para nutrición, si el código menciona ambos?**
R: El catálogo de Instacart es de productos estadounidenses; USDA FoodData Central tiene mejor cobertura y exactitud para ese universo de productos que OpenFoodFacts, que está más orientado a productos europeos (`reports/source_inventory.md`).

### Feature engineering
**P: ¿Por qué 30 componentes principales y no menos/más?**
R: Es el punto donde la varianza acumulada cruza el umbral de 90%, definido de antemano como criterio de retención de energía informativa (`reports/dimensionality_reduction_report.md`). Es una decisión basada en un criterio cuantitativo predefinido, no ajustada post-hoc para mejorar resultados posteriores.

### Clustering
**P: ¿Por qué DBSCAN y no K-Means, si K-Means es más simple e interpretable?**
R: El benchmark mostró que los datos no forman clusters esféricos de tamaño similar (supuesto que K-Means necesita) — K-Means alcanzó Silhouette máximo de 0.54 incluso extendiendo la búsqueda hasta k=25, mientras DBSCAN alcanzó 0.6549 con solo dos hiperparámetros, y además maneja de forma nativa el ruido/outliers sin forzarlos a un cluster (`reports/clustering_experiments.md`).

**P: ¿Silhouette 0.65 es "bueno"? ¿Cómo lo saben?**
R: Un Silhouette > 0.5 se considera generalmente indicativo de estructura de cluster razonable en la literatura; aquí además se validó por estabilidad (el óptimo se sostiene en el rango eps∈[2.3, 2.7], no es un pico aislado producto del azar) — ver `reports/final_model_selection.md`.

*(Nota interna: si eligen ejecutar la Fase 2, aquí también deben poder mostrar `cluster_profiles.md` con ejemplos concretos de qué caracteriza a 2-3 clusters específicos, en vez de solo citar el Silhouette agregado.)*

### Recomendación
**P: ¿Por qué el sistema híbrido no tiene la mejor Precision@5 de la tabla (la tiene Popularity o PageRank)?**
R: Popularity y PageRank son rankings estáticos no personalizados que recomiendan casi siempre los mismos productos "universales" a todos los households — de ahí su coverage bajo (22% y 26% respectivamente). El híbrido sacrifica un poco de precisión agregada a cambio de **100% de coverage** (recomienda todo el catálogo, no solo los 13 productos más populares) y de incorporar la señal de vencimiento, que es central a la pregunta de producto del proyecto (reducir desperdicio). Es una decisión de diseño de producto, no una debilidad del modelo (`reports/graph_analytics_report.md`, sección 4).

**P: ¿Cómo evitan leakage temporal en la evaluación?**
R: El protocolo de Masked Basket Completion Task enmascara aleatoriamente el 20% de interacciones no-cero dentro de la misma sesión (no una predicción cronológica hacia el futuro), lo que evalúa la capacidad de completar una canasta parcialmente observada — una tarea de cross-selling intra-sesión, explícitamente distinta de forecasting temporal, y así documentado en el docstring de `src/evaluation.py`.

### Grafos
**P: Si el grafo está completamente conectado (1,225/1,225 aristas), ¿qué aporta realmente el análisis de grafos?**
R: La topología binaria es efectivamente trivial dado el tamaño del catálogo (50 nodos) y el volumen de sesiones (1,177), pero la señal relevante vive en los **pesos** de las aristas (frecuencia de co-ocurrencia) y en cómo esos pesos se traducen en PageRank ponderado, que sí discrimina productos "puente" de alta rotación (frutas/verduras frescas) frente a productos de nicho. Además, PageRank supera a Popularity simple en Precision@5 y MAP@5 (+6.5% y +10.4% respectivamente), lo que demuestra que la centralidad estructural aporta señal incremental real, no solo redundante con la frecuencia (`reports/graph_analytics_report.md`, sección 4).

### Evaluación
**P: ¿Por qué compararon 5 sistemas y no solo el híbrido final?**
R: Para poder atribuir el valor de cada componente por separado (popularidad como piso, PageRank como señal estructural pura, contenido y CF como señales de personalización) y así justificar cuantitativamente por qué el híbrido combina lo mejor de cada uno en vez de simplemente afirmar que "el híbrido es mejor" sin evidencia comparativa.

### Reproducibilidad
**P: Si clono el repositorio ahora mismo, ¿puedo reproducir todos sus resultados?**
R (después de completar la Fase 1 y 7 de este plan): Sí — `pip install -r requirements.txt` funciona en un entorno limpio, y el runbook documenta los 19 scripts en el orden exacto de ejecución, cada uno con sus entradas/salidas declaradas explícitamente.

*(Antes de completar la Fase 1, la respuesta honesta sería "con un ajuste menor a requirements.txt", que es precisamente por lo que esta corrección es prioridad alta y no cosmética.)*

### Decisiones técnicas generales
**P: ¿Cuál fue la decisión técnica más difícil o más discutible del proyecto, y cómo la justifican?**
R (sugerida): la discretización de variables nutricionales continuas en tokens de texto (`cal_low`, `prot_mid`) para poder incluirlas en el espacio TF-IDF del recomendador de contenido. El equipo mismo reconoce que esto introduce un supuesto de ortogonalidad falso entre niveles adyacentes (bajo vs. medio se trata igual de "distinto" que bajo vs. alto), y lo documenta como deuda técnica explícita para una futura migración a encoding ordinal continuo o arquitecturas de dos torres (`reports/recommendation_experiments.md`, sección 2). Mostrar esta autocrítica de forma proactiva en la defensa es más fuerte que esperar a que el profesor la encuentre.

---

## 11. Recomendaciones de Mejora: de "Aprobado" a "Sobresaliente"

Actuando como evaluador del curso, estas son las mejoras que elevarían más la calificación relativa al esfuerzo que requieren:

1. **Umbral de poda en el grafo (edge thresholding) + detección de comunidades.** Hoy el grafo es completo y la topología no discrimina. Aplicar un umbral (p. ej. conservar solo aristas con peso > percentil 75) y correr un algoritmo de detección de comunidades (Louvain o label propagation, ambos disponibles en NetworkX) generaría una topología no trivial. **Valor añadido especialmente alto:** permite comparar las comunidades del grafo contra los 38 clusters de DBSCAN — si coinciden razonablemente, es una validación cruzada independiente y elegante de la segmentación del proyecto (dos métodos completamente distintos, features vs. co-ocurrencia transaccional, llegando a conclusiones similares). Esto es exactamente el tipo de conexión entre capas que un evaluador busca en un proyecto "sobresaliente" y no cuesta más de un día de trabajo.

2. **Intervalos de confianza / bootstrap sobre las métricas de evaluación.** Actualmente todas las cifras de `evaluation_table.csv` son puntuales (una sola corrida con seed=42). Un bootstrap de la partición hold-out (p. ej. 100 remuestreos) daría un intervalo de confianza para Precision@5/MAP@5 por sistema, permitiendo afirmar con rigor estadístico si la diferencia entre Hybrid y CF-ALS es significativa o es ruido de muestreo. Esto atiende directamente el criterio de evaluación "metric rigor".

3. **Explicabilidad del recomendador híbrido en el demo.** Descomponer, para cada recomendación mostrada, cuánto aportó cada señal ($w_C$ contenido, $w_F$ CF, $w_E$ vencimiento, y el nuevo $w_G$ de PageRank si se implementa la Fase 3) en un mini-gráfico de barras apiladas. Esto convierte al sistema de una "caja negra que da un top-5" a un sistema interpretable, muy valorado en evaluación de sistemas de recomendación aplicados.

4. **Prueba empírica de escalabilidad, no solo teórica.** `reports/scale_analysis.md` presenta complejidad Big-O teórica pero ninguna medición real. Correr el pipeline con un dataset sintético 5x o 10x más grande (más hogares/días de simulación) y reportar tiempos reales de `preprocessing.py`/`features.py` con Polars convertiría una afirmación teórica en evidencia empírica de la escalabilidad reclamada.

5. **Dashboard interactivo en vez de (o además del) notebook de demo.** El brief menciona explícitamente "small dashboard" como una opción de mayor peso percibido que un notebook. Un Streamlit ligero (selector de household → recomendaciones → grafo interactivo con `pyvis` o `plotly`) es alcanzable en menos de un día dado que todos los artefactos ya existen, y comunica mucho mejor el producto en una defensa de tiempo limitado que un notebook con celdas.

6. **Test de significancia sobre la comparación PageRank vs. Popularity.** La afirmación "PageRank supera a Popularity en Precision@5 (+6.5%)" es más convincente con una prueba de McNemar o un bootstrap pareado que confirme que la diferencia no es azar, dado que ambos comparten el mismo carácter de ranking no personalizado y por tanto son directamente comparables sesión por sesión.

7. **Sección de conclusiones que cuantifique el "producto question" original.** La pregunta de producto (`reports/proposal.md`) pregunta explícitamente cómo optimizar consumo considerando vencimiento + nutrición + co-ocurrencia simultáneamente. El informe final debería cerrar con una respuesta cuantitativa directa a esa pregunta (p. ej., "el sistema híbrido reduce en X% el desperdicio simulado frente a un baseline sin señal de vencimiento" — esta comparación puede construirse fácilmente ablacionando $w_E=0$ vs. el híbrido de producción, algo que `hybrid_ablation.csv` ya casi contiene).

8. **CI ligero (GitHub Actions) que corra un smoke test en cada push.** Incluso un workflow mínimo que instale `requirements.txt` y corra `pytest tests/` en cada commit es una señal fuerte y de bajo costo de madurez de ingeniería que distingue un proyecto de curso de un proyecto "productizado", exactamente el espíritu del criterio "reproducibility" de la rúbrica.

9. **Visualización de red mejorada.** La figura actual de `reports/figures/hito5/graph_network.png` sería más informativa coloreada por comunidad (si se implementa la recomendación 1) y con el tamaño de nodo proporcional al PageRank, en vez de un layout genérico — mejora de bajo costo con alto impacto visual en la presentación final.

10. **Métrica de "anti-desperdicio" directa, no solo proxy de precisión.** Dado que el objetivo del producto es reducir desperdicio, una métrica de negocio específica (p. ej., "% de recomendaciones top-5 que corresponden a productos con vencimiento ≤ 3 días, ponderado por si el household realmente los consumió en el hold-out") comunicaría el valor del proyecto en el lenguaje del problema, no solo en el lenguaje genérico de recsys (precision/recall), reforzando la coherencia narrativa que valora el criterio de "Final Defense" de la rúbrica ("coherence between objective, data, model, and evaluation").
