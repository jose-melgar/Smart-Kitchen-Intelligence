# Análisis de Escala y Escalabilidad (Dataset V1)

## Dimensiones Verificadas
- **Eventos:** 1,000 registros de interacción.
- **Catálogo:** 50 productos reales (API OpenFoodFacts).
- **Variables Totales:** 12 columnas (unificadas tras el procesamiento).

## Calidad y Completitud (Data Quality)
- **Missingness by Design:** Se identifica un 58% de nulos en `expiry_date`. Tras el análisis técnico, se confirma que esto no representa una pérdida de calidad, sino que corresponde lógicamente a las acciones de tipo 'OUT' (consumo), donde el registro de vencimiento es irrelevante para el estado del inventario.
- **Sparsity:** La densidad es de 20 eventos por producto. Esta dispersión inicial es óptima para validar la robustez de los algoritmos de recomendación híbrida frente al problema de "cold start".

## Análisis de Escalabilidad y Cuellos de Botella

### Complejidad Algorítmica (Big O)
El pipeline de procesamiento actual (`src/preprocessing.py`) se basa en dos operaciones críticas:
1. **Conversión Temporal (`to_datetime`):** $O(n)$, donde $n$ es el número de eventos.
2. **Operación de Unión (`pd.merge`):** Se utiliza un *hash join* con una complejidad promedio de $O(n + m)$ en tiempo y espacio (donde $n$ = eventos y $m$ = catálogo).

### Cuellos de Botella Teóricos a Gran Escala
Al incrementar el volumen a $10^7$ eventos (10 millones):
- **Limitación de RAM:** El uso de Pandas obligará a cargar ambos DataFrames en memoria. Con un ancho de 12 columnas y tipos de datos actuales, el proceso podría colapsar al exceder los 10-16GB de RAM disponibles en máquinas estándar.
- **Latencia de I/O:** La escritura en formato CSV se volverá ineficiente. 
- **Solución Roadmap:** Para mitigar estos cuellos de botella, se planea la migración hacia **Parquet** (almacenamiento columnar) y el uso de **PySpark** para distribuir el *merge* en un cluster, transformando la complejidad de memoria de $O(n)$ local a una gestión distribuida por particiones.