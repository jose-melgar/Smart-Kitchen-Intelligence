# Análisis de Escala y Escalabilidad Evolutiva (Hitos 1, 2 y 3)

## 1. Evolución de las Dimensiones del Dataset
El sistema ha sido diseñado para escalar desde una prueba de concepto hasta un entorno de Big Data masivo:
- **Hito 1 (Prototipo V1):** Simulación inicial de 30 días con ~1,500 a 3,000 registros de interacción.
- **Hito 2 (Escalabilidad V2):** Incremento a 25,444 registros transaccionales (90 días de historial para 10 hogares).
- **Hito 3 (Segmentación V3):** Generación de 38 clusters de comportamiento sobre la matriz de 30 componentes ortogonales.
- **Catálogo Maestro:** 50 productos únicos validados mediante la **USDA FoodData Central API**, asegurando una base nutricional con integridad científica.

## 2. Calidad y Gestión de Datos (Data Quality)
- **Explicit Missingness:** Se detectaron nulos en variables de la USDA. Siguiendo el protocolo de "Transparencia de Datos" del Hito 1, no se inyectaron valores sintéticos en la ingesta.
- **Imputación Estadística (Hito 2):** En la fase de preprocesamiento, los nulos se gestionaron mediante imputación por promedio de categoría, garantizando que el pipeline de clustering no pierda registros críticos.
- **Integridad de Lote:** El 100% de los registros de desperdicio (`Waste`) mantienen integridad referencial con su `stock_id` original, permitiendo un análisis preciso del ciclo de vida del producto.

## 3. Estrategia de Ingeniería de Características (De Disperso a Denso)
Para mitigar la **Maldición de la Dimensionalidad** (Semana 3):
- **Problema Inicial:** El uso de One-Hot Encoding (OHE) planteado en el Hito 1 generaba una matriz excesivamente dispersa (*sparse*) al escalar el catálogo.
- **Solución Implementada:** Se sustituyó el OHE por **CatBoost Encoding** (Target Encoding). Esto redujo la dimensionalidad categórica a una sola columna densa basada en la probabilidad de consumo, eliminando el ruido estructural antes del PCA.

## 4. Análisis de Escalabilidad y Stack de Big Data
- **Optimización con Polars:** El pipeline utiliza **Polars** para JOINS y transformaciones masivas. Su motor basado en Apache Arrow y multithreading permite procesar los 25k registros en milisegundos, superando las limitaciones de memoria de Pandas.
- **Cuellos de Botella Teóricos ($10^7$ eventos):**
    - **Almacenamiento:** El formato CSV se proyecta sustituir por **Parquet** para obtener compresión columnar (~80% de reducción).
    - **Latencia de API:** Se implementará procesamiento por lotes (*Batch Processing*) para las consultas a la USDA.
- **Complejidad Algorítmica (Big O):**
    - **Ingesta y Join:** $O(n/p)$ (donde $p$ es el número de hilos).
    - **Reducción (PCA):** $O(min(p^3, n \cdot p^2))$ con $p=56$ características.
    - **Clustering (DBSCAN):** $O(n \log n)$, eficiente para grandes volúmenes gracias a la reducción previa de dimensiones.