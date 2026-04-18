# Diccionario de Datos SKI (V1)

| Variable | Tipo | Descripción | Unidad/Formato |
| :--- | :--- | :--- | :--- |
| `event_id` | STRING | ID único del evento. | EVT_XXXXX |
| `product_id` | STRING | Código EAN-13 del producto (FK). | Numérico |
| `timestamp` | DATETIME | Fecha y hora del movimiento. | ISO 8601 |
| `action_type` | STRING | Tipo de movimiento: IN o OUT. | Categórico |
| `location` | STRING | Ubicación física (Refrigerador, etc.). | Categórico |
| `expiry_date` | DATE | Fecha de vencimiento (solo en IN). | YYYY-MM-DD |
| `product_name` | STRING | Nombre comercial del producto. | Texto |
| `category` | STRING | Categoría de alimentos. | Texto |
| `nutriscore` | CHAR | Calificación de salud (A a E). | Categórico |
| `calories_100g` | FLOAT | Energía por 100g. | kcal |
| `proteins_100g` | FLOAT | Proteínas por 100g. | gramos |
| `carbs_100g` | FLOAT | Carbohidratos por 100g. | gramos |