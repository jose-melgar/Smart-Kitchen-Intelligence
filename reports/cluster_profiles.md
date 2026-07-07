# Perfiles de Clusters DBSCAN (Hito 3 — Cluster Profiling)

> Generado automáticamente por `src/cluster_profiling.py`. Fuentes: `data/features/cluster_labels_refined.npy`,
> `data/features/feature_matrix.npy`, `data/features/feature_names.json`, `data/processed/inventory_v1.csv`.
> No contiene datos de relleno: cada cifra se calcula directamente sobre la distribución real de clusters.

## 1. Resumen General

- Eventos totales: **25444**
- Clusters identificados (excluyendo ruido): **38**
- Puntos de ruido (label -1): **71** (0.28% del total)

## 2. Perfil por Cluster

Para cada cluster se reporta el tamaño, las hasta 3 categorías de producto más frecuentes
(`category_<id>`, identificador USDA/Instacart del catálogo — no existe un mapeo textual de
categorías en el repositorio), la característica original con mayor desviación respecto a la
media global del dataset (`Δ` en unidades estandarizadas, ya que `feature_matrix.npy` está escalado
con `StandardScaler`), y el patrón temporal dominante.

| Cluster | N | % Total | Categorías Dominantes (top 3) | Feature Más Distintivo (Δ vs. media global) | Hora Media | Día Dominante |
| :--- | ---: | ---: | :--- | :--- | ---: | :--- |
| 0 | 1002 | 3.94% | category_4 (100.0%) | `txt_honeycrisp` (+4.92) | 14.1h | Miércoles |
| 1 | 1098 | 4.32% | category_16 (100.0%) | `txt_half` (+4.71) | 13.5h | Miércoles |
| 2 | 508 | 2.00% | category_3 (100.0%) | `txt_100` (+6.99) | 13.0h | Martes |
| 3 | 973 | 3.82% | category_7 (100.0%) | `txt_water` (+5.01) | 12.6h | Sábado |
| 4 | 540 | 2.12% | category_16 (100.0%) | `txt_almond` (+6.78) | 12.7h | Sábado |
| 5 | 1417 | 5.57% | category_4 (66.3%), category_16 (33.7%) | `txt_organic` (+3.40) | 13.9h | Sábado |
| 6 | 527 | 2.07% | category_20 (100.0%) | `txt_hummus` (+6.88) | 13.1h | Domingo |
| 7 | 1017 | 4.00% | category_1 (50.8%), category_4 (49.2%) | `txt_blueberries` (+4.90) | 13.6h | Lunes |
| 8 | 966 | 3.80% | category_4 (100.0%) | `txt_avocado` (+5.03) | 14.4h | Jueves |
| 9 | 1076 | 4.23% | category_4 (100.0%) | `txt_strawberries` (+4.75) | 14.4h | Sábado |
| 10 | 496 | 1.95% | category_4 (100.0%) | `txt_kirby` (+7.09) | 13.9h | Martes |
| 11 | 978 | 3.84% | category_4 (100.0%) | `txt_yellow` (+4.91) | 14.0h | Miércoles |
| 12 | 510 | 2.00% | category_4 (100.0%) | `txt_carrots` (+4.06) | 14.3h | Domingo |
| 13 | 1025 | 4.03% | category_4 (100.0%) | `txt_raspberries` (+4.88) | 14.1h | Domingo |
| 14 | 939 | 3.69% | category_4 (100.0%) | `txt_organic` (-0.89) | 14.2h | Domingo |
| 15 | 488 | 1.92% | category_4 (100.0%) | `txt_bell` (+7.14) | 13.9h | Domingo |
| 16 | 501 | 1.97% | category_16 (100.0%) | `txt_milk` (+6.12) | 13.5h | Lunes |
| 17 | 522 | 2.05% | category_4 (100.0%) | `txt_lemon` (+5.50) | 14.1h | Viernes |
| 18 | 499 | 1.96% | category_4 (100.0%) | `txt_blackberries` (+7.04) | 14.2h | Sábado |
| 19 | 508 | 2.00% | category_4 (100.0%) | `txt_banana` (+6.99) | 14.2h | Jueves |
| 20 | 559 | 2.20% | category_4 (100.0%) | `txt_grapes` (+6.65) | 14.2h | Domingo |
| 21 | 520 | 2.04% | category_4 (100.0%) | `txt_onion` (+4.94) | 14.8h | Jueves |
| 22 | 520 | 2.04% | category_4 (100.0%) | `txt_extra` (+6.92) | 14.4h | Sábado |
| 23 | 959 | 3.77% | category_4 (100.0%) | `txt_bunch` (+5.04) | 14.4h | Miércoles |
| 24 | 522 | 2.05% | category_4 (100.0%) | `txt_grape` (+6.88) | 14.4h | Viernes |
| 25 | 535 | 2.10% | category_4 (100.0%) | `txt_granny` (+6.82) | 14.8h | Domingo |
| 26 | 526 | 2.07% | category_4 (100.0%) | `txt_arugula` (+6.88) | 14.1h | Jueves |
| 27 | 532 | 2.09% | category_4 (100.0%) | `txt_cluster` (+6.84) | 14.3h | Martes |
| 28 | 519 | 2.04% | category_4 (100.0%) | `txt_large` (+5.91) | 14.6h | Domingo |
| 29 | 480 | 1.89% | category_4 (100.0%) | `txt_cucumber` (+5.88) | 14.6h | Lunes |
| 30 | 522 | 2.05% | category_4 (100.0%) | `txt_bag` (+6.89) | 14.2h | Viernes |
| 31 | 524 | 2.06% | category_4 (100.0%) | `txt_fuji` (+6.00) | 14.2h | Miércoles |
| 32 | 476 | 1.87% | category_4 (100.0%) | `txt_baby` (+5.11) | 13.6h | Sábado |
| 33 | 488 | 1.92% | category_4 (100.0%) | `txt_carrots` (+5.72) | 13.9h | Domingo |
| 34 | 534 | 2.10% | category_4 (100.0%) | `txt_kale` (+6.82) | 14.1h | Viernes |
| 35 | 522 | 2.05% | category_4 (100.0%) | `txt_limes` (+6.89) | 13.5h | Viernes |
| 36 | 513 | 2.02% | category_4 (100.0%) | `txt_apples` (+6.95) | 14.4h | Sábado |
| 37 | 532 | 2.09% | category_4 (100.0%) | `txt_zucchini` (+6.82) | 14.1h | Miércoles |

