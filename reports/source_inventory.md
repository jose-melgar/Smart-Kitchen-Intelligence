# Inventario de Fuentes de Datos

## Fuente 1: OpenFoodFacts (Catálogo)
- **URL:** [https://world.openfoodfacts.org/data](https://world.openfoodfacts.org/data)
- **Uso:** Capa de catálogo de productos (información nutricional y categorías).

## Fuente 2: Logs de Interacción (Simulados)
- **Origen:** Generación interna mediante `src/simulation.py`.
- **Uso:** Capa de interacción (entradas y salidas).

## Estrategia de Resiliencia y Contingencia
Dada la naturaleza crítica de la disponibilidad de datos en sistemas de Big Data, se ha implementado un mecanismo de **Fallback (Respaldo)** en el script de ingesta (`src/ingestion.py`). 
- **Escenario:** En caso de que la API de OpenFoodFacts no responda (errores 5xx) o presente latencia excesiva, el sistema activa automáticamente la generación de un "Catálogo de Emergencia" (Mock Data).
- **Objetivo:** Garantizar la continuidad del pipeline de procesamiento y permitir que las capas de recomendación y grafos funcionen incluso ante inestabilidades del servidor externo.