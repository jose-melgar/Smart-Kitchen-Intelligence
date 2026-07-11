# Guía de Defensa — Hito 5 (Semana 12)
## Smart Kitchen Intelligence — Analítica de Grafos y PageRank

> Documento interno de preparación para la exposición.
> Estructura: (1) qué se hizo, (2) cómo se conecta con los hitos previos, (3) resultados, (4) respuestas listas a las preguntas típicas del profe Carlos.

---

## 1. El proyecto en una frase

**Smart Kitchen Intelligence (SKI)** es un sistema de Big Data para **reducir desperdicio de comida en el hogar** y **sugerir el siguiente restock** combinando: afinidad histórica del hogar + patrones latentes colectivos + urgencia por vencimiento.

**Usuario principal:** el hogar (representado como un “household” en la simulación). El sistema le devuelve un **top-5 de productos** a reponer.

**Output del modelo:** dado un hogar (o una sesión de restock en curso) → lista ranqueada de los próximos 5 productos a comprar/usar, con razonamiento detrás (perfil de contenido, filtrado colaborativo, urgencia de vencimiento y, desde el Hito 5, importancia estructural en la red).

---

## 2. Recorrido completo del pipeline (Hito 1 → Hito 5)

```
Hito 1 (S3)  Ingesta + Simulación  →  inventory_v1.csv (25,444 eventos, 10 hogares, 50 productos)
Hito 2 (S5)  Features + PCA        →  72,000 × 61  →  30 PCs (90% varianza) + t-SNE
Hito 3 (S7)  Clustering            →  DBSCAN (ε=2.7, min_samples=15) → 38 perfiles, Silhouette 0.6549
Hito 4 (S11) Recomendador híbrido  →  Content (TF-IDF) + CF (ALS) + Expiry → MAP@5 0.0574, Coverage 100%
Hito 5 (S12) Grafo + PageRank      →  Red 50×1225 ponderada + PageRank vs Popularity como ranking baseline
```

Cada hito **reusa** los artefactos del anterior. El Hito 5 **no genera datos nuevos**: opera enteramente sobre la matriz `R_restock_bin.npz` (1,177 × 50) producida en Hito 4.

---

## 3. Qué se hizo específicamente en el Hito 5

### 3.1 Construcción del grafo de co-ocurrencia
**Script:** `src/graph_construction.py`
**Idea:** dos productos están “relacionados” si tienden a aparecer juntos en la misma **sesión de restock** (ventana de 60 min por hogar).

**Método (una línea):**

```python
adjacency = (R.T @ R).toarray()   # R es 1177 × 50  →  A es 50 × 50
```

Donde `A[i][j]` = número de sesiones en las que los productos *i* y *j* co-aparecen.

**Salida:** `data/recommender/kitchen_graph.gexf`

**Resultado topológico:**

| Propiedad | Valor |
|---|---|
| Nodos (productos) | 50 |
| Aristas | 1,225 |
| Componentes conexas | 1 |
| Densidad | 1.0 (grafo completo) |

> El grafo es **completo**: cada par de productos ha co-aparecido al menos una vez en los 90 días. La discriminación está en los **pesos**, no en la topología binaria.

### 3.2 Métricas estructurales
**Script:** `src/graph_analytics.py`

- **Grado ponderado** = suma de pesos de aristas incidentes a un nodo.
  - Min 1,613 · Max 1,996 · Media 1,822.8
- **PageRank ponderado** (α = 0.85, NetworkX por defecto):
  - σ ≈ 0.00094 (distribución casi uniforme — el grafo es muy denso)

**Top-10 PageRank:**

| Rank | Producto | PR |
|---|---|---|
| 1 | Yellow Onions | 0.0216 |
| 2 | Strawberries | 0.0216 |
| 3 | Organic Avocado | 0.0215 |
| 4 | Seedless Red Grapes | 0.0214 |
| 5 | Organic Raspberries | 0.0214 |
| 6 | Organic Strawberries | 0.0213 |
| 7 | Organic Baby Spinach | 0.0210 |
| 8 | 100% Whole Wheat Bread | 0.0209 |
| 9 | Organic Hass Avocado | 0.0208 |
| 10 | Sparkling Water | 0.0207 |

**Interpretación semántica:** frutas frescas y verduras básicas — productos “universales” de alta rotación.

### 3.3 PageRank como sistema de ranking
**Script:** `src/evaluation.py` (extendido del Hito 4).

