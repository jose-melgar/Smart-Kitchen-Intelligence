# Borrador del Esquema de Datos

## Tabla: `dim_products` (Catálogo)
- **PK:** `product_id` (Código de barras/ID único).
- **Atributos:** `product_name`, `category`, `nutriscore`, `calories_100g`, `proteins_100g`, `carbs_100g`.

## Tabla: `fact_inventory_events` (Interacciones)
- **PK:** `event_id`.
- **FK:** `product_id` (Relación con catálogo).
- **Atributos:** `timestamp`, `action_type` (IN/OUT), `location` (Fridge/Shelf/Box), `expiry_date_observed`.

## Uniones (Joins) Esperadas
El análisis principal se basará en el JOIN de `fact_inventory_events` con `dim_products` a través de `product_id` para enriquecer los movimientos de inventario con información nutricional.