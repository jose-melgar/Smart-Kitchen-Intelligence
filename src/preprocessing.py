import pandas as pd
import os

def process_v1_dataset():
    # 1. Cargar datos crudos
    catalog_path = 'data/raw/catalog_raw.csv'
    movements_path = 'data/raw/movements_raw.csv'
    
    if not os.path.exists(catalog_path) or not os.path.exists(movements_path):
        print("Error: No se encuentran los archivos en data/raw/. Ejecuta ingestion y simulation primero.")
        return

    df_cat = pd.read_csv(catalog_path)
    df_mov = pd.read_csv(movements_path)

    # 2. Limpieza básica
    # Convertir timestamps a objetos datetime
    df_mov['timestamp'] = pd.to_datetime(df_mov['timestamp'])
    
    # Manejo de nulos en fechas de vencimiento (rellenar con 'N/A' para el CSV final)
    df_mov['expiry_date'] = df_mov['expiry_date'].fillna('N/A')

    # 3. JOIN: Unir movimientos con información del catálogo
    # Usamos un left join para mantener todos los movimientos aunque el ID no esté en el catálogo
    inventory_v1 = pd.merge(df_mov, df_cat, on='product_id', how='left')

    # 4. Guardar el dataset procesado
    os.makedirs('data/processed', exist_ok=True)
    output_path = 'data/processed/inventory_v1.csv'
    inventory_v1.to_csv(output_path, index=False)
    
    print(f"Éxito: Processed Dataset V1 guardado en {output_path}")
    print(f"Total de registros procesados: {len(inventory_v1)}")

if __name__ == "__main__":
    process_v1_dataset()