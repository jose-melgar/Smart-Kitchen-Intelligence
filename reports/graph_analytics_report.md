# Reporte de Analítica de Grafos y Centralidad PageRank (Hito 5)

## 1. Objetivo

El Hito 5 introduce una capa de **analítica de grafos** al proyecto Smart Kitchen Intelligence. La idea es modelar las relaciones de co-ocurrencia entre productos (qué productos se compran juntos en una misma sesión de reabastecimiento) como una **red no dirigida ponderada**, y luego aplicar métricas de teoría de grafos para identificar los productos más "centrales" o influyentes en el ecosistema de la cocina.

## 2. Construcción del Grafo (`graph_construction.py`)

### Método
Se parte de la **matriz binaria de sesiones de restock** $R$ (1,177 sesiones × 50 productos) generada en el Hito 4. La matriz de co-ocurrencia se calcula mediante la multiplicación matricial:

$$A = R^T \cdot R$$

Donde $A_{ij}$ representa cuántas sesiones contienen simultáneamente los productos $i$ y $j$. La diagonal $A_{ii}$ indica en cuántas sesiones aparece cada producto individualmente (se descarta para las aristas).

### Resultado
- **50 nodos** (uno por producto del catálogo)
- **1,225 aristas** (grafo completamente conectado: $\binom{50}{2} = 1225$)
- **1 componente conexa** (todos los productos están interconectados)
- Formato de exportación: GEXF (`data/recommender/kitchen_graph.gexf`)

La conectividad total es esperable dado que el simulador estocástico genera sesiones diversas con 50 productos compartidos entre 10 hogares durante 90 días. Sin embargo, la diferenciación reside en los **pesos** de las aristas: no todos los pares de productos co-ocurren con la misma frecuencia.

## 3. Métricas Estructurales (`graph_analytics.py`)

### 3.1 Grado Ponderado
El grado simple es idéntico para todos los nodos (49, grafo completo), por lo que la métrica relevante es el **grado ponderado**: la suma de los pesos de todas las aristas incidentes a un nodo.

| Métrica | Valor |
|---|---|
| Grado ponderado mínimo | 1,613 |
| Grado ponderado máximo | 1,996 |
| Grado ponderado medio | 1,822.8 |

Los productos con mayor grado ponderado son aquellos que co-ocurren más frecuentemente con el resto del catálogo. Representan los "productos puente" que conectan distintos patrones de consumo.

### 3.2 Centralidad PageRank
Se aplica el algoritmo PageRank ponderado (factor de amortiguación $\alpha = 0.85$, convergencia por defecto de NetworkX). PageRank asigna mayor importancia a los nodos conectados a otros nodos también importantes, capturando una noción de influencia transitiva que el grado ponderado simple no puede expresar.

**Top-10 Productos por PageRank:**

| Rank | Producto | PageRank |
|---|---|---|
| 1 | Yellow Onions (45007) | 0.0216 |
| 2 | Strawberries (16797) | 0.0216 |
| 3 | Organic Avocado (39877) | 0.0215 |
| 4 | Seedless Red Grapes (4920) | 0.0214 |
| 5 | Organic Raspberries (26604) | 0.0214 |
| 6 | Organic Strawberries (27086) | 0.0213 |
| 7 | Organic Baby Spinach (45066) | 0.0210 |
| 8 | 100% Whole Wheat Bread (5077) | 0.0209 |
| 9 | Organic Hass Avocado (47626) | 0.0208 |
| 10 | Sparkling Water (39275) | 0.0207 |

La distribución de PageRank es relativamente uniforme (std = 0.00094), lo que refleja la alta conectividad del grafo. No obstante, los productos en el top tienden a ser productos frescos de alta rotación (frutas, verduras, pan), consistente con la semántica del dominio.

## 4. PageRank como Sistema de Ranking

En la evaluación consolidada (`evaluation.py`), se incorporó PageRank como un **quinto sistema de referencia** evaluado bajo el mismo protocolo de Masked Basket Completion Task (hold-out 20%, seed 42):

| Sistema | Precision@5 | MAP@5 | Coverage@5 |
|---|---|---|---|
| Popularity | 0.0508 | 0.0539 | 22.0% |
| **PageRank** | **0.0541** | **0.0595** | **26.0%** |
| Content (TF-IDF) | 0.0450 | 0.0511 | 84.0% |
| CF (ALS) | 0.0467 | 0.0549 | 100.0% |
| Hybrid | 0.0494 | 0.0574 | 100.0% |

