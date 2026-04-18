# Propuesta del Proyecto: Smart Kitchen Intelligence (SKI)

## Dominio y Contexto
Gestión automatizada de inventarios inteligentes en el ecosistema del hogar, enfocada en la reducción del desperdicio alimentario y la optimización de la salud nutricional mediante Big Data.

## Declaración del Problema
La invisibilidad de los ciclos de vida de los alimentos y la falta de correlación entre el inventario disponible y el consumo histórico genera ineficiencia económica y nutricional.

## Pregunta del Producto (Product Question)
¿Cómo puede un sistema de recomendación híbrido optimizar el consumo de alimentos basándose en la proximidad de vencimiento, el perfil nutricional y la co-ocurrencia histórica de ingredientes?

### Definiciones Operacionales
Para responder a la pregunta del producto con rigor matemático, definimos:

1. **Co-ocurrencia Histórica:** Se define como la frecuencia relativa con la que un conjunto de productos $\{A, B\}$ son registrados bajo un mismo tipo de acción en una ventana temporal común.
2. **Ventana Temporal ($\Delta t$):**
   - **Ventana de Abastecimiento (Restock Window):** Intervalo de **60 minutos** para eventos 'IN'. Utilizada para identificar patrones de compra y agrupamiento de proveedores.
   - **Ventana de Sesión de Cocina (Kitchen Session):** Intervalo de **15 minutos** para eventos 'OUT'. Utilizada para inferir recetas y hábitos de preparación simultánea de alimentos.
3. **Fórmula de Proximidad:** Dos eventos $e_1$ y $e_2$ son considerados co-ocurrentes si:
   $|timestamp(e_1) - timestamp(e_2)| \le \Delta t$

## Idoneidad para el curso de Big Data
Este proyecto cumple con los criterios de excelencia al integrar:
- **Variedad:** Fusión de datos estructurados (CSV local) con semi-estructurados (JSON API).
- **Análisis de Grafos:** Implementación de centralidad y co-ocurrencia para modelar el comportamiento del usuario.
- **Escalabilidad:** Pipeline diseñado para transicionar de procesamiento local a arquitecturas distribuidas.