## 3. Análisis de Fallos (Ruido, label = -1)

DBSCAN clasificó **71 eventos (0.28% del total)** como ruido
(label `-1`), es decir, puntos que no alcanzan la densidad mínima (`min_samples=15`) dentro del radio
`eps=2.7` de ningún cluster.

- **Categorías dominantes en el ruido:** category_4 (90.1%), category_16 (5.6%), category_3 (2.8%)
- **Feature más distintivo del ruido:** `category_encoded` (Δ=-12.41 vs. media global)
- **Hora media de los eventos de ruido:** 14.0h — **Día dominante:** Martes

**Hipótesis de causa:**

1. el ruido sigue teniendo una categoría mayoritaria (90.1%), pero **menos concentrada** que el promedio de los clusters reales (97.8%), es decir, mezcla proporcionalmente más categorías minoritarias que un cluster típico.
2. Los puntos de ruido mezclan 4 categorías distintas, más que el promedio de 1.1 categorías por cluster real, consistente con una mezcla heterogénea de eventos que no encajan en ninguna densidad local.
3. La cantidad (`quantity`) media en el ruido es 1.775, mayor que la media global (1.722), sugiriendo que eventos con volúmenes de movimiento atípicos contribuyen a la caída en ruido.

En conjunto, el ruido no se explica por una única variable, sino por combinaciones poco frecuentes
de categoría, franja horaria y volumen de movimiento que no forman una vecindad densa suficiente
según los hiperparámetros del modelo ganador (DBSCAN, eps=2.7, min_samples=15).