PageRank se incorpora como un **quinto sistema** del benchmark, usando exactamente el mismo protocolo del Hito 4: **Masked Basket Completion Task** (Cloze Task Style), hold-out 20% con semilla 42, 968 sesiones evaluadas, 2,094 interacciones ocultas.

PageRank funciona como un **ranking estático no personalizado**: el mismo vector de scores se repite para todas las sesiones.

---

## 4. Resultados — la tabla central

| Sistema | Precision@5 | Recall@5 | MAP@5 | Coverage@5 |
|---|---|---|---|---|
| Popularity | 0.0508 | 0.1167 | 0.0539 | 22.0% |
| **PageRank** | **0.0541** | **0.1283** | **0.0595** | **26.0%** |
| Content (TF-IDF) | 0.0450 | 0.1037 | 0.0511 | 84.0% |
| CF (ALS) | 0.0467 | 0.1125 | 0.0549 | 100.0% |
| **Hybrid** | 0.0494 | 0.1177 | 0.0574 | **100.0%** |

**Tres hallazgos clave:**

1. **PageRank > Popularity** en todas las métricas de ranking: +6.5% Precision, +10.4% MAP. → La centralidad estructural captura más que la frecuencia simple.
2. **PageRank tiene Coverage = 26%**: es un ranking estático, recomienda siempre los mismos ~13 productos → no sirve como sistema autónomo.
3. **Hybrid sigue siendo el sistema de producción**: 100% Coverage + segundo mejor MAP, único que descubre productos del long tail.

---

## 5. Cómo todo está conectado

```
inventory_v1.csv  (Hito 1)
        │
        ├─► features_72k_61.csv  →  PCA(30) + t-SNE  (Hito 2)
        │                                  │
        │                                  └─► DBSCAN ε=2.7  →  38 clusters  (Hito 3)
        │
        └─► build_R.py  →  R_restock_bin.npz (1177×50)  (Hito 4)
                                  │
                  ┌───────────────┼────────────────┬─────────────────┐
                  ▼               ▼                ▼                 ▼
            TF-IDF items     ALS (λ-sweep)    Expiry vector    R.T @ R  (Hito 5)
                  │               │                │                 │
                  └───────┬───────┴────────┬───────┘                 ▼
                          ▼                ▼              kitchen_graph.gexf
                  recommender_hybrid  evaluation.py             │
                          │                ▲              graph_analytics.py
                          │                │                    │
                          └────────────────┴────────────────────┘
                                           │
                                           ▼
                            evaluation_table.csv  (5 sistemas)
```

**Lo que une al Hito 5 con todo lo anterior:** la misma matriz R, el mismo protocolo de evaluación, el mismo catálogo, las mismas sesiones. PageRank es una **señal extra** que se está validando antes de integrarla al ensamble del Hito 6.

---

## 6. Guion de defensa según el modelo del profe Carlos

> El profe sigue 4 capas: (1) problema de negocio → (2) “¿por qué?” a cada decisión → (3) comprensión técnica real → (4) robustez. Aquí van las respuestas listas, con datos, en el formato “qué hiciste · por qué · qué alternativas descartaste”.

### Capa 1 — Problema de negocio (lo primero que va a preguntar)

**P: ¿Qué quieres hacer?**
Reducir desperdicio de alimentos en el hogar sugiriendo el restock óptimo. El sistema responde: dado un hogar y su inventario actual, ¿qué 5 productos debe priorizar?

**P: ¿Quién es el usuario?**
Un hogar (household). No es un negocio, no es un coach. Es un consumidor doméstico cuyo dolor es comprar de más, dejar caducar productos y no saber qué reponer.

**P: ¿Cuál es el output del modelo?**
Lista ranqueada top-5 de productos (`product_id` → score). En la evaluación se mide cuántos de esos 5 coinciden con la **canasta enmascarada** de esa sesión.

**P: ¿Cuál es el uso práctico?**
Antes de un restock, el hogar abre la app y ve “estos 5 productos son los que probablemente necesitas y/o se te van a vencer pronto”. Cierra el loop entre consumo, vencimiento y reposición.

### Capa 2 — Justificación de CADA decisión (su pregunta firma: “¿por qué?”)

Cada respuesta lleva el patrón **qué · por qué (con dato) · alternativas descartadas**.

