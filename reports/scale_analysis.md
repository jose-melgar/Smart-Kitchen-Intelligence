# Análisis de Escala (V1)

## Dimensiones Generales
- **Registros totales (Catálogo):** ~1,000 productos (extraídos de API).
- **Registros totales (Eventos):** ~10,000 eventos (simulados para la Fase 1).

## Calidad de los Datos
- **Missingness (Datos faltantes):** Se registra un 5% de nulos en `expiry_date` para simular errores de sensor/usuario.
- **Sparsity (Dispersión):** Matriz de interacción usuario-producto altamente dispersa (ideal para Collaborative Filtering en Sem 10).
- **Memoria:** Estimación de 15MB para el dataset V1 en formato Parquet.