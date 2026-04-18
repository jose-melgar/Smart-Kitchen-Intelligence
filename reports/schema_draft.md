# Esquema de Datos Verificado (Star Schema)

## Arquitectura del Modelo
El sistema implementa un **Modelo en Estrella (Star Schema)** desnormalizado para optimizar la carga analítica y la preparación de características (feature engineering).

### Tabla de Hechos (Fact Table)
**`fact_inventory_events`**: Centraliza el flujo transaccional de la cocina.
- **PK:** `event_id` (Identificador único de evento).
- **FK:** `product_id` (Llave foránea vinculada al catálogo).
- **Métricas:** `timestamp`, `action_type`, `location`, `expiry_date`.

### Tabla de Dimensiones (Dimension Table)
**`dim_products`**: Almacena atributos estáticos y metadatos de salud.
- **PK:** `product_id`
- **Atributos:** `product_name`, `category`, `nutriscore`, `calories_100g`, `proteins_100g`, `carbs_100g`.

## Justificación y Alternativas del Esquema

### ¿Por qué Star Schema sobre otras arquitecturas?
1. **Eficiencia en Agregaciones:** A diferencia de un esquema relacional normalizado (3NF), la estrella minimiza el número de JOINS necesarios para calcular métricas nutricionales acumuladas por ubicación o periodos de tiempo, reduciendo la latencia en consultas de analítica descriptiva.
2. **Flexibilidad para Recomendación (Semana 10):** El mantenimiento de la dimensión `dim_products` aislada permite alimentar modelos de filtrado colaborativo y factorización de matrices de manera eficiente, manteniendo la integridad referencial sin redundancia de metadatos pesados en los logs de eventos.
3. **Proyección de Grafos (Semana 12):** Se ha determinado que este esquema es el más apto para actuar como "fuente de verdad" antes de proyectar los datos hacia una base de grafos nativa. Construir un grafo de co-ocurrencia a partir de una tabla de hechos limpia es computacionalmente más barato que realizar una ingesta directa sobre una estructura de grafos no validada.

### Comparativa con Alternativas
- **Vs. Documental (NoSQL):** Un modelo NoSQL (estilo MongoDB) facilitaría la ingesta, pero penalizaría la consistencia de los datos nutricionales. Si la API actualiza el Nutriscore de un producto, en un modelo documental habría que actualizar miles de documentos; en nuestro Star Schema, solo se actualiza una fila en `dim_products`.