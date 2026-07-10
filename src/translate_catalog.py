"""
Script rápido para traducir los nombres del catálogo al español.
Solo modifica el CSV visual, manteniendo intactos los IDs para la matemática.
"""
import pandas as pd
from deep_translator import GoogleTranslator
from pathlib import Path

# Ruta al catálogo
file_path = Path(__file__).parent.parent / "data/recommender/product_catalog.csv"

print(f"Cargando catálogo desde: {file_path}")
catalog = pd.read_csv(file_path)

print("Iniciando traducción (puede tomar un par de minutos)...")
translator = GoogleTranslator(source='en', target='es')

# Función para traducir de a uno y evitar que falle si hay caracteres raros
def traducir(texto):
    try:
        # Pone la primera letra en mayúscula por estética
        return translator.translate(texto).capitalize()
    except Exception as e:
        return texto # Si falla, deja el original

# Aplicar traducción solo a la columna visual
catalog['product_name'] = catalog['product_name'].apply(traducir)

# Sobrescribir el archivo
catalog.to_csv(file_path, index=False)
print("¡Traducción completada y guardada con éxito! Ya puedes abrir Streamlit.")