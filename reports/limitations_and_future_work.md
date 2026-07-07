# Limitaciones y Trabajo Futuro

> Entregable de Semana 14. Consolida en un solo documento las limitaciones
> metodológicas del sistema completo — algunas son decisiones de diseño
> deliberadas y justificadas (Secciones 1 y 2), otras son deuda técnica
> genuina (Sección 3). Sintetiza menciones que hoy están dispersas en
> `reports/recommendation_experiments.md`, `reports/graph_analytics_report.md`
> y el código fuente.

## 1. Catálogo pequeño (50 productos) e interacciones sintéticas: una decisión ética, no una limitación de escala

SKI opera sobre un catálogo deliberadamente acotado a **50 productos** y una capa de interacción **enteramente sintética** (10 households simulados, 90 días, generados por `src/simulation.py`). Esto no es una limitación de recursos de cómputo — es una decisión metodológica alineada estrictamente con los requisitos de uso ético de datos documentados en `reports/ethics_note.md` y `reports/source_inventory.md`:

1. **Evitar scraping no autorizado.** Una alternativa para "crecer" el catálogo habría sido scrapear catálogos de supermercados reales o APIs de retailers sin autorización explícita, para obtener miles de productos con interacciones de usuarios reales. Se descartó deliberadamente: el proyecto solo consume dos fuentes con permiso explícito de uso — el dataset de Instacart (liberado públicamente para investigación en Kaggle) y la API pública de USDA FoodData Central (datos abiertos del gobierno de EE. UU.) — ambas accedidas mediante protocolos oficiales (`kagglehub`, API REST con API key), sin vulnerar términos de servicio de ninguna plataforma.
2. **Evitar datos de usuarios reales.** Los 50 productos y los patrones de compra por hora provienen de las distribuciones *agregadas* de Instacart (no de transacciones individuales identificables), y toda la capa de interacción household-producto (`data/raw/movements_raw.csv`) es generada por simulación estocástica (`src/simulation.py`), no observada. Esto elimina cualquier riesgo de PII: no existen nombres, direcciones ni identificadores vinculables a personas reales — los UUIDs de `stock_id`/`event_id` son sintéticos por construcción.
3. **Costo de esta decisión, reconocido explícitamente.** Acotar el catálogo a 50 productos con solo 6 categorías distintas (ver `reports/cluster_profiles.md`) limita la granularidad de los perfiles de cluster (algunos clusters son monocategoría casi por definición) y el candidate pool de evaluación es pequeño frente a un catálogo de supermercado real (miles de SKUs). El dataset sostiene la segunda mitad del curso (clustering, recomendación, grafo) por la **complejidad transaccional y de pipeline** que introduce — sesiones, ventanas temporales, ALS, TF-IDF híbrido, grafo de co-ocurrencia — no por el volumen de catálogo.

**Conclusión de esta sección:** el tamaño reducido del catálogo es el precio explícito y aceptado de cumplir con el uso ético de datos (Sección "Ethics and Access Note" del brief), no un descuido de diseño.

## 2. Grafo de co-ocurrencia completamente conectado: la señal está en los pesos, no en la topología

Como se documenta en `reports/graph_analytics_report.md` (Sección 2), el grafo de co-ocurrencia producto-producto resultante de $A = R^T \cdot R$ sobre `R_restock_bin` es un **grafo completo**: 50 nodos, los 1,225 pares posibles ($\binom{50}{2}$) están conectados por al menos una arista, y existe una única componente conexa.

Esto es matemáticamente esperable dado el diseño del simulador: 10 households comparten el mismo catálogo de 50 productos durante 90 días, por lo que casi cualquier par de productos termina co-ocurriendo en alguna sesión de restock. La consecuencia directa es que **la topología binaria del grafo (qué nodos están conectados) no aporta señal discriminativa** — todos los nodos están conectados a todos. El análisis se diseñó, por tanto, para depender exclusivamente de los **pesos de las aristas** (frecuencia de co-ocurrencia) y de las métricas derivadas de esos pesos:

