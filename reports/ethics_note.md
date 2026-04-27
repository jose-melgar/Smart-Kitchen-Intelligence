# Nota de Ética y Acceso

## Seguridad y Privacidad de Credenciales
- **Manejo de Secretos:** El proyecto implementa una arquitectura de separación de secretos. Las credenciales de acceso a la **USDA FoodData Central API** se gestionan mediante variables de entorno locales y archivos de configuración protegidos (`.env`).
- **Exclusión de Repositorios:** Siguiendo las mejores prácticas de seguridad, todas las llaves de API están estrictamente excluidas del control de versiones (GitHub) mediante reglas de `.gitignore`, garantizando que no haya exposición accidental de credenciales.

## Origen y Permisos
- **Metadata Nutricional:** Los datos provienen de la **USDA FoodData Central API**, una fuente de datos abiertos del gobierno de EE. UU. dedicada a la transparencia alimentaria.
- **Patrones de Comportamiento:** Se utiliza el dataset público de **Instacart Online Grocery**, anonimizado y liberado para fines de investigación académica.
- **Ingesta:** No se realiza scraping de perfiles privados ni se vulneran términos de servicio de plataformas restringidas. El acceso a los datos se realiza mediante protocolos oficiales (KaggleHub y API REST).

## Privacidad de Datos Personales
Para mitigar riesgos de privacidad y cumplir con las directrices de manejo de datos sensibles:
1. **Generación Sintética:** No se utilizan datos de usuarios reales. Toda la capa de interacción individual es generada mediante simulación estocástica basada en las distribuciones agregadas de Instacart.
2. **Anonimización por Diseño:** Aunque se utilizan patrones de comportamiento reales para la simulación, el sistema crea perfiles "estándar", eliminando cualquier vínculo con individuos específicos del dataset original.
3. **Manejo de PII:** El sistema no almacena ni procesa nombres, direcciones, correos electrónicos ni información financiera. Toda la Información de Identificación Personal (PII) es inexistente en el dataset; los identificadores únicos (`stock_id`, `event_id`) son UUIDs generados internamente sin relación con identidades reales.

## Responsabilidad Algorítmica
- **Transparencia en Desperdicio:** El sistema clasifica el desperdicio (`Waste`) de forma transparente basándose en los estándares de persistencia de la **FoodKeeper App** (USDA).
- **Alcance Informativo:** El usuario mantiene el control total sobre la interpretación de las recomendaciones nutricionales. Los resultados del sistema actúan como una guía informativa para la gestión de inventario y no constituyen una prescripción médica o nutricional.