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