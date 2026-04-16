# Propuesta del Proyecto: Smart Kitchen Intelligence (SKI)

## Dominio y Contexto
El proyecto se sitúa en el dominio de **Smart Cities y Hogares Inteligentes**, específicamente en la gestión automatizada de inventarios de cocina (refrigeradores, estanterías y despensas).

## Declaración del Problema
La falta de visibilidad sobre el inventario real de alimentos en el hogar conduce a dos problemas críticos:
1. **Desperdicio de Alimentos:** Productos que caducan por olvido.
2. **Nutrición Ineficiente:** Dificultad para planificar comidas saludables con los ingredientes disponibles.

## Pregunta del Producto (Product Question)
¿Cómo puede un sistema de recomendación híbrido optimizar el consumo de alimentos basándose en la proximidad de vencimiento, el perfil nutricional y la co-ocurrencia histórica de ingredientes?

## Idoneidad para el curso de Big Data
Este proyecto es apto porque permite implementar todas las capas exigidas:
- **Variedad:** Combina metadatos nutricionales (API) con registros de eventos (Simulación).
- **Análisis de Grafos:** Permite modelar relaciones de co-ocurrencia de alimentos.
- **Escalabilidad:** El pipeline está diseñado para procesar miles de transacciones de inventario.