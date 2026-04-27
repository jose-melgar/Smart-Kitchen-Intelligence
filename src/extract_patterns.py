import kagglehub
import pandas as pd
import json
import os

def extract_patterns_from_kaggle():
    print("1. Conectando con KaggleHub...")
    print("Descargando dataset de Instacart (se guardará en caché para no descargar 2 veces)...")
    
    # kagglehub descarga el dataset completo y devuelve la ruta temporal donde lo guardó
    dataset_path = kagglehub.dataset_download("yasserh/instacart-online-grocery-basket-analysis-dataset")
    print(f"Dataset localizado en: {dataset_path}")
    
    print("\n2. Leyendo los archivos necesarios...")
    # Leemos los CSV directamente desde la ruta descargada por kagglehub
    orders = pd.read_csv(os.path.join(dataset_path, "orders.csv"))
    prior = pd.read_csv(os.path.join(dataset_path, "order_products__prior.csv"))
    products = pd.read_csv(os.path.join(dataset_path, "products.csv"))
    
    print("\n3. Extrayendo Inteligencia de Negocio (Business Intelligence)...")
    
    # A. Distribución de compras por hora
    hour_dist = orders['order_hour_of_day'].value_counts(normalize=True).round(4).to_dict()
    
    # B. Top 50 productos más comprados (Para no simular con los miles de productos raros)
    top_product_ids = prior['product_id'].value_counts().head(50).index.tolist()
    top_products_df = products[products['product_id'].isin(top_product_ids)]
    productos_dict = top_products_df[['product_id', 'product_name', 'department_id']].to_dict(orient='records')

    # C. Empaquetar todo en un perfil de simulación
    patrones = {
        "distribucion_horas": hour_dist,
        "top_50_productos": productos_dict
    }
    
    # Guardamos el resultado en la carpeta raw
    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/instacart_patterns.json", "w") as f:
        json.dump(patrones, f, indent=2)
        
    print("\n¡Éxito! Archivo 'data/raw/instacart_patterns.json' generado.")
    print("El simulador ahora puede usar este archivo ligero sin necesidad de cargar Kaggle.")

if __name__ == "__main__":
    extract_patterns_from_kaggle()