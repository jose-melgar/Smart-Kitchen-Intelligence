# Smart Kitchen Intelligence (SKI)

**Estado Actual:** Fase 1 (Semana 3) Completada. Pipeline de datos inicial implementado, generando el dataset procesado `inventory_v1.csv` de manera reproducible.

## 1. Descripción del Proyecto

**Smart Kitchen Intelligence (SKI)** es un prototipo de sistema de datos diseñado para abordar el desperdicio de alimentos y la nutrición ineficiente en el hogar. El sistema ingiere metadatos de productos desde la API de OpenFoodFacts y simula un historial de interacciones de inventario (entradas y salidas) para crear un dataset robusto que sirva de base para análisis avanzados.

El objetivo final no es solo monitorear un inventario, sino construir un motor de recomendación y descubrimiento que responda a la pregunta: *¿Cómo optimizar el consumo de alimentos basándose en la proximidad de vencimiento, el perfil nutricional y la co-ocurrencia histórica de ingredientes?*

## 2. Quick Start: Reproducción del Pipeline V1

Para ejecutar el pipeline completo y generar el dataset procesado `data/processed/inventory_v1.csv`, siga estos pasos. Se asume un entorno tipo Unix (Linux/macOS).

```bash
# 1. Clonar el repositorio
git clone https://github.com/jose-melgar/Smart-Kitchen-Intelligence.git
cd Smart-Kitchen-Intelligence

# 2. Configurar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar el pipeline de datos en secuencia
echo ">>> (1/3) Ejecutando ingesta de catálogo..."
python src/ingestion.py

echo ">>> (2/3) Ejecutando simulación de movimientos..."
python src/simulation.py


echo ">>> (3/3) Ejecutando preprocesamiento y unión de datos..."
python src/preprocessing.py


echo ">>> Pipeline completado. Dataset disponible en: data/processed/inventory_v1.csv"
```
Para una guía más detallada, consulte el [**Runbook de Ejecución (`runbook.md`)**](./runbook.md).

## 3. Arquitectura y Capas del Sistema

El proyecto está estructurado en capas interdependientes que permiten un desarrollo modular y escalable.

*   **Capa de Ingesta y Simulación:**
    *   `src/ingestion.py`: Se conecta a la API de OpenFoodFacts. Incluye una estrategia de *fallback* a datos mock para garantizar la resiliencia del pipeline.
    *   `src/simulation.py`: Genera un log de eventos de inventario (`IN`/`OUT`) basado en el catálogo de productos, creando la capa de interacción necesaria para el filtrado colaborativo y el análisis de comportamiento.

*   **Capa de Procesamiento (ETL):**
    *   `src/preprocessing.py`: Realiza la unión (join) entre los datos de catálogo y los logs de movimiento. Normaliza tipos de datos y prepara el dataset analítico principal (`inventory_v1.csv`) basado en un [Esquema de Estrella](./schema_draft.md) desnormalizado.

*   **Capa de Análisis y Modelado (Fases Futuras):**
    *   **Ingeniería de Características:** Creación de variables como `días_hasta_vencimiento` o perfiles de consumo por usuario (simulado).
    *   **Análisis de Grafos:** Construcción de un grafo de co-ocurrencia de productos (basado en eventos `IN` con proximidad temporal) para identificar sustitutos o complementos.
    *   **Sistema de Recomendación:** Desarrollo de un motor híbrido que pondera la popularidad, el perfil nutricional, la fecha de vencimiento y las señales del grafo.

## 4. Estructura del Repositorio

La estructura de directorios está diseñada para garantizar la separación de conceptos y la reproducibilidad, un pilar fundamental de la ingeniería de datos.

```text
.
├── data/              # Datos versionados con Git LFS o DVC (no código)
│   ├── raw/           # Salida inmutable de los scripts de ingesta/simulación
│   └── processed/     # Datasets limpios y listos para modelado
├── src/               # Código fuente Python modular y ejecutable
├── notebooks/         # Jupyter Notebooks para análisis exploratorio (EDA) y prototipado
├── reports/           # Documentación clave del proyecto (propuesta, análisis, etc.)
├── runbook.md         # Guía de ejecución detallada del pipeline
└── requirements.txt   # Dependencias del proyecto
```

## 5. Documentación Clave del Proyecto

La toma de decisiones de ingeniería y el diseño del sistema están documentados en los siguientes reportes:

| Documento | Propósito |
| :--- | :--- |
| **`proposal.md`** | Define el problema, la pregunta de producto y la idoneidad del proyecto. |
| **`source_inventory.md`**| Cataloga las fuentes de datos y la estrategia de resiliencia. |
| **`schema_draft.md`** | Justifica la elección del esquema de datos y su impacto en el rendimiento. |
| **`scale_analysis.md`** | Analiza la escalabilidad del pipeline e identifica cuellos de botella. |
| **`data_dictionary.md`** | Proporciona una definición precisa de cada variable en el dataset procesado. |
| **`ethics_note.md`** | Aborda el origen de los datos y las medidas de mitigación de riesgos. |

---
**Curso:** Big Data | **Universidad:** UPC | **Track:** B (Build-Your-Own Dataset)