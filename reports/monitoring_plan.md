# Plan de Monitoreo y Operacionalización

> Entregable de Semana 14. Describe qué se mediría, con qué cadencia se
> reentrenaría y qué dispararía una alerta si Smart Kitchen Intelligence (SKI)
> pasara de prototipo académico a un sistema en producción con datos reales de
> households. No introduce infraestructura nueva: formaliza umbrales sobre
> métricas que el pipeline actual ya calcula (`evaluation_table.csv`,
> `graph_metrics.json`, `sparsity_report.json`).

## 1. Qué se mide

### 1.1 Métricas de calidad del recomendador (por corrida de `evaluation.py`)

| Métrica | Artefacto fuente | Valor actual (referencia) | Qué vigila |
| :--- | :--- | :--- | :--- |
| Catalog Coverage@5 | `evaluation_table.csv` (`coverage@k`) | Hybrid = 100%, Popularity = 22% | Que el sistema en producción siga recomendando el catálogo completo y no colapse hacia un puñado de productos populares (el mismo patrón de "Sesgo Basal" ya documentado en `evaluation_summary.json`). |
| Precision@5 / MAP@5 | `evaluation_table.csv` | Hybrid: P@5=0.0494, MAP@5=0.0574 | Degradación del ranking frente a la línea base congelada del informe. |
| Recall@5 / nPrecision@5 | `evaluation_table.csv` | — | Complementan Precision@5 cuando el tamaño del truth set cambia (ver nota de comparabilidad en `evaluation_summary.json`). |

**Umbral de alerta sugerido:** caída de más de 15% relativo en `coverage@5` o `map@k` del sistema de producción (hybrid v1) respecto al valor congelado en `evaluation_table.csv` en la última corrida aceptada.

### 1.2 Staleness de metadata nutricional (USDA FoodData Central)

`src/ingestion.py` consulta la API de la USDA **una sola vez por producto**, en el momento de construir `data/raw/catalog_raw.csv`; el pipeline actual no registra ni versiona la fecha de esa consulta. Esto es una brecha real y no una posibilidad hipotética: si el catálogo creciera o los datos nutricionales de la USDA se corrigieran aguas arriba, SKI no tendría forma de saberlo.

**Métrica propuesta:** `dias_desde_ultima_consulta_usda` por producto, calculada a partir de un timestamp `usda_fetched_at` que debería añadirse a `catalog_raw.csv` (hoy ausente).

**Umbral de alerta sugerido:** reconsultar cualquier producto con `dias_desde_ultima_consulta_usda > 180`, y el catálogo completo si supera ese umbral el `journal_median_gap` reportado en `reports/data_dictionary.md`.

### 1.3 Drift de la distribución de consumo

El simulador (`src/simulation.py`) parametriza sus distribuciones estocásticas a partir de `data/raw/instacart_patterns.json` (frecuencia por producto, distribución horaria de compra). Si SKI se conectara a datos reales de households, la distribución observada podría desviarse de esas distribuciones base.

**Métrica propuesta:** distancia de Kolmogorov-Smirnov (o divergencia KL discretizada) entre:
- la distribución horaria de eventos `OUT` observada en la ventana de monitoreo (p. ej. últimos 30 días), y
- la distribución horaria base de `instacart_patterns.json` usada para calibrar el simulador.

Análogamente para la distribución de frecuencia relativa por producto (¿qué tan parecida es la popularidad observada a la usada para entrenar CF/PageRank?).

**Umbral de alerta sugerido:** KS-statistic > 0.15 en cualquiera de las dos distribuciones sobre una ventana móvil de 30 días, evaluado semanalmente.

### 1.4 Salud estructural del grafo de co-ocurrencia

`graph_analytics.py` ya calcula componentes conexas, grado ponderado y PageRank (`data/recommender/graph_metrics.json`). En producción, estos números deberían monitorearse porque son la base de dos sistemas evaluados (`pagerank`, y potencialmente `hybrid_v2_graph`):

| Métrica | Valor actual (referencia) | Umbral de alerta |
| :--- | :--- | :--- |
| Componentes conexas | 1 | > 1 (el grafo se fragmenta: aparecen productos sin co-ocurrencia con el resto del catálogo) |
| Grado ponderado medio | 1,822.8 | Caída > 30% (sesiones de restock se vuelven más pequeñas o menos diversas) |
| Densidad de aristas | 100% (grafo completo, 1,225/1,225) | Caída por debajo de 80% (indicaría que el catálogo creció más rápido que la co-ocurrencia observada) |

### 1.5 Sparsity de las matrices de interacción R

