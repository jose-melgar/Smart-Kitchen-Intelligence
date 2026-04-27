# Análisis de Escala y Escalabilidad (Dataset V1)

## Dimensiones Verificadas (Prototipo)
- **Eventos:** ~1,500 - 3,000 registros de interacción (Simulación de 30 días).
- **Catálogo:** 50 productos únicos alineados con la **USDA FoodData Central API**.
- **Atributos:** 10-12 columnas unificadas en el Dataset V1.

## Calidad y Completitud (Data Quality)
- **Explicit Missingness:** Se identifica un porcentaje de nulos en variables nutricionales provenientes de la USDA. Siguiendo el protocolo de "Transparencia de Datos", estos no se rellenan con valores al azar en la ingesta, permitiendo una **Imputación de Datos** estadística (por promedio de categoría) en la fase de preprocesamiento.
- **Lógica de Desperdicio:** El 100% de los registros `Waste` y `Forced_Waste` cuentan con integridad referencial respecto a su `stock_id` original, permitiendo un análisis preciso de la eficiencia de consumo.

## Análisis de Escalabilidad y Cuellos de Botella

### Optimización con Polars
Para mitigar las limitaciones de Pandas, el pipeline se ha proyectado para utilizar **Polars**:
1. **Multithreading:** Polars utiliza todas las unidades de ejecución (cores) disponibles, permitiendo que el *Join* entre eventos y catálogo sea hasta 10-20 veces más rápido que en Pandas.
2. **Lazy Evaluation:** El uso de `LazyFrame` permite optimizar las consultas antes de ejecutarlas, filtrando datos innecesarios antes de cargarlos en memoria.
3. **Gestión de Memoria:** Polars utiliza Apache Arrow, lo que reduce drásticamente el consumo de RAM al procesar grandes volúmenes de eventos ($10^6+$).



### Cuellos de Botella Teóricos a Gran Escala
Al incrementar el volumen a $10^7$ eventos (10 millones):
- **Limitación de Almacenamiento:** El formato CSV resulta ineficiente. Se implementará el uso de **Parquet**, que ofrece compresión columnar y reduce el tamaño de almacenamiento en un ~80%.
- **Latencia de API:** La consulta individual a la USDA se vuelve inviable. La solución es el procesamiento por lotes (*Batch Processing*) o la descarga de snapshots estáticos de la base de datos de la USDA para cruces locales en memoria.

### Complejidad Algorítmica (Big O)
- **Cruce de Datos (Polars Join):** $O(n/p)$, donde $n$ es el número de eventos y $p$ el número de hilos de ejecución.
- **Ingeniería de Características:** $O(n)$ gracias a las operaciones vectorizadas nativas de Polars.