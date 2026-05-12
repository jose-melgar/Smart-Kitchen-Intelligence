# Esquema de Datos y Arquitectura de Características

## 1. Arquitectura de Almacenamiento (Hito 1)
El sistema implementa un **Modelo en Estrella (Star Schema)** desnormalizado para optimizar la carga analítica inicial.

- **Tabla de Hechos (`fact_inventory_events`):** Centraliza el flujo transaccional, métricas temporales y clasificación de negocio (`event_type`, `quantity`, `expiry_date`).
- **Tabla de Dimensiones (`dim_products`):** Almacena atributos estáticos y metadatos nutricionales validados por la USDA (`product_name`, `category`, `nutriscore`).

## 2. Evolución hacia Matriz Densa (Hito 2)
Para el análisis de Big Data y la reducción de dimensionalidad, el esquema evoluciona:

- **Denormalización Activa:** Se realiza un JOIN entre hechos y dimensiones para crear un registro plano.
- **Codificación Densa:** En lugar de expandir el esquema con columnas One-Hot (que fragmentarían el modelo en un espacio disperso), se aplica **CatBoost Encoding**. Esto mantiene el esquema compacto.
- **Proyección Tensorial:** El resultado final es una matriz de 56 dimensiones optimizada para operaciones de álgebra lineal, sirviendo como entrada para el PCA.

## 3. Justificación del Diseño
- **Eficiencia en Agregaciones:** El Star Schema minimiza los JOINS necesarios para reportes de desperdicio.
- **Preparación para Clustering:** La transición a una matriz densa asegura que los algoritmos de agrupamiento de la Semana 7 calculen distancias euclidianas significativas en lugar de operar sobre ceros estructurales (ruido).