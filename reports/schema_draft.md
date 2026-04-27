# Esquema de Datos Verificado (Star Schema)

## Arquitectura del Modelo
El sistema implementa un **Modelo en Estrella (Star Schema)** desnormalizado para optimizar la carga analítica y la preparación de características (feature engineering). Esta estructura permite separar los eventos transaccionales de los metadatos nutricionales.

### Tabla de Hechos (Fact Table)
**`fact_inventory_events`**: Centraliza el flujo transaccional y el ciclo de vida de los productos en la cocina.
- **PK:** `event_id` (UUID de transacción).
- **FK:** `product_id` (Vínculo con la dimensión de productos).
- **Atributos de Lote:** `stock_id` (Identificador único de la instancia física/lote).
- **Métricas Temporales:** `timestamp` (Precisión de segundos), `expiry_date` (Fecha de vencimiento).
- **Dimensiones de Negocio:** `event_type` (IN/OUT), `quantity` (Depleción granular), `classification` (Purchase, Consumption, Waste, Forced_Waste).

### Tabla de Dimensiones (Dimension Table)
**`dim_products`**: Almacena atributos estáticos y metadatos de salud validados por la USDA.
- **PK:** `product_id` (Referencia Instacart).
- **Atributos:** `product_name`, `category` (Department ID), `nutriscore` (Calculado), `calories_100g`, `proteins_100g`, `carbs_100g`.

## Justificación y Alternativas del Esquema

### ¿Por qué Star Schema?
1. **Eficiencia en Agregaciones:** Minimiza los JOINS necesarios para calcular métricas como el "Desperdicio por Categoría" o "Consumo Proteico Semanal".
2. **Trazabilidad por stock_id:** La inclusión del `stock_id` en la tabla de hechos permite diferenciar instancias del mismo `product_id`, resolviendo el problema de mezclar productos antiguos con nuevos.
3. **Proyección de Grafos (Hito 2):** Este esquema facilita la creación de un grafo de co-ocurrencia. Los `product_id` actúan como nodos y los `event_id` compartidos (mismo timestamp de compra) definen las aristas.

### Comparativa con Alternativas
- **Vs. Modelo Documental:** Evita la redundancia de datos nutricionales pesados. Una actualización en los valores de la USDA solo requiere modificar una fila en `dim_products`, manteniendo la integridad en millones de eventos históricos.