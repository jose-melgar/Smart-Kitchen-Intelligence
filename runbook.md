# Guía de Ejecución y Reproducibilidad (Runbook) - SKI Project

Este documento detalla los pasos necesarios para reproducir el pipeline de datos completo del proyecto, desde la ingesta de datos crudos hasta la generación de la matriz de características y el análisis de dimensionalidad (Entregas Semanas 3 y 5).

## 1. Configuración del Entorno

### 1.1. Dependencias del Sistema
El pipeline requiere Python 3.9+ y las dependencias listadas en `requirements.txt`.

```bash
# Crear y activar un entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar las dependencias de Python
pip install -r requirements.txt
```

### 1.2. Configuración de Credenciales (Obligatorio)

El pipeline utiliza dos APIs que requieren autenticación:

1.  **Kaggle API:** Para descargar el dataset de Instacart. Asegúrate de tener tu archivo `kaggle.json` en `~/.kaggle/kaggle.json`. Consulta la [guía de Kaggle](https://www.kaggle.com/docs/api) para obtener tus credenciales.

2.  **USDA FoodData Central API:** Para enriquecer los datos con información nutricional.
    *   Crea un archivo llamado `.env` en la raíz del proyecto.
    *   Añade tu clave de API de la USDA (puedes obtener una [aquí](https://fdc.nal.usda.gov/api-key.html)) dentro del archivo de la siguiente manera:

    ```.env
    USDA_API_KEY="TU_CLAVE_API_AQUI"
    ```

## 2. Ejecución Completa del Pipeline de Datos

El pipeline se ejecuta en una secuencia de scripts. Cada uno genera artefactos que son consumidos por el siguiente. Ejecútalos en el orden indicado.

### Paso 1: Extracción de Patrones de Comportamiento
Este script descarga un dataset público de Instacart para extraer patrones realistas de compra (distribución por horas, productos más comunes).

```bash
python src/extract_patterns.py
```
*   **Entrada:** Dataset `yasserh/instacart-online-grocery-basket-analysis-dataset` de Kaggle.
*   **Salida:** `data/raw/instacart_patterns.json`

### Paso 2: Simulación Masiva de Movimientos
Usando los patrones extraídos, este script simula el comportamiento de múltiples hogares durante 90 días para generar un volumen de datos transaccionales significativo.

```bash
python src/simulation.py
```
*   **Entrada:** `data/raw/instacart_patterns.json`
*   **Salida:** `data/raw/movements_raw.csv`

### Paso 3: Enriquecimiento del Catálogo con Datos Nutricionales
Este script toma los productos de la simulación y consulta la API de USDA para obtener datos nutricionales reales, construyendo el catálogo de productos.

```bash
python src/ingestion.py
```
*   **Entradas:** `data/raw/movements_raw.csv`, API de USDA.
*   **Salida:** `data/raw/catalog_raw.csv`

### Paso 4: Preprocesamiento y Consolidación
Unifica los movimientos simulados con la información del catálogo en un único dataset limpio y listo para el análisis. Utiliza Polars para un alto rendimiento.

```bash
python src/preprocessing.py
```
*   **Entradas:** `data/raw/movements_raw.csv`, `data/raw/catalog_raw.csv`.
*   **Salida:** `data/processed/inventory_v1.csv`

## 3. Generación de Artefactos para Machine Learning (Semana 5)

Una vez que el dataset procesado está listo, se pueden ejecutar los scripts de análisis.

### Paso 5: Ingeniería de Características (Feature Engineering)
Convierte el dataset tabular en una matriz numérica de características lista para ser usada por algoritmos de Machine Learning.

```bash
python src/features.py
```
*   **Entrada:** `data/processed/inventory_v1.csv`
*   **Salidas:** `data/features/feature_matrix.npy`, `data/features/feature_names.json`

### Paso 6: Análisis de Reducción de Dimensionalidad
Ejecuta PCA sobre la matriz de características para analizar su estructura latente y generar un reporte visual.

```bash
python src/reduction.py
```
*   **Entradas:** `data/features/feature_matrix.npy`, `data/processed/inventory_v1.csv`.
*   **Salidas:** Gráficos `pca_scree_plot.png` y `pca_scatter_2d.png` en `reports/figures/`, y un resumen en la consola.