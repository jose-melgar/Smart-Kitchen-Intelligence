import polars as pl
import os

def run_preprocessing():
    print("🧹 Iniciando Pre-procesamiento (Polars) para alto volumen...")
    
    # 1. Definición de rutas EXACTAS
    movements_path = "data/raw/movements_raw.csv"
    catalog_path = "data/raw/catalog_raw.csv" 
    output_path = "data/processed/inventory_v1.csv"

    # Verificar existencia de archivos
    if not os.path.exists(movements_path):
        print(f"❌ Error: No se encuentra {movements_path}")
        return
    if not os.path.exists(catalog_path):
        print(f"❌ Error: No se encuentra {catalog_path}")
        return

    # 2. Carga ultra-rápida con Polars
    df_movements = pl.read_csv(movements_path)
    df_catalog = pl.read_csv(catalog_path)

    # 3. Limpieza de columnas duplicadas en el catálogo
    # Solo tomamos las métricas nutricionales y la categoría para evitar colisión de nombres
    catalog_subset = df_catalog.select([
        "product_id", 
        "nutriscore", 
        "calories_100g", 
        "proteins_100g", 
        "carbs_100g", 
        "category"
    ])

    # 4. Asegurar compatibilidad de tipos
    df_movements = df_movements.with_columns(pl.col("product_id").cast(pl.Int64))
    catalog_subset = catalog_subset.with_columns(pl.col("product_id").cast(pl.Int64))

    # 5. Ejecutar el Join
    inventory_v1 = df_movements.join(
        catalog_subset,
        on="product_id",
        how="left"
    )

    # 6. Guardar el resultado
    os.makedirs("data/processed", exist_ok=True)
    inventory_v1.write_csv(output_path)
    
    print(f"✅ ¡Dataset consolidado con éxito!")
    print(f"📁 Archivo generado: {output_path}")
    print(f"📊 Total de registros procesados: {len(inventory_v1)}")

if __name__ == "__main__":
    run_preprocessing()