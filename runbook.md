# Guía de Ejecución y Reproducibilidad (Runbook) - SKI Project

Este documento detalla los pasos necesarios para reproducir el pipeline de datos de la Fase 1 (Semana 3) del proyecto **Smart Kitchen Intelligence**.

## 1. Configuración del Entorno
Se recomienda el uso de un entorno virtual para evitar conflictos de dependencias.

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 2. Generación de Catálogo de Productos (API)
El primer paso es obtener el catálogo de productos. El script `src/ingestion.py` se conecta a la API de Open Food Facts para descargar datos de productos. Si la API falla, genera un conjunto de datos de respaldo.

Para ejecutar la ingesta:
```bash
python src/ingestion.py
```
Este comando creará el archivo `data/raw/catalog_raw.csv`.

## 3. Simulación de Movimientos de Cocina
Una vez que tenemos el catálogo, simulamos el historial de movimientos (entradas/salidas). El script `src/simulation.py` se encarga de esto.

Para ejecutar la simulación:
```bash
python src/simulation.py
```
Este script leerá el catálogo y creará el archivo `data/raw/movements_raw.csv`.

## 4. Preprocesamiento y Unión de Datos
Con los datos crudos listos, el siguiente paso es limpiarlos y unirlos. El script `src/preprocessing.py` combina la información del catálogo con los movimientos de inventario.

Para ejecutar el preprocesamiento:
```bash
python src/preprocessing.py
```
Este comando generará el archivo `data/processed/inventory_v1.csv`, que es el dataset consolidado y listo para el análisis.

Con estos tres pasos, el pipeline de preparación de datos está completo.