`build_R.py` y `normalizations.py` ya producen `sparsity_report.json` (densidad actual de `R_restock_bin` ≈ 17.4%, `row_nnz` medio ≈ 8.7 productos/sesión). Una caída sostenida de densidad indicaría sesiones de restock cada vez más pequeñas/dispersas, lo cual degrada tanto CF (menos señal por sesión) como el candidate pool de evaluación.

**Umbral de alerta sugerido:** densidad de `R_restock_bin` por debajo de 10% sobre una ventana móvil de 4 semanas.

## 2. Cadencia de reentrenamiento sugerida

| Componente | Cadencia sugerida | Justificación |
| :--- | :--- | :--- |
| Matrices R (`build_R.py`) | Semanal | Ventana de sesión de 60 min es sensible a la acumulación de nuevas transacciones; recalcular semanalmente mantiene las sesiones representativas sin sobrecargar el pipeline. |
| Perfiles de contenido / TF-IDF (`recommender_content.py`) | Al agregar/retirar productos del catálogo | El vocabulario TF-IDF depende directamente del catálogo; no necesita recalcularse por volumen transaccional, solo por cambios de catálogo. |
| Factores ALS (`recommender_cf.py`) | Semanal, junto con R | Los factores latentes deben reflejar la co-ocurrencia más reciente; el barrido de λ (`lambda_sweep.csv`) puede re-ejecutarse mensualmente en vez de semanalmente, ya que el óptimo ($\lambda=1.0$) es estable frente a cambios incrementales de volumen. |
| Grafo de co-ocurrencia + PageRank (`graph_construction.py`, `graph_analytics.py`) | Semanal, junto con R | Se deriva de la misma matriz `R_restock_bin`; recalcularlo fuera de ciclo con R produciría métricas de grafo desalineadas con los factores de CF usados en la misma evaluación. |
| Pesos del ensamble híbrido (`recommender_hybrid.py`, ablación) | Trimestral, o al detectar alerta en §1.1 | La ablación de pesos es costosa de interpretar (requiere re-validar contra `evaluation.py`); no se justifica recalcularla en cada ciclo semanal salvo que una métrica de calidad dispare alerta. |
| Catálogo nutricional (USDA) | Cada 6 meses, o al detectar alerta en §1.2 | Los datos nutricionales de un mismo producto cambian con muy baja frecuencia; una cadencia semestral es proporcional al riesgo real de desactualización. |

## 3. Qué dispara una alerta (resumen operativo)

1. **Alerta de calidad de recomendación:** `coverage@5` o `map@k` del sistema de producción cae más de 15% relativo frente a la última corrida aceptada de `evaluation_table.csv`.
2. **Alerta de staleness de catálogo:** cualquier producto sin refresco de USDA en más de 180 días.
3. **Alerta de drift de consumo:** KS-statistic > 0.15 entre la distribución observada (30 días) y la distribución base de `instacart_patterns.json`.
4. **Alerta de salud del grafo:** el grafo de co-ocurrencia deja de ser conexo (>1 componente), o la densidad de aristas cae por debajo de 80%.
5. **Alerta de sparsity:** densidad de `R_restock_bin` por debajo de 10% en una ventana móvil de 4 semanas.

Cualquiera de estas alertas debería disparar, como mínimo, una re-ejecución fuera de ciclo de `evaluation.py` y una revisión manual antes de decidir si se dispara un reentrenamiento fuera de la cadencia regular de la Sección 2.

## 4. Boceto de arquitectura de despliegue (conceptual)

SKI es, hoy, un pipeline batch de scripts secuenciales (ver `runbook.md`), no un servicio en tiempo real. Para un despliegue conceptual se sugiere mantenerlo así:

- **Batch diario/semanal:** recálculo de `R_*`, factores ALS, grafo y métricas de monitoreo (Sección 1), ejecutado como un job programado (cron / scheduler) que corre la secuencia de `runbook.md` §5-§6.
- **Serving:** los artefactos resultantes (`item_sim_content.npy`, `als_Y.npy`, `graph_metrics.json`, pesos de `hybrid_meta.json`) se cargan en memoria por un servicio de recomendación ligero (análogo a `src/demo_app.py`) que sirve el top-N sin recalcular nada en tiempo real.
- **Tiempo real** solo sería necesario para el componente de expiry (`score_expiry`), ya que depende del inventario vivo del household al momento de la consulta — este es, de hecho, el único componente del ensamble que ya se calcula on-demand en el código actual (`recommender_hybrid.py::score_expiry`).

Esta separación batch/serving es consistente con la arquitectura actual: no requiere reescribir ningún componente, solo programar su ejecución periódica y envolver la carga de artefactos en un servicio.