#### ¿Por qué `R^T · R` y no otro método para construir el grafo?
- **Qué:** producto matricial entre la transpuesta y la matriz binaria de sesiones.
- **Por qué:** equivale a la proyección estándar de un grafo bipartito (sesión-producto) sobre la dimensión de productos. Cada entrada `A[i][j]` tiene una **interpretación directa**: cuántas sesiones contienen ambos productos. No hay parámetro libre, no hay magia.
- **Alternativas descartadas:**
  - PMI / lift: requiere normalizar por frecuencia marginal; con 50 productos y un grafo denso, la señal de PMI se vuelve ruidosa.
  - Cosine similarity entre columnas: la usamos en CF ítem-ítem (`recommender_cf.py`), pero para el grafo queremos **conteo absoluto** porque PageRank es invariante a reescalamientos monotónicos por nodo.

#### ¿Por qué ventana de sesión = 60 min para restock?
- **Qué:** una “sesión de restock” = eventos `IN` del mismo hogar separados por ≤ 60 min.
- **Por qué:** el simulador estocástico genera bursts de eventos `IN` cuando un hogar regresa del mercado. 60 min cubre el tiempo realista de descargar y registrar la compra. Resultado: 1,177 sesiones bien separadas con un nnz de ~5,236 (densidad ~8.9%).
- **Alternativas descartadas:**
  - 15 min → demasiado corto, fragmenta una sola compra en 3-4 sesiones falsas.
  - Toda la jornada (8h+) → mezcla compras de distintos momentos del día.
- Lo mismo aplica para kitchen sessions (eventos OUT) con 15 min — pero esa rama no se usa en Hito 5.

#### ¿Por qué PageRank y no otra métrica de centralidad?
- **Qué:** PageRank ponderado (α = 0.85).
- **Por qué:** captura **importancia transitiva** — un producto es central si co-ocurre con otros productos centrales. En un grafo completo donde el grado simple es trivial (49 para todos), necesitamos una métrica que pondere por la **calidad de los vecinos**, no solo la cantidad.
- **Alternativas descartadas:**
  - **Betweenness:** en un grafo completo, todos los caminos cortos son aristas directas → betweenness ≈ 0 para todos. No discrimina.
  - **Closeness:** mismo problema, distancia 1 entre todos los pares.
  - **Eigenvector centrality:** matemáticamente similar a PageRank, pero PageRank tiene un factor de teletransporte que garantiza convergencia y se usa industrialmente — es defendible y citable (Brin & Page, 1998).
  - **Grado ponderado:** la mantenemos como métrica complementaria, pero no como sistema de ranking porque su correlación con PageRank es muy alta y PageRank ya la subsume.

#### ¿Por qué α = 0.85 en PageRank?
- **Qué:** factor de amortiguación (damping) = 0.85.
- **Por qué:** es el **valor estándar de Brin & Page (1998)** y el default de NetworkX. Representa la probabilidad de seguir un enlace vs teletransportarse a un nodo aleatorio. Reducirlo aumenta el efecto de la distribución uniforme y aplana los rankings; subirlo cerca de 1 puede romper convergencia.
- **Alternativas descartadas:** no se hizo barrido porque con un grafo completo de 50 nodos las diferencias entre α ∈ [0.7, 0.95] son del orden de 10⁻⁴, irrelevantes para el ranking top-5. Lo registramos como limitación: en un dataset real con grafo disperso sí valdría la pena calibrar.

#### ¿Por qué hold-out 20% y semilla 42?
- **Qué:** se enmascara el 20% de las interacciones no-cero de cada sesión.
- **Por qué:** con 1,177 sesiones y nnz ~5,236, el 20% deja ~1,047 interacciones de test distribuidas en 968 sesiones (truth ≈ 1-2 por sesión). Suficiente para tener señal sin reventar la matriz de train.
- **Por qué hold-out aleatorio y no temporal:** el objetivo es **basket completion intra-sesión** (cross-selling en tiempo real), no predicción longitudinal. El hold-out temporal mediría otra cosa (concept drift), no nuestro caso de uso.
- **Alternativas descartadas:**
  - 10% → truth demasiado pequeño, alta varianza en MAP.
  - 50% → train demasiado pobre para ALS converja con factores=16.
  - Semilla 42 fija para reproducibilidad; el barrido completo de semillas habría que correrlo para reportar IC, no se hizo y se anota como mejora.

