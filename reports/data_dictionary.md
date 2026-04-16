# Diccionario de Datos (Actualizado V1)

## Tabla: `catalog_raw.csv`
| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `product_id` | STRING | Código EAN-13 o ID único del producto. |
| `product_name` | STRING | Nombre comercial del producto. |
| `category` | STRING | Categoría principal (ej. Snacks, Beverages). |
| `nutriscore` | CHAR | Grado nutricional (A-E). |
| `calories_100g` | FLOAT | Contenido energético en kcal por cada 100g. |
| `proteins_100g` | FLOAT | Proteínas en gramos por cada 100g. |
| `carbs_100g` | FLOAT | Carbohidratos en gramos por cada 100g. |

## Tabla: `movements_raw.csv`
| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `event_id` | STRING | Identificador único del evento (EVT_XXXXX). |
| `product_id` | STRING | FK que conecta con el catálogo. |
| `timestamp` | DATETIME| Fecha y hora exacta del movimiento. |
| `action_type` | STRING | 'IN' (entrada a la cocina) o 'OUT' (salida/consumo). |
| `location` | STRING | Ubicación (Refrigerador, Estantería, Despensa, Caja). |
| `expiry_date` | DATE | Fecha de vencimiento (solo presente en acciones 'IN'). |