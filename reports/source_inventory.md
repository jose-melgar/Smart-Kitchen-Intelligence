# Inventario de Fuentes de Datos (Master Data Management)

Este documento detalla el origen y el propósito de los datos utilizados para la construcción del Dataset V1 del proyecto Smart Kitchen Intelligence.

## Fuente 1: Instacart Online Grocery Dataset (Patrones de Consumo)
* **Origen:** [Kaggle - Instacart Dataset](https://www.kaggle.com/datasets/yasserh/instacart-online-grocery-basket-analysis-dataset)
* **Método de Ingesta:** Automatizado mediante la librería `kagglehub`.
* **Uso:** Proporciona la "Inteligencia de Mercado". Se extraen las probabilidades estocásticas de compra por hora del día y la frecuencia de productos para alimentar el motor de simulación, asegurando que los datos sintéticos sigan comportamientos humanos reales.

## Fuente 2: USDA FoodData Central (Metadata Nutricional)
* **URL:** [https://fdc.nal.usda.gov/](https://fdc.nal.usda.gov/)
* **Método de Ingesta:** API REST con autenticación mediante API Key.
* **Uso:** Fuente primaria de verdad para la información nutricional (Calorías, Proteínas, Carbohidratos). Se seleccionó sobre OpenFoodFacts por su alineación exacta con el catálogo de productos estadounidense presente en Instacart.

## Fuente 3: Logs de Interacción Basados en Evidencia
* **Origen:** Motor de simulación estocástica (`src/simulation.py`).
* **Uso:** Genera la capa transaccional (Hechos). Utiliza los pesos estadísticos de la Fuente 1 para crear un historial de 30 días con alta fidelidad técnica (UUIDs, Timestamps y Depleción Granular).

---

## Estrategia de Integridad y Calidad de Datos

Dada la variabilidad de las APIs externas, el pipeline implementa un protocolo de **Búsqueda en Dos Niveles (Two-Tier Search)**:

1. **Capa Intermediaria (Normalización):** El script de ingesta actúa como traductor, limpiando modificadores comerciales (ej. "Organic", "Bag of") para maximizar la tasa de acierto (*hit rate*) en la API de la USDA.
2. **Transparencia de Datos (Missingness):** En lugar de inyectar datos sintéticos arbitrarios, el sistema opta por el **Manejo Explícito de Ausencias**. Si un producto no es hallado, se registra como `Falta Dato`, permitiendo una posterior fase de imputación estadística en el preprocesamiento.