#### ¿Por qué α (alpha del Hybrid) = pesos (0.35, 0.45, 0.20)?
- **Qué:** pesos del ensamble lineal `w_C·content + w_F·CF + w_E·expiry`.
- **Por qué:** se determinaron por **grid search** en `recommender_hybrid.py` (función `main`, líneas 134-180). Se probaron 6 configuraciones incluyendo extremos (solo contenido, solo CF, solo expiry, content+CF balanceado) y la mezcla (0.35, 0.45, 0.20) maximiza precision@5 en el hold-out. CF pesa más porque tiene más capacidad predictiva; expiry pesa menos porque es la señal anti-desperdicio que rompe el ranking en casos críticos.
- **Alternativas descartadas:** (1,0,0), (0,1,0), (0,0,1), (0.5,0.5,0), (0.25,0.45,0.30) — todas peor en el sweep registrado en `data/recommender/hybrid_ablation.csv`.

#### ¿Por qué TF-IDF en la capa de contenido?
- **Qué:** TF-IDF sobre pseudo-documentos de cada producto (`nombre + categoría + atributos`).
- **Por qué:** el catálogo es texto corto y categórico. TF-IDF normaliza por **frecuencia inversa de documentos** — un producto que aparece con la palabra “organic” en 30 ítems no debe dominar la similitud. Sirve además como baseline reproducible y barato.
- **Cómo funciona realmente** (esto el profe lo va a pedir, ojo):
  - **TF (term frequency):** cuántas veces aparece el término en el documento.
  - **IDF (inverse document frequency):** `log(N / df_t)` donde `df_t` es en cuántos documentos aparece. Penaliza palabras ubicuas.
  - **TF-IDF = TF × IDF.** Luego cada documento es un vector disperso en R^|vocab|.
  - Para recomendar usamos **cosine similarity** entre el perfil del hogar (suma de vectores de productos vistos) y cada producto del catálogo.
- **Alternativas descartadas:**
  - **Word2Vec / Sentence-BERT:** sobre-ingeniería para un catálogo de 50 ítems con texto corto. Embeddings densos pre-entrenados no aportan sobre TF-IDF a esta escala.
  - **CatBoost Encoding sobre categorías:** ya lo usamos en el feature engineering del Hito 2 para clustering; para contenido del recomendador queremos similitud léxica directa.

#### ¿Por qué λ (lambda) elegido para ALS?
- **Qué:** barrido de λ ∈ {0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0} en `recommender_cf.py` (función `lambda_sweep`).
- **Por qué se barre:** λ es la **regularización L2** del paso de actualización en ALS (Hu, Koren, Volinsky 2008). Demasiado bajo → overfit a sesiones ricas; demasiado alto → todos los factores tienden a 0.
- **Cómo se elige el óptimo:** se compara precision@5 sobre el mismo hold-out 20%. El máximo se persiste en `als_meta.json`.
- **Otros parámetros:** factors=16, alpha=20.0, iterations=12. Alpha es la confianza incremental sobre los conteos (Hu et al.), 20 es el valor recomendado en el paper para feedback implícito.

#### ¿Por qué el grafo es no dirigido y ponderado?
- **No dirigido:** la co-ocurrencia es simétrica por construcción — si A y B aparecen juntos, A↔B es una sola relación.
- **Ponderado:** el conteo de co-ocurrencias varía entre 1,613 y 1,996; ignorar pesos perdería toda la señal porque la topología binaria es trivialmente completa.

### Capa 3 — Comprensión técnica real

#### ¿Cómo funciona PageRank en una frase?
Es el autovector principal de una matriz de transición. La idea: un “surfista aleatorio” camina por el grafo siguiendo aristas con probabilidad α, o se teletransporta a un nodo aleatorio con probabilidad 1-α. La distribución estacionaria de visitas = vector PageRank.

Fórmula iterativa que usamos:

```
PR(v) = (1-α)/N + α · Σ_{u∈N(v)} [ w(u,v) / d_w(u) ] · PR(u)
```

- **w(u,v):** peso de la arista (= co-ocurrencias entre u y v).
- **d_w(u):** grado ponderado de u (normalizador para que PR sea probabilidad).
- **N = 50**, α = 0.85.
- NetworkX itera hasta convergencia con tolerancia 1e-6.

#### ¿Qué significa cada fila/columna de R?
- **Fila u (1,177 filas):** una **sesión de restock** — burst de eventos `IN` de un hogar en una ventana de 60 min.
- **Columna i (50 columnas):** un **producto del catálogo** (OpenFoodFacts + USDA).
- **R[u][i] = 1** si el producto i fue parte de la sesión u.

