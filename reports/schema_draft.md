# Esquema de Datos y Arquitectura de Inteligencia

## 1. Arquitectura de Almacenamiento (Hito 1)
El sistema implementa un **Modelo en Estrella (Star Schema)** desnormalizado para optimizar la carga analítica y la preparación de características.

### Tabla de Hechos (`fact_inventory_events`)
Centraliza el flujo transaccional y el ciclo de vida del producto.
- **PK/FK:** `event_id`, `product_id`, `stock_id`.
- **Métricas:** `quantity`, `timestamp`, `expiry_date`.
- **Dimensiones:** `event_type`, `classification`.

### Tabla de Dimensiones (`dim_products`)
Almacena metadatos de salud validados por la USDA.
- **Atributos:** `product_name`, `category`, `nutriscore`, `calories_100g`, `proteins_100g`, `carbs_100g`.

## 2. Capa de Transformación y Proyección (Hito 2)
Evolución hacia una **Matriz Tensorial Densa** para análisis avanzado:
- **Denormalización Activa:** JOIN entre hechos y dimensiones para crear registros planos multimodales.
- **Codificación Densa:** Implementación de **CatBoost Encoding** para mantener el esquema compacto y evitar la fragmentación de columnas OHE.
- **Reducción de Dimensionalidad:** Proyección de 56 dimensiones a 30 componentes mediante **PCA**, reteniendo el 90% de la energía del sistema.

## 3. Capa de Segmentación de Comportamiento (Hito 3)
Inclusión del **Segmented Dataset**:
- Los datos reducidos alimentan el modelo **DBSCAN Refinado**. El esquema final incorpora el atributo `cluster_label`, permitiendo que el sistema de recomendaciones consulte grupos de productos con patrones de consumo similares en lugar de items aislados.

## 4. Justificación y Alternativas
- **Vs. Modelo Documental:** El Star Schema evita la redundancia masiva y facilita las agregaciones temporales de Big Data.
- **Trazabilidad:** La inclusión del `stock_id` resuelve el problema de mezclar productos antiguos con nuevos ingresos, una limitación común en inventarios planos.
- **Preparación para Clustering:** La matriz densa asegura que el cálculo de distancias euclidianas sea significativo, eliminando el ruido de los ceros estructurales de las matrices dispersas.