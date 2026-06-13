# Reporte de Experimentos de Recomendación y Análisis de Errores (Hito 4)

## 1. Análisis de Errores Cualitativo (Error Analysis)
Para auditar el comportamiento del recomendador híbrido en producción, el pipeline automatizado en `src/evaluation.py` extrajo los 5 casos de éxito rotundo (*strong cases*, sesiones con $\ge 2$ aciertos en Top-5) y los 5 casos de falla absoluta (*failure cases*, cero aciertos), guardados en `data/recommender/error_analysis.csv`.

### Hallazgos Clave:
* **Casos de Éxito (*Strong Cases*):** Concentrados de forma reproducible en sesiones densas con un volumen alto de historial previo (*n_train_seen*). Esto permite que la regresión por mínimos cuadrados sobre los factores latentes de la matriz de ítems de ALS ($Y$) proyecte un vector de sesión estable y de alta confianza.
* **Casos de Falla (*Failure Cases*):** Asociados a sesiones con un volumen inusualmente elevado de productos reales en el hold-out (*n_truth* alto) o canastas con alta volatilidad estocástica. El tamaño restrictivo del corte del Top-5 genera un cuello de botella matemático que impide capturar interacciones de canastas masivas y diversas.

## 2. Limitaciones de la Representación Nutricional
Se reconoce que la discretización de variables continuas de la API de la USDA en tokens textuales (`cal_low`, `prot_mid`, etc.) dentro de la Capa de Contenido introduce una suposición de ortogonalidad matemática en el espacio vectorial de TF-IDF. Al calcular la similitud coseno mediante producto punto con norma $L2$, el modelo asume de forma errónea que la distancia entre un nivel bajo y medio de calorías es idéntica a la distancia entre un nivel bajo y alto. 

### Trabajo Futuro:
Se establece como deuda técnica prioritaria migrar hacia arquitecturas de recomendación de dos torres (*Two-Tower Neural Networks*) o implementar *Target Encoding* ordinal continuo para preservar las nociones métricas de intervalo físico de los nutrientes en el Hito 6.