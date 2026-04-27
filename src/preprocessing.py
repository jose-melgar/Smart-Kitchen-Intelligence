import pandas as pd
import os

def process_and_enrich_data():
    print("🚀 Iniciando el proceso de preprocesamiento y enriquecimiento...")
    
    # 1. Cargar los datasets crudos
    catalog_path = "data/raw/catalog_raw.csv"
    movements_path = "data/raw/movements_raw.csv"
    
    if not os.path.exists(catalog_path) or not os.path.exists(movements_path):
        print("❌ Error: Faltan archivos en data/raw/. Ejecuta ingestion.py y simulation.py primero.")
        return

    catalog = pd.read_csv(catalog_path)
    movements = pd.read_csv(movements_path)
    
    # 2. Unión de Datos (Inner Join)
    # Unimos por product_id para asegurar que cada movimiento tenga su metadata nutricional
    df_v1 = pd.merge(movements, catalog, on="product_id", how="inner")
    
    # 3. Conversión de Tipos de Datos
    df_v1['timestamp'] = pd.to_datetime(df_v1['timestamp'])
    df_v1['expiry_date'] = pd.to_datetime(df_v1['expiry_date'])
    
    # 4. Feature Engineering (Ingeniería de Características)
    # Calculamos cuántos días faltaban para el vencimiento en el momento del evento
    df_v1['days_to_expiry'] = (df_v1['expiry_date'] - df_v1['timestamp']).dt.days
    
    # Creamos una columna booleana para identificar productos en riesgo (ej. vencen en < 3 días)
    df_v1['is_at_risk'] = df_v1['days_to_expiry'] <= 3
    
    # 5. Manejo de Datos Faltantes (Imputación Simple)
    # Si algún valor nutricional falló en la ingesta, lo llenamos con 0 para evitar errores en modelos
    cols_to_fix = ['calories_100g', 'proteins_100g', 'carbs_100g']
    for col in cols_to_fix:
        df_v1[col] = df_v1[col].fillna(0)

    # 6. Guardar el Producto Final (Hito 1)
    os.makedirs("data/processed", exist_ok=True)
    output_path = "data/processed/inventory_v1.csv"
    df_v1.to_csv(output_path, index=False)
    
    print(f"✅ Dataset V1 generado exitosamente con {len(df_v1)} registros.")
    print(f"📁 Archivo guardado en: {output_path}")
    
    # Mostrar resumen de calidad
    print("\n--- Resumen del Dataset ---")
    print(df_v1[['event_type', 'classification']].value_counts())

if __name__ == "__main__":
    process_and_enrich_data()