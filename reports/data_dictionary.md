# Diccionario de Datos

| Tabla | Columna | Tipo | Descripción |
| :--- | :--- | :--- | :--- |
| dim_products | `product_id` | STRING | ID único del producto (UPC/EAN). |
| dim_products | `nutriscore_grade` | CHAR | Calificación nutricional de la A a la E. |
| fact_inventory_events | `action_type` | CATEGORIC | 'IN' para entrada de producto, 'OUT' para salida/consumo. |
| fact_inventory_events | `location` | STRING | Ubicación física donde se registró el evento. |
| fact_inventory_events | `expiry_date` | DATE | Fecha de vencimiento registrada al ingresar el producto. |