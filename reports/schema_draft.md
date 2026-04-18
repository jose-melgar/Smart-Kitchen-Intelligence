# Esquema de Datos Final (Star Schema)

## Tabla de Hechos (Fact Table)
**`fact_inventory_events`**: Contiene los 1,000 registros de movimientos.
- **PK:** `event_id`
- **FK:** `product_id` (hacia el catálogo)

## Tabla de Dimensiones (Dimension Table)
**`dim_products`**: Catálogo de 50 productos con metadatos.
- **PK:** `product_id`

## Relación
Relación **1:N** (Uno a Muchos). Un producto del catálogo puede aparecer en múltiples eventos de inventario. El dataset `inventory_v1.csv` representa la desnormalización de este esquema para facilitar el análisis exploratorio.