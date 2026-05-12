# Diccionario de Datos SKI (Hito 1 & 2 - Consolidado)

Este documento describe la estructura de los datos transaccionales (V1) y las variables de la matriz de características (V2).

## 1. Variables Transaccionales (Base Hito 1)
| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `event_id` | STRING | Identificador único universal (UUID) de la transacción. |
| `stock_id` | STRING | ID de lote. Vincula una entrada (`IN`) con su salida (`OUT`). |
| `product_id` | INTEGER | Código identificador basado en el catálogo de Instacart. |
| `event_type` | STRING | Tipo de movimiento: **IN** (Entrada) o **OUT** (Salida). |
| `timestamp` | DATETIME | Fecha y hora exacta del movimiento (`YYYY-MM-DD HH:MM:SS`). |
| `quantity` | INTEGER | Cantidad de unidades involucradas. |
| `classification` | STRING | Etiqueta de negocio: `Purchase`, `Consumption`, `Waste`, `Forced_Waste`. |
| `nutriscore` | STRING | Calificación de salud (A-E) o "Falta Dato". |

## 2. Variables de la Matriz de Características (Hito 2)
Estas variables han sido procesadas mediante **StandardScaler** (Media 0, Varianza 1) para el PCA.

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `calories_100g` | FLOAT | Contenido energético por 100g (Fuente: USDA API). |
| `proteins_100g` | FLOAT | Contenido de proteínas por 100g (Fuente: USDA API). |
| `carbs_100g` | FLOAT | Contenido de carbohidratos por 100g (Fuente: USDA API). |
| `category_encoded`| FLOAT | **CatBoost Encoding:** Representación densa de la categoría. |
| `txt_[keyword]` | FLOAT | **Vectores TF-IDF:** Peso de importancia de términos en el nombre (50 dimensiones). |
| `hour_of_day` | INTEGER | Hora del día extraída del timestamp (0-23). |
| `day_of_week` | INTEGER | Día de la semana extraído del timestamp (0-6). |

## 3. Notas Técnicas
- **Eliminación de Dummies:** Se descartaron las columnas One-Hot del Hito 1 para favorecer la densidad de información.
- **Granularidad:** El dataset mantiene una granularidad transaccional a nivel de ítem individual por hogar.