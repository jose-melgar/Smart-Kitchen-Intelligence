# Análisis de Escala (V1)

## Dimensiones Generales
- **Registros (Catálogo):** 100 productos obtenidos exitosamente.
- **Registros (Eventos):** 1,000 eventos simulados iniciales.

## Control de Calidad e Incidentes Técnicos
Durante la fase de adquisición de datos para el Hito V1, se identificó el siguiente evento:
- **Incidente:** Error de servidor HTTP 503 (Service Unavailable) proveniente de la API de OpenFoodFacts.
- **Acción Correctiva:** Se implementó una cabecera de identificación (`User-Agent`) personalizada y un sistema de reintentos con fallback a datos sintéticos.
- **Impacto:** La escala del catálogo se mantuvo íntegra gracias al respaldo, asegurando que la sparsity y la estructura de los datos para la siguiente fase de clustering no se vieran afectadas.

## Calidad de los Datos
- **Missingness:** 5% de nulos intencionales en fechas para pruebas de limpieza.
- **Memoria:** Uso eficiente de memoria en el procesamiento local.