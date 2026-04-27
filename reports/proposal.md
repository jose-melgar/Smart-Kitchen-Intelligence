# Propuesta del Proyecto: Smart Kitchen Intelligence (SKI)

## Dominio y Contexto
Gestión automatizada de inventarios inteligentes en el ecosistema del hogar, enfocada en la reducción del desperdicio alimentario y la optimización de la salud nutricional mediante arquitecturas de Big Data. El sistema integra patrones de consumo masivo con metadata nutricional oficial.

## Declaración del Problema
La invisibilidad de los ciclos de vida de los alimentos y la falta de correlación entre el inventario disponible y el consumo histórico genera ineficiencia económica y nutricional. Los usuarios suelen comprar por impulso o hábito sin considerar la caducidad ni el equilibrio macro-nutricional de sus existencias.

## Pregunta del Producto (Product Question)
¿Cómo puede un sistema de recomendación híbrido optimizar el consumo de alimentos basándose en la proximidad de vencimiento (FoodKeeper), el perfil nutricional real (USDA) y la co-ocurrencia histórica de ingredientes (Instacart Patterns)?

### Definiciones Operacionales
Para responder a la pregunta del producto con rigor matemático, definimos:

1. **Co-ocurrencia Histórica:** Frecuencia relativa con la que un conjunto de productos $\{A, B\}$ aparecen en una misma ventana temporal. Este proyecto utiliza las **Reglas de Asociación** extraídas del dataset de Instacart para validar estas relaciones.
2. **Ventana Temporal ($\Delta t$):**
   - **Ventana de Abastecimiento (Restock Window):** Intervalo de **60 minutos** para eventos 'IN'. Utilizada para identificar sesiones de compra y comportamiento de stock.
   - **Ventana de Sesión de Cocina (Kitchen Session):** Intervalo de **15 minutos** para eventos 'OUT'. Utilizada para inferir recetas y hábitos de preparación simultánea.
3. **Fórmula de Proximidad:** Dos eventos $e_1$ y $e_2$ son considerados co-ocurrentes si:
   $|timestamp(e_1) - timestamp(e_2)| \le \Delta t$



## Idoneidad para el curso de Big Data
Este proyecto cumple con los criterios de excelencia al integrar:
- **Variedad:** Fusión de datos estructurados (Instacart CSV), semi-estructurados (Vectores de probabilidad en JSON) y consumo de APIs REST (USDA FoodData Central).
- **Análisis de Grafos (Proyección):** Implementación de métricas de centralidad para modelar productos "ancla" en la dieta del usuario.
- **Escalabilidad:** Pipeline diseñado para transicionar de procesamiento local a arquitecturas de alto rendimiento mediante **Polars** y almacenamiento columnar en **Parquet**.