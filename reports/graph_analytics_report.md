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

## 5. Conclusiones y Trabajo Futuro

La capa de grafos valida que la estructura topológica de co-compra contiene información predictiva no trivial. El paso natural (planificado para el Hito 6) es **integrar el score de PageRank como un cuarto componente del recomendador híbrido**, ponderándolo en el ensamble lineal para mejorar el re-ranking de producción sin sacrificar la cobertura del catálogo.
