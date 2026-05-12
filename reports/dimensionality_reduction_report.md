# Reporte Técnico: Reducción de Dimensionalidad y Visualización (Hito 2)

## 1. Metodología de Compresión
Se aplicó **PCA (Principal Component Analysis)** sobre la matriz consolidada de 56 características densas para gestionar la complejidad multimodal del inventario. El flujo incluyó:
1. Imputación por media de categoría.
2. Vectorización TF-IDF y Target Encoding (CatBoost).
3. Escalado estándar obligatorio para asegurar que variables como calorías no dominen sobre proteínas.

## 2. Análisis de Energía Retenida (SVD/PCA)
El objetivo fue retener el **90% de la varianza acumulada** para preservar la inteligencia nutricional y temporal del sistema.

| Componente | Varianza Explicada | Varianza Acumulada |
| :--- | :--- | :--- |
| PC1 | 6.98% | 6.98% |
| PC2 | 5.58% | 12.56% |
| PC3 | 4.81% | 17.38% |
| PC4 | 4.50% | 21.88% |
| PC5 | 4.19% | 26.07% |

**Conclusión:** Se determinó que **30 componentes principales** son necesarios para alcanzar el **90.01%** de energía. Esto refleja una baja redundancia; los hábitos de la cocina son diversos y requieren esta profundidad para ser modelados correctamente.

## 3. Visualizaciones e Interpretación

### A. Scree Plot (Justificación Técnica)
El gráfico muestra que el 90% de la información se captura en el componente 30, permitiendo una reducción del 46% del espacio de datos original sin pérdida significativa de precisión.


### B. t-SNE Clusters (Exploración No Lineal)
Se implementó **t-SNE** como método complementario de visualización. A diferencia de la proyección lineal de PCA, t-SNE revela "islas" de comportamiento, lo que confirma que el Feature Engineering ha logrado separar grupos lógicos de productos y patrones de consumo por hogar.


### C. PCA Biplot (Impacto de Variables)
El Biplot superpone los vectores de carga sobre los datos. Variables como `category_encoded` y los indicadores nutricionales muestran los vectores más largos, demostrando ser los factores con mayor peso en la diferenciación del inventario.


## 4. Dataset Final
La matriz reducida se ha guardado en `feature_matrix_reduced.npy` (30 dimensiones). Este archivo constituye el **Single Source of Truth** para la fase de clustering de la Semana 7.