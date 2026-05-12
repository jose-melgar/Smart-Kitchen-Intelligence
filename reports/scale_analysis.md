# Análisis de Escala y Escalabilidad (Milestone 1 & 2)

## 1. Evolución de las Dimensiones del Dataset
- **Hito 1 (Prototipo V1):** ~1,500 - 3,000 registros transaccionales (Simulación inicial de 30 días).
- **Hito 2 (Escalabilidad V2):** 25,444 registros transaccionales (Simulación robusta de 90 días, 10 hogares).
- **Catálogo:** 50 productos únicos validados mediante la **USDA FoodData Central API**.
- **Matriz Resultante:** 56 columnas densas tras el procesamiento multimodal.

## 2. Calidad y Completitud (Data Quality)
- **Manejo de Nulos:** Siguiendo el protocolo de "Transparencia de Datos" del Hito 1, los nulos nutricionales no se inyectan sintéticamente en la ingesta. En el Hito 2, se aplica una **Imputación Estadística** basada en el promedio de la categoría antes del PCA para asegurar la integridad de la matriz.
- **Lógica de Desperdicio:** Se mantiene la integridad referencial mediante el `stock_id`, permitiendo rastrear el 100% de los registros de `Waste` y `Forced_Waste` desde su ingreso.

## 3. Transición Técnica: De One-Hot a CatBoost Encoding
Para cumplir con los estándares de Big Data y mitigar la **Maldición de la Dimensionalidad** identificada en la Semana 3, se realizó el siguiente cambio:
- **Hito 1 (Planteamiento):** Se propuso One-Hot Encoding (OHE) para departamentos.
- **Hito 2 (Implementación):** Se sustituyó el OHE por **CatBoost Encoding** (Target Encoding). Esto evita matrices dispersas (*sparse*) con excesivos ceros y genera una representación densa basada en la probabilidad de movimiento del inventario, enriqueciendo la capacidad discriminatoria del modelo.

## 4. Análisis de Escalabilidad (Big Data Stack)
- **Optimización con Polars:** El pipeline utiliza Polars para aprovechar el multithreading y la evaluación perezosa (*Lazy Evaluation*). El uso de Apache Arrow reduce drásticamente el consumo de RAM en comparación con Pandas.
- **Complejidad Algorítmica (Big O):**
    - **Cruce de Datos (Polars Join):** $O(n/p)$, donde $n$ es el número de eventos y $p$ el número de hilos.
    - **PCA:** $O(min(p^3, n \cdot p^2))$ donde $p$ es el número de características (56). Al mantener una matriz densa, el proceso es altamente eficiente para 25k+ registros.
- **Persistencia:** Se proyecta el uso de **Parquet** para volúmenes superiores a $10^7$ eventos para optimizar el almacenamiento columnar.