import requests
import pandas as pd
import os

def get_mock_catalog():
    """Genera un catálogo básico si la API falla para no detener el desarrollo."""
    print("Generando catálogo de emergencia (Mock Data)...")
    mock_data = [
        {"product_id": "8410010012345", "product_name": "Leche Entera", "category": "Lácteos", "nutriscore": "B", "calories_100g": 62, "proteins_100g": 3.2, "carbs_100g": 4.8},
        {"product_id": "8410020054321", "product_name": "Arroz Integral", "category": "Granos", "nutriscore": "A", "calories_100g": 350, "proteins_100g": 7.5, "carbs_100g": 72},
        {"product_id": "8410030098765", "product_name": "Atún en lata", "category": "Pescados", "nutriscore": "B", "calories_100g": 116, "proteins_100g": 26, "carbs_100g": 0.1},
        {"product_id": "8410040011111", "product_name": "Yogurt Natural", "category": "Lácteos", "nutriscore": "A", "calories_100g": 59, "proteins_100g": 3.5, "carbs_100g": 4.7},
        {"product_id": "8410050022222", "product_name": "Pasta Espagueti", "category": "Cereales", "nutriscore": "A", "calories_100g": 358, "proteins_100g": 12, "carbs_100g": 71}
    ]
    return pd.DataFrame(mock_data)

def fetch_openfoodfacts_data(limit=50):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&sort_by=unique_scans_n&page_size={limit}&json=True&tagtype_0=languages&tag_contains_0=contains&tag_0=spanish"
    headers = {"User-Agent": "SmartKitchenIntelligence - UPC-Project - Version 1.1"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            products = response.json().get('products', [])
            if products:
                print(f"Éxito: {len(products)} productos obtenidos de la API.")
                return pd.DataFrame([{
                    "product_id": p.get('code'),
                    "product_name": p.get('product_name', 'N/A'),
                    "category": p.get('categories', 'N/A').split(',')[0],
                    "nutriscore": p.get('nutrition_grades', 'N/A').upper(),
                    "calories_100g": p.get('nutriments', {}).get('energy-kcal_100g', 0),
                    "proteins_100g": p.get('nutriments', {}).get('proteins_100g', 0),
                    "carbs_100g": p.get('nutriments', {}).get('carbohydrates_100g', 0)
                } for p in products])
        
        print(f"Advertencia: Servidor respondió con {response.status_code}. Usando fallback.")
    except Exception as e:
        print(f"Error de conexión: {e}. Usando fallback.")
    
    return get_mock_catalog()

if __name__ == "__main__":
    os.makedirs('data/raw', exist_ok=True)
    df_catalog = fetch_openfoodfacts_data(limit=50) # Reducimos el límite para evitar saturación
    path = 'data/raw/catalog_raw.csv'
    df_catalog.to_csv(path, index=False)
    print(f"Catálogo listo en {path}")