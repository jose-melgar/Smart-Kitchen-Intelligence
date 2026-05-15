# Declaración de Selección de Modelo Final (Hito 3)

## 1. Modelo Ganador: DBSCAN Refinado
Tras un proceso de benchmark competitivo, se ha seleccionado el algoritmo **DBSCAN** con parámetros **épsilon=2.7** y **min_samples=15** como el motor de segmentación para Smart Kitchen Intelligence.

## 2. Justificación Técnica
1. **Cohesión Estadística:** Presentó el mayor **Silhouette Score (0.6549)**, lo que garantiza grupos con fronteras claras y alta similitud interna.
2. **Estabilidad:** El proceso de refinamiento demostró que el modelo es estable en el rango de $eps$ [2.3 - 2.7], asegurando que los clusters no son producto del azar.
3. **Manejo de Ruido:** Logró reducir el ruido al **0.28%**, integrando casi la totalidad de los 25,444 eventos en patrones de comportamiento lógicos.
4. **Capacidad de Perfilamiento:** Identificó **38 perfiles únicos**, lo que permite una granularidad ideal para diferenciar hábitos como "Consumo de perecederos matutinos" vs "Abastecimiento de larga duración".

## 3. Conclusión
Este modelo transforma la matriz reducida del Hito 2 en una capa de inteligencia segmentada. El resultado permite que el sistema de SKI no solo vea productos, sino que entienda el **comportamiento latente** detrás de cada movimiento de inventario, sentando las bases para el motor de recomendaciones híbrido.