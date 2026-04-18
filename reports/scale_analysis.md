# Análisis de Escala (Dataset V1 - Verificado)

## Dimensiones del Dataset Procesado
- **Registros Totales:** 1,000 eventos de interacción (logs).
- **Entidades Únicas (Catálogo):** 50 productos reales (extraídos de OpenFoodFacts).
- **Ancho del Dataset:** 12 variables (6 de interacción + 6 de metadatos nutricionales).

## Calidad y Completitud (Data Quality)
- **Missingness (Nulos):** Se identifica un 58% de valores nulos en la columna `expiry_date`. Este es un "vacío por diseño" (Missingness by Design), ya que los eventos de tipo 'OUT' (consumo) no requieren registro de vencimiento.
- **Sparsity (Dispersión):** La densidad del dataset es de 20 interacciones por producto. Esta dispersión es ideal para validar algoritmos de filtrado colaborativo en fases posteriores.
- **Inconsistencias:** No se detectaron duplicados en la columna `event_id`, garantizando la integridad de la Primary Key.

## Resiliencia del Pipeline
- El volumen actual es manejable en memoria RAM (~250 KB), pero el pipeline de preprocesamiento ha sido validado para escalar linealmente mediante el uso de Joins optimizados en Pandas.