# Diccionario de Datos SKI (Consolidado Hito 1, 2 y 3)

Este documento describe la estructura completa del dataset `inventory_v1.csv` y los artefactos de características generados.

## 1. Variables Transaccionales (Base Hito 1)
| Variable | Tipo | Descripción | Formato / Ejemplo |
| :--- | :--- | :--- | :--- |
| `event_id` | STRING | Identificador único universal del log de evento. | UUID |
| `stock_id` | STRING | ID de lote. Vincula una entrada con sus salidas. | UUID |
| `product_id` | INTEGER | Código identificador basado en Instacart. | 24852 |
| `event_type` | STRING | Tipo de movimiento: **IN** o **OUT**. | Categórico |
| `timestamp` | DATETIME | Fecha y hora exacta del movimiento. | YYYY-MM-DD HH:MM:SS |
| `quantity` | INTEGER | Cantidad de unidades involucradas. | 1, 4 |
| `expiry_date` | DATE | Fecha de caducidad calculada (FoodKeeper). | YYYY-MM-DD |
| `classification`| STRING | Etiqueta de negocio: `Purchase`, `Consumption`, `Waste`. | Categórico |
| `nutriscore` | STRING | Calificación de salud (A-E) o "Falta Dato". | A, B, C... |

## 2. Variables Nutricionales y de Características (Hito 2)
Procesadas mediante **StandardScaler** para la normalización estadística.

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `calories_100g` | FLOAT | Contenido energético (Fuente: USDA API). |
| `proteins_100g` | FLOAT | Contenido de proteínas (Fuente: USDA API). |
| `carbs_100g` | FLOAT | Contenido de carbohidratos (Fuente: USDA API). |
| `category_encoded`| FLOAT | **CatBoost Encoding:** Valor denso de la categoría. |
| `txt_[keyword]` | FLOAT | **TF-IDF:** Importancia de términos (50 dimensiones). |
| `hour_of_day` | INTEGER | Hora extraída del timestamp (0-23). |
| `day_of_week` | INTEGER | Día de la semana extraído (0-6). |

## 3. Variables de Segmentación (Hito 3)
| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `cluster_label` | INTEGER | Etiqueta del perfil de comportamiento asignada por **DBSCAN Refinado**. |

## 4. Notas de Calidad
1. **Integridad de Lote:** El `stock_id` es crítico para rastrear qué porcentaje de un lote específico terminó en desperdicio.
2. **Escalado:** Todas las variables en la fase de características tienen media 0 y varianza 1 para no sesgar el cálculo de distancias en el clustering.