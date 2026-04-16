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
El primer paso es obtener el catálogo de productos. El script `src/ingestion.py` se conecta a la API de Open Food Facts para descargar datos de productos. Si la API falla, genera un conjunto de datos de respaldo (mock).

Para ejecutar la ingesta:
```bash
python src/ingestion.py
```
Este comando creará el archivo `data/raw/catalog_raw.csv`, que es esencial para el siguiente paso.

## 3. Simulación de Movimientos de Cocina (Base de Datos)
Una vez que tenemos el catálogo, podemos simular el historial de movimientos de la cocina (entradas y salidas de productos). El script `src/simulation.py` se encarga de esto.

Para ejecutar la simulación:
```bash
python src/simulation.py
```
Este script leerá el catálogo previamente generado y creará el archivo `data/raw/movements_raw.csv` con datos de eventos simulados.

Con estos dos pasos, tendrás los datos brutos necesarios para continuar con las siguientes fases del proyecto.