# Diccionario de Datos SKI (Inventory V1)

Este documento describe la estructura, tipos de datos y restricciones de los campos presentes en el dataset procesado `inventory_v1.csv`, el cual consolida la información transaccional de la cocina con la metadata nutricional de la USDA.

| Variable | Tipo | Descripción | Formato / Ejemplo |
| :--- | :--- | :--- | :--- |
| `event_id` | STRING | Identificador único universal del log de evento. | UUID (e.g., `638b36b2-6`) |
| `stock_id` | STRING | ID de lote/instancia. Vincula una entrada con sus salidas específicas. | UUID (e.g., `806bd70b`) |
| `product_id` | INTEGER | Código identificador del producto basado en el catálogo de Instacart. | Numérico (e.g., `24852`) |
| `event_type` | STRING | Tipo de movimiento de inventario: **IN** (Entrada) o **OUT** (Salida). | Categórico |
| `timestamp` | DATETIME | Fecha y hora exacta en la que ocurrió el movimiento. | `YYYY-MM-DD HH:MM:SS` |
| `quantity` | INTEGER | Cantidad de unidades (o peso) involucradas en la acción específica. | Numérico (e.g., `1`, `4`) |
| `expiry_date` | DATE | Fecha de caducidad del producto calculada según reglas de FoodKeeper. | `YYYY-MM-DD` |
| `classification` | STRING | Etiqueta lógica de negocio: `Purchase`, `Consumption`, `Waste`, `Forced_Waste`. | Categórico |
| `product_name` | STRING | Nombre comercial del producto recuperado del Master Data. | Texto (e.g., `Organic Garlic`) |
| `category` | INTEGER | ID del departamento/categoría original de Instacart. | Numérico (e.g., `4` para Produce) |
| `nutriscore` | STRING | Calificación de salud calculada u obtenida. | `A`, `B`, `C`, `D`, `E` o `Falta Dato` |
| `calories_100g` | FLOAT | Contenido energético por cada 100g (Fuente: USDA API). | kcal (e.g., `33.3`) |
| `proteins_100g` | FLOAT | Contenido de proteínas por cada 100g (Fuente: USDA API). | gramos (e.g., `2.35`) |
| `carbs_100g` | FLOAT | Contenido de carbohidratos por cada 100g (Fuente: USDA API). | gramos (e.g., `12.1`) |

## Notas Técnicas sobre la Calidad
1. **Integridad de Lote (`stock_id`):** Esta variable es crítica para el análisis de desperdicio, ya que permite rastrear cuántas unidades de un ingreso específico (`IN`) terminaron en consumo y cuántas en desperdicio (`OUT`).
2. **Manejo de Nulos:** Las variables nutricionales pueden presentar valores nulos (`NaN`) en casos donde la API de la USDA no proporcionó referencia. Estos campos están marcados para una fase de imputación estadística en el Hito 2.
3. **Clasificación Automática:** La variable `classification` se genera mediante una función de comparación temporal entre el `timestamp` del evento y la `expiry_date`.