#### ¿Cómo construyes R? ¿Encodings?
- En `build_R.py` se generan **4 encodings** sobre el mismo conjunto sesión × producto:
  - `R_bin` — binaria (presencia/ausencia). **Esta es la que usa el Hito 5.**
  - `R_count` — número de eventos del producto en la sesión.
  - `R_qty` — cantidad sumada (litros, gramos).
  - `R_freq` — `R_count` normalizada por tamaño de sesión (row-stochastic).
- Por defecto el recomendador usa `R_restock_tfidf_R.npz` (TF-IDF sobre `R_count`) para ALS, porque equilibra productos populares vs raros. El grafo usa `R_bin` porque la co-ocurrencia es binaria por definición.

#### ¿Qué normalizaciones aplicaste y por qué?
Documentado en `src/normalizations.py`:

| Normalización | Para qué |
|---|---|
| `raw` | baseline |
| `row_mean_center` | escalar sesiones grandes vs pequeñas |
| `log1p` | comprimir cola larga en counts/qty |
| `tfidf_R` | **previo a ALS**, penaliza productos ubicuos |
| `l2_row` | **previo a CF ítem-ítem**, convierte dot product en cosine sim |

Cada una tiene un caso de uso claro. En la presentación: TF-IDF de R para el CF, L2 para ítem-ítem, y `R_bin` directo para el grafo.

#### ¿Cómo evalúas? ¿Qué métricas y por qué?
- **Tarea:** Masked Basket Completion (Cloze Task Style). Se oculta el 20% de las interacciones; el sistema debe reconstruirlas con su top-5.
- **Métricas:**
  - **Precision@5** — fracción del top-5 que estaba en la verdad. Cruda pero estándar.
  - **Recall@5** — de los productos verdaderos, cuántos están en el top-5.
  - **MAP@5** — Mean Average Precision: pondera por la **posición** del acierto. Más estricta que Precision.
  - **Coverage@5** — cuántos productos distintos del catálogo aparecen al menos una vez en algún top-5. Mide **diversidad** del sistema. Crucial para diferenciar Popularity (22%) de Hybrid (100%).

### Capa 4 — Robustez (cold-start, evaluación, datos)

#### ¿Cómo manejas el cold-start?
- **Hogar nuevo (sin historial):** se cae al sistema de **contenido** (TF-IDF sobre catálogo) + **popularidad** como fallback. Implementado en `src/cold_start.py`.
- **Producto nuevo:** se le asigna el centroide TF-IDF de su categoría hasta tener al menos 3 sesiones de evidencia.
- **PageRank no aplica a cold-start** porque requiere co-ocurrencias observadas — explícitamente lo dejamos fuera de ese caso de uso.

#### "Si es cold-start, ¿cómo generas recomendaciones con collaborative filtering?" (pregunta que ya nos hizo el profesor en Semana 11 y quedó sin responder con claridad)
Distinguimos dos escenarios, no uno solo (`src/cold_start.py`):
- **Producto cold (cero historial):** correcto, ahí es imposible usar CF — no hay fila/columna en `R` de la que derivar similitud. Usamos solo `content_only` (TF-IDF).
- **Sesión/hogar cold (historial parcial, 1-2 productos ya conocidos):** aquí sí se puede usar `partial_cf`, porque no depende de un factor latente entrenado para esa sesión (eso sí sería imposible) — depende de la similitud ítem-ítem **precomputada** entre los 1-2 productos ya conocidos y el resto del catálogo. Es "cold" a nivel de sesión, no un cold-start absoluto de cero señal — de ahí el nombre `partial_cf` en vez de `cf` a secas.
- Respuesta corta si preguntan de nuevo: *"Depende de si el cold-start es de producto o de sesión. Con cero historial, solo content y popularidad. Con 1-2 productos ya conocidos, sí podemos usar similitud ítem-ítem CF sobre esos productos — no es collaborative filtering completo con factores entrenados para esa sesión, es collaborative filtering parcial."*

#### ¿Cómo vas a evaluar el sistema?
- **Offline (este informe):** Precision/Recall/MAP/Coverage @5 sobre hold-out 20% con seed 42, 968 sesiones.
- **Métrica de éxito real (sistema de producción):** **MAP@5 + Coverage** simultáneamente. Un Precision alto con Coverage 22% es un sistema inútil (siempre recomienda lo mismo). Por eso el Hybrid es el sistema de producción aunque PageRank lo supere en Precision cruda.

#### ¿Qué harías diferente si rehicieras el Hito 5?
- Barrer α de PageRank en {0.7, 0.8, 0.85, 0.9, 0.95} aunque el grafo sea denso, para tener datos del sweep aunque el resultado sea “no cambia”.
- Detectar comunidades (Louvain/Leiden) — en este hito no se hizo porque el grafo es completo y las comunidades quedan degeneradas. Sería interesante con un threshold de poda de aristas: por ejemplo, descartar aristas con peso < percentil 25 y ver si emergen grupos semánticos.
- Reportar intervalos de confianza con múltiples semillas (10 corridas mínimo).

#### ¿Tienes datos para respaldar X?
La tabla de la sección 4 está en `data/recommender/evaluation_table.csv`. Los scripts son deterministas con semilla 42 y reproducibles con tres comandos (`graph_construction.py` → `graph_analytics.py` → `evaluation.py`).

---

## 7. Tácticas defensivas (lo que el profe va a intentar)

### “Le pregunto al otro miembro del equipo”
Cada uno tiene que poder responder:
- Qué es R, cómo se construyó, qué significan filas y columnas.
- Por qué α = 0.85 y por qué hold-out 20%.
- Qué mide PageRank conceptualmente (surfista aleatorio).
- Por qué Hybrid es mejor que PageRank pese a tener peor Precision (respuesta: **Coverage**).

**Tareas asignadas para que cada uno domine las suyas + las del otro:**
- **Gabriel:** datos y pipeline (Hito 1-2), construcción de R, normalizaciones, evaluación.
- **José:** clustering, recomendador (Hito 3-4), grafo y PageRank.
- **Cruce obligatorio:** ambos saben responder todo lo de las capas 1 y 2.

### “Muéstrame el código en vivo”
- Repo está en `Smart-Kitchen-Intelligence/` con `runbook.md` que documenta cada script.
- Scripts clave a tener abiertos en VS Code antes de exponer:
  - `src/graph_construction.py` (12-50 líneas, fácil de mostrar)
  - `src/graph_analytics.py` (PageRank en una línea: `nx.pagerank(G, weight='weight')`)
  - `src/evaluation.py` líneas 188-215 (integración del PageRank como sistema)
  - `data/recommender/evaluation_table.csv` para la tabla final

### “¿Y si solo tengo un producto?”
- Cold start: ese producto se rankea por contenido (similitud TF-IDF). PageRank queda al margen porque necesita una sesión con ≥ 2 productos para tener señal.

### “¿Y si soy un hogar nuevo?”
- Fallback a popularidad + contenido. PageRank aporta marginalmente porque su ranking estático sesga hacia productos universales (cebolla, fresas), que es razonable para un usuario sin historial.

### Inconsistencias a evitar
- **No confundir PageRank con personalización.** PageRank es global, no por hogar.
- **No decir “PageRank es el mejor”.** Es el mejor en Precision/MAP, pero Coverage 26% lo descalifica como sistema autónomo.
- **No decir “el grafo es trivial porque está completo”.** Es completo en topología binaria, pero los pesos varían en un rango de 1,613 a 1,996 — esa es la señal.

---

## 8. Cierre — fórmula del Hito 6 (lo que viene)

```
S_hybrid+ = w_C · Ŝ_content + w_F · Ŝ_CF + w_E · Ŝ_expiry + w_G · Ŝ_PageRank
```

Donde `Ŝ_PageRank` es el vector PageRank normalizado Min-Max y `w_G` se calibra por ablación.

Esto cierra el loop: hemos **probado empíricamente** que la centralidad de red aporta señal predictiva no trivial, y por eso vale la pena integrarla al ensamble.

---

## 9. Artefactos a tener listos para la exposición

| Artefacto | Ubicación |
|---|---|
| Informe LaTeX compilado | `Informes/informe_hito5.pdf` |
| Esta guía de defensa | `Informes/guia_defensa_hito5.md` |
| Grafo exportado | `data/recommender/kitchen_graph.gexf` |
| Métricas PageRank | `data/recommender/graph_metrics.json` |
| Tabla comparativa final | `data/recommender/evaluation_table.csv` |
| Figuras Hito 5 | `reports/figures/hito5/` |
| Reporte ejecutivo | `reports/graph_analytics_report.md` |

---

**Regla de oro (te la copio de tu análisis):** cada decisión = tres frases listas (qué, por qué con dato, alternativas descartadas). Esta guía las tiene todas. Si en un punto no logras dar las tres frases en voz alta, ahí es donde hay que repasar antes de la expo.