### Hallazgos clave:
1. **PageRank supera a Popularity** en Precision@5 (+6.5%) y MAP@5 (+10.4%), demostrando que la centralidad estructural de la red captura señales de relevancia más ricas que la simple frecuencia de aparición.
2. **Coverage limitada** (26%): como ranking estático (no personalizado), PageRank solo recomienda los mismos ~13 productos a todos los usuarios, similar al sesgo de popularidad.
3. **El Hybrid sigue siendo el sistema de producción óptimo** porque combina la capacidad predictiva del CF con la diversidad completa del catálogo (100% coverage) y la señal anti-desperdicio.

## 5. Integración de PageRank en el Recomendador Híbrido (Semana 13)

Se implementó y ejecutó la extensión planteada anteriormente: un **cuarto componente de PageRank** ($w_G$) en el ensamble lineal del recomendador híbrido, junto a Contenido ($w_C$), CF ($w_F$) y Expiry ($w_E$):

$$\text{score}_{v2}(\text{prod}) = w_C \cdot \text{score}_{content} + w_F \cdot \text{score}_{cf} + w_E \cdot \text{score}_{expiry} + w_G \cdot \text{score}_{pagerank}$$

`src/recommender_hybrid.py` ejecuta un **barrido de ablación sobre el 4-simplex** de pesos ($w_C, w_F, w_E, w_G \geq 0$, suma 1, incrementos de 0.25 → 35 combinaciones) y selecciona la combinación ganadora por precision@5. El resultado del barrido fue:

$$w_C = 0.25,\quad w_F = 0.50,\quad w_E = 0.25,\quad w_G = \mathbf{0.00}$$

Es decir, **el peso óptimo encontrado para PageRank es 0.00**: ninguna combinación con $w_G > 0$ superó a las mezclas de Contenido+CF+Expiry en el barrido. Esta combinación (`hybrid_v2_graph`) se evaluó bajo el mismo protocolo consolidado de Masked Basket Completion Task (`evaluation.py`) junto a los demás sistemas:

| Sistema | Precision@5 | MAP@5 | Coverage@5 |
|---|---|---|---|
| Hybrid (v1, sin grafo) | **0.0494** | **0.0574** | 100.0% |
| Hybrid v2 (con grafo, $w_G=0.00$) | 0.0479 | 0.0560 | 100.0% |

El híbrido v1 (sin grafo) **supera ligeramente** a la variante v2 tanto en Precision@5 (-3.0% relativo) como en MAP@5 (-2.4% relativo). Dado que $w_G=0.00$ ya en la fase de ablación, la variante v2 evaluada es funcionalmente un híbrido de 3 términos con una redistribución distinta de pesos ($w_C, w_F, w_E$) frente al v1 de producción — y esa redistribución, no el grafo, es lo que explica la pequeña caída de desempeño.

### Interpretación: resultado negativo honesto, no una falla de implementación

Este es un **resultado negativo válido y esperable**, no un error del pipeline: la señal de PageRank es **global y estática por producto** (idéntica para todas las sesiones), mientras que CF y Contenido ya capturan señal **específica de sesión/household**. En una tarea de *cross-selling* intra-canasta como el Masked Basket Completion Task, lo que decide el acierto es precisamente esa especificidad — qué le falta a *esta* canasta — algo que un score de centralidad de red, por diseño, no puede aportar más allá de lo que la co-ocurrencia agregada ya le enseñó al CF (ambos derivan, en última instancia, de la misma matriz $R$).

Esto es coherente con lo observado en la Sección 4: PageRank como sistema aislado ya superaba a Popularity (otro ranking estático) pero no al híbrido, y su cobertura limitada (26%) confirma que es una señal de "productos universalmente centrales", no de afinidad household-específica.

**Conclusión de producción:** el grafo de co-ocurrencia y su métrica de PageRank **aportan valor real, pero a nivel macro/estructural** — identificar productos "puente" que conectan clústeres de consumo dispares (Sección 3.1), auditar la topología de la red de co-compra, y servir como baseline de ranking estático competitivo frente a la popularidad — **no como señal de re-ranking a nivel de canasta individual**. El sistema de producción para recomendación se mantiene en el **híbrido v1** (Contenido + CF + Expiry, $w_C=0.35, w_F=0.45, w_E=0.20$). La integración de grafo queda documentada como extensión evaluada y descartada por evidencia empírica, no como trabajo pendiente.
