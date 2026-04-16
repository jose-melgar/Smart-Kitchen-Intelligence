# Inventario de Fuentes de Datos

## Fuente 1: OpenFoodFacts (Catálogo)
- **URL:** [https://world.openfoodfacts.org/data](https://world.openfoodfacts.org/data)
- **Tipo:** API Pública / Dataset Abierto.
- **Licencia:** Open Database License (ODbL).
- **Formato:** JSON / CSV.
- **Uso:** Capa de catálogo de productos (información nutricional y categorías).

## Fuente 2: Logs de Interacción (Simulados)
- **Origen:** Generación interna mediante scripts de Python (`src/ingestion.py`).
- **Tipo:** Datos sintéticos de comportamiento de usuario.
- **Formato:** Parquet / CSV.
- **Uso:** Capa de interacción (entradas y salidas de la estantería/refrigerador).