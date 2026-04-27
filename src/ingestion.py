import requests
import pandas as pd
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()
USDA_API_KEY = os.getenv("USDA_API_KEY")

def fetch_from_usda(product_name):
    if not USDA_API_KEY:
        print("❌ Error: No se encontró la USDA_API_KEY en el archivo .env")
        return None
    """Consulta la USDA FoodData Central para obtener nutrición real."""
    # Limpiamos el nombre para mejorar la búsqueda
    clean_query = product_name.replace("Organic", "").strip()
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}&query={clean_query}&pageSize=1"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['foods']:
                food = data['foods'][0]
                nutrients = food.get('foodNutrients', [])
                
                # IDs de la USDA: 1008=Energía, 1003=Proteína, 1005=Carbohidratos
                res = {}
                for n in nutrients:
                    if n['nutrientId'] == 1008: res['calories_100g'] = n['value']
                    if n['nutrientId'] == 1003: res['proteins_100g'] = n['value']
                    if n['nutrientId'] == 1005: res['carbs_100g'] = n['value']
                return res
    except Exception:
        pass
    return None

def build_catalog_from_movements():
    print("1. Analizando movimientos y recuperando nombres desde patrones...")
    
    # Cargar movimientos (solo tienen IDs)
    movements_path = "data/raw/movements_raw.csv"
    if not os.path.exists(movements_path):
        raise FileNotFoundError("Ejecuta simulation.py primero.")
    
    movements = pd.read_csv(movements_path)
    unique_ids = movements['product_id'].unique()

    # Cargar patrones para recuperar el nombre (mapeo ID -> Nombre)
    with open("data/raw/instacart_patterns.json", "r") as f:
        patterns = json.load(f)
    
    # Crear un diccionario de búsqueda rápida {id: nombre}
    id_to_name = {p['product_id']: p['product_name'] for p in patterns['top_50_productos']}
    id_to_dept = {p['product_id']: p['department_id'] for p in patterns['top_50_productos']}

    print(f"Detectados {len(unique_ids)} productos únicos. Consultando USDA...")
    
    catalog_list = []
    for p_id in unique_ids:
        p_name = id_to_name.get(p_id, "Unknown Product")
        p_dept = id_to_dept.get(p_id, 0)
        
        print(f"Buscando: {p_name} (ID: {p_id})...")
        usda_data = fetch_from_usda(p_name)
        
        if usda_data:
            usda_data.update({
                "product_id": p_id, 
                "product_name": p_name,
                "category": p_dept
            })
            catalog_list.append(usda_data)
        else:
            catalog_list.append({
                "product_id": p_id, "product_name": p_name, "category": p_dept,
                "nutriscore": "Falta Dato", "calories_100g": None,
                "proteins_100g": None, "carbs_100g": None
            })
        
        # Rate limit preventivo
        time.sleep(1.1) 

    df_catalog = pd.DataFrame(catalog_list)
    
    # Asignación de Nutriscore basada en calorías para los datos obtenidos
    def assign_nutriscore(cal):
        if pd.isna(cal): return "Falta Dato"
        if cal < 50: return "A"
        if cal < 150: return "B"
        if cal < 300: return "C"
        return "D"
    
    if not df_catalog.empty:
        df_catalog['nutriscore'] = df_catalog['calories_100g'].apply(assign_nutriscore)
    
    os.makedirs("data/raw", exist_ok=True)
    df_catalog.to_csv("data/raw/catalog_raw.csv", index=False)
    print(f"✅ Catálogo generado con {len(df_catalog)} registros alineados.")

if __name__ == "__main__":
    build_catalog_from_movements()