- **Grado ponderado** (no grado simple, que es idéntico = 49 para todo nodo en un grafo completo): identifica productos "puente" por *cuánto* co-ocurren, no por *si* co-ocurren.
- **PageRank ponderado** ($\alpha=0.85$, `weight='weight'`): la centralidad transitiva se calcula sobre los pesos, no sobre la adyacencia binaria — de lo contrario, todo nodo tendría el mismo PageRank por simetría estructural del grafo completo.

Esta elección de diseño ya fue validada empíricamente en dos frentes documentados en `reports/graph_analytics_report.md`:
- Como sistema de ranking aislado, PageRank (ponderado) supera a Popularity en Precision@5 (+6.5%) y MAP@5 (+10.4%) — confirma que el peso de las aristas contiene señal real más allá de la simple frecuencia de aparición de un producto.
- La ablación de integración al recomendador híbrido (Semana 13, `src/recommender_hybrid.py`) encontró un peso óptimo $w_G=0.00$ para PageRank como cuarto componente del ensamble — es decir, la señal de centralidad global no añade valor de re-ranking *a nivel de canasta individual* más allá de lo que Contenido y CF ya capturan (ambos derivan, en última instancia, de la misma matriz $R$). Este es un resultado negativo honesto, no un fallo de implementación: confirma que el valor del grafo es **macro-estructural** (identificar productos puente, auditar la topología de co-compra, servir de baseline de ranking estático) y no de personalización por sesión.

**Trabajo futuro relacionado:** con un catálogo más grande y datos reales de households (Sección 1), el grafo dejaría de ser completo — aparecerían componentes desconectadas o aristas ausentes entre productos que nunca co-ocurren, y en ese escenario la topología binaria (no solo los pesos) volvería a ser una señal potencialmente informativa (p. ej., distancia de camino más corto entre productos, detección de comunidades). Esto queda fuera del alcance actual porque el catálogo de 50 productos, por diseño (Sección 1), no genera esa dispersión estructural.

## 3. Otras limitaciones y deuda técnica

1. **Evaluación offline únicamente.** El protocolo de Masked Basket Completion Task (`src/evaluation.py`) es un proxy de hold-out aleatorio (semilla 42), no una validación con usuarios reales ni un A/B test. Las métricas absolutas (Precision@5 ≈ 0.05) deben leerse de forma comparativa entre sistemas, no como una medida de calidad percibida por un usuario final.
2. **Sin pruebas automatizadas.** No existe una carpeta `tests/` ni smoke tests que verifiquen formas/rangos de los artefactos generados en cada etapa del pipeline. La verificación actual depende de inspección manual de los valores impresos por cada script contra los resultados esperados documentados en `runbook.md`.
3. **Pipeline sin orquestador único.** La reproducción end-to-end requiere ejecutar más de 20 scripts en el orden documentado en `runbook.md`; no existe un `Makefile` o `run_pipeline.py` que encapsule esa secuencia en un solo comando.
4. **Sin configuración externalizada.** Rutas de archivos e hiperparámetros (ventanas de sesión, $\lambda$ de ALS, pesos del híbrido) están hardcodeados dentro de cada script en vez de vivir en un archivo de configuración central. Esto es viable porque todo se ejecuta desde la raíz del repositorio, pero no escala a un segundo dataset o entorno sin editar código.
5. **Equipo de 2 personas.** El brief recomienda equipos de 3 a 5 integrantes; esto no es un incumplimiento (el brief permite roles combinados) pero limitó la profundidad de paralelización posible durante el desarrollo, en particular en la fase de cierre de Semana 14.
6. **Staleness y drift no monitoreados en el pipeline actual.** Como se detalla en `reports/monitoring_plan.md`, hoy no existe un mecanismo de versionado de la fecha de consulta a la API de la USDA ni de detección de drift entre el consumo simulado y las distribuciones base de Instacart. El plan de monitoreo formaliza qué se debería medir si el sistema pasara a producción, pero esa instrumentación no está implementada.
