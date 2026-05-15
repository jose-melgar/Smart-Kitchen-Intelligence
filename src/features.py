import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import category_encoders as ce
import os
import json

def build_feature_matrix():
    print("Iniciando pipeline de características densas (Hito 2)...")
    
    input_path = "data/processed/inventory_v1.csv"
    if not os.path.exists(input_path):
        print(f"Error: {input_path} no encontrado.")
        return
    
    df = pd.read_csv(input_path)

    # 1. Variables Numéricas (Imputación por media de categoría)
    numeric_cols = ['calories_100g', 'proteins_100g', 'carbs_100g']
    for c in numeric_cols:
        df[c] = df.groupby('category')[c].transform(lambda x: x.fillna(x.mean())).fillna(0)
    
    # 2. Variables de Texto (TF-IDF)
    print("📝 Procesando texto (TF-IDF)...")
    tfidf = TfidfVectorizer(max_features=50, stop_words='english')
    text_features = tfidf.fit_transform(df['product_name'].fillna('')).toarray()
    text_cols = [f"txt_{w}" for w in tfidf.get_feature_names_out()]
    df_text = pd.DataFrame(text_features, columns=text_cols)

    # 3. Codificación Densa de Categorías (CatBoost Encoding)
    # Reemplazamos One-Hot Encoding para evitar matrices dispersas (Sparsity).
    # Usamos la probabilidad de "consumo/desperdicio" ('OUT') como target estadístico.
    print("🏷️ Aplicando CatBoost Encoder (Target Encoding) a categorías...")
    target = np.where(df['event_type'] == 'OUT', 1, 0)
    cbe = ce.CatBoostEncoder(cols=['category'])
    df_cat = cbe.fit_transform(df[['category']], target)
    df_cat.columns = ['category_encoded']

    # 4. Variables Temporales
    print("⏰ Extrayendo características temporales...")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_time = pd.DataFrame({
        'hour_of_day': df['timestamp'].dt.hour,
        'day_of_week': df['timestamp'].dt.dayofweek
    })

    # 5. Consolidación
    df_num = df[numeric_cols].reset_index(drop=True)
    full_matrix = pd.concat([df_num, df_cat, df_text, df_time], axis=1)
    
    # 6. Escalado Final (Obligatorio para PCA y t-SNE)
    print("⚖️ Aplicando StandardScaler...")
    scaler = StandardScaler()
    X_raw = full_matrix.to_numpy() 
    scaled_data = scaler.fit_transform(X_raw)
    
    # 7. Persistencia
    os.makedirs("data/features", exist_ok=True)
    np.save("data/features/feature_matrix.npy", scaled_data)
    
    with open("data/features/feature_names.json", "w") as f:
        json.dump(full_matrix.columns.tolist(), f)

    print(f"✅ Features densas generadas exitosamente. Nueva dimensión: {scaled_data.shape}")

if __name__ == "__main__":
    build_feature_matrix()