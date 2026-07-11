# `data/recommender/` — Artefactos del Hito 4

Outputs del pipeline de recomendación (Semana 11). Todos los archivos se
regeneran de cero ejecutando los scripts en `src/` listados en
[`runbook.md`](../../runbook.md).

## Matrices de interacción R

| Archivo                          | Forma         | Encoding                                  | Generado por |
| -------------------------------- | ------------- | ----------------------------------------- | ------------ |
| `R_restock_bin.npz`              | 1177 × 50     | Binaria (presencia/ausencia)               | `build_R.py` |
| `R_restock_count.npz`            | 1177 × 50     | Conteo de eventos por sesión               | `build_R.py` |
| `R_restock_qty.npz`              | 1177 × 50     | Suma de `quantity` por sesión              | `build_R.py` |
| `R_restock_freq.npz`             | 1177 × 50     | Conteo / tamaño de sesión (stochastic)     | `build_R.py` |
| `R_kitchen_bin.npz`              | 8075 × 50     | Binaria sobre sesiones de OUT 15 min       | `build_R.py` |
| `R_kitchen_count.npz`            | 8075 × 50     | Conteo sobre kitchen sessions              | `build_R.py` |
| `R_household_bin.npz`            | 10 × 50       | Binaria sobre household (caso base)        | `build_R.py` |
| `R_household_count.npz`          | 10 × 50       | Conteo por household                        | `build_R.py` |

## Normalizaciones de R

| Archivo                          | Transformación aplicada                    | Generado por        |
| -------------------------------- | ------------------------------------------ | ------------------- |
| `R_restock_raw.npz`              | Sin tocar (línea base)                     | `normalizations.py` |
| `R_restock_row_mean_center.npz`  | Resta media por fila                       | `normalizations.py` |
| `R_restock_log1p.npz`            | log(1+x)                                   | `normalizations.py` |
| `R_restock_tfidf_R.npz`          | TF-IDF tratando R como (sesión × producto) | `normalizations.py` |
| `R_restock_l2_row.npz`           | Normalización L2 por fila                  | `normalizations.py` |

## Recomendador basado en contenido (TF-IDF)

| Archivo                  | Contenido                                            |
| ------------------------ | ---------------------------------------------------- |
| `tfidf_items.npz`        | Matriz TF-IDF L2-normalizada (50 × 93 tokens)        |
| `tfidf_vocab.json`       | Mapeo token → índice                                 |
| `product_catalog.csv`    | Catálogo con `doc` agregado por producto              |
| `item_sim_content.npy`   | Similitud coseno ítem-ítem por contenido (50 × 50)   |

## Filtrado colaborativo (ALS)

| Archivo                | Contenido                                           |
| ---------------------- | --------------------------------------------------- |
| `item_sim_cf_dot.npy`  | Co-ocurrencia ítem-ítem (dot product sobre `bin`)   |
| `item_sim_cf_cosine.npy` | Similitud coseno ítem-ítem por comportamiento     |
| `als_X.npy`            | Factores latentes de sesión (1177 × 16)             |
| `als_Y.npy`            | Factores latentes de producto (50 × 16)             |
| `als_meta.json`        | Hiperparámetros del ALS final + métricas             |
| `lambda_sweep.csv`     | Resultados del barrido de λ ∈ {0.001, ..., 10}      |

## Cold-start

| Archivo                          | Contenido                                |
| -------------------------------- | ---------------------------------------- |
| `cold_start_session.csv`         | precision@5 por sesión cold con 1 seed   |
| `cold_start_session_2seed.csv`   | precision@5 por sesión cold con 2 seeds  |
| `cold_start_product.csv`         | precision@5 por producto cold (content)  |
| `cold_start_summary.json`        | Estrategia ganadora + justificación      |

**Nota de terminología (por qué `partial_cf` no contradice "cold-start"):** `src/cold_start.py` evalúa dos escenarios distintos, no uno solo:
- **Producto cold (cero historial):** un producto sin ninguna sesión previa en `R`. Aquí es literalmente imposible usar CF (no hay filas/columnas de las que derivar similitud), así que solo `content_only` (TF-IDF) es viable — ver `evaluate_product_cold`.
- **Sesión/hogar cold (historial parcial):** una sesión nueva con 1-2 productos ya conocidos (`seed_items_per_session`), no cero. `partial_cf` es válido en este caso porque opera por similitud ítem-ítem sobre esos 1-2 productos conocidos (no requiere un factor latente entrenado para *esa* sesión) — es "cold" a nivel de sesión/usuario, no a nivel de producto. Es un caso de **partial/warm-start**, de ahí el nombre `partial_cf`, y no un cold-start puro con cero señal.

Esta distinción responde directamente a la objeción planteada por el profesor en la defensa de Hito 4 (Semana 11): *"si es cold start problem, you don't have any history... you cannot use collaborative filtering"* — cierta para producto cold, no aplicable a sesión cold con seeds conocidos.

## Recomendador híbrido

| Archivo                  | Contenido                                       |
| ------------------------ | ----------------------------------------------- |
| `hybrid_top10_hh0.csv`   | Top-10 recomendado para household 0 con scores  |
| `hybrid_ablation.csv`    | precision@5 por combinación de pesos (w_C,w_F,w_E) |
| `hybrid_meta.json`       | Pesos finales y fecha de referencia              |

## Evaluación consolidada (Week 10 milestone)

| Archivo                       | Contenido                                                  |
| ----------------------------- | ---------------------------------------------------------- |
| `evaluation_table.csv`        | Tabla 4 sistemas × 4 métricas sobre hold-out común         |
| `evaluation_summary.json`     | Protocolo + resultados completos                            |
| `error_analysis.csv`          | 5 strong cases + 5 failure cases (híbrido)                  |

## Metadatos

| Archivo                       | Contenido                                  |
| ----------------------------- | ------------------------------------------ |
| `products.json`               | Catálogo de productos ordenado por id      |
| `sessions_restock.json`       | Lista de session_id para restock           |
| `sessions_kitchen.json`       | Lista de session_id para kitchen           |
| `sparsity_report.json`        | Densidad / nnz por variante de R           |
| `normalization_summary.json`  | Stats por normalización                    |

## Cómo regenerar

```bash
python src/build_R.py
python src/recommender_content.py
python src/normalizations.py
python src/recommender_cf.py
python src/cold_start.py
python src/recommender_hybrid.py
python src/evaluation.py
python src/generate_hito4_figures.py
```

Tiempo total end-to-end: ~20 segundos en máquina estándar.
