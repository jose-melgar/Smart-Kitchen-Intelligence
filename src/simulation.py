import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def simulate_kitchen_movements(catalog_path, num_events=1000):
    if not os.path.exists(catalog_path):
        print("Error: No existe el catálogo base para simular.")
        return
    
    df_cat = pd.read_csv(catalog_path)
    product_ids = df_cat['product_id'].unique()
    
    events = []
    locations = ['Refrigerador', 'Estantería', 'Despensa', 'Caja']
    actions = ['IN', 'OUT']
    
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_events):
        p_id = np.random.choice(product_ids)
        action = np.random.choice(actions, p=[0.4, 0.6]) # Más salidas que entradas (consumo)
        loc = np.random.choice(locations)
        
        # Simular fecha de vencimiento (solo si entra)
        expiry = (datetime.now() + timedelta(days=np.random.randint(5, 60))).date() if action == 'IN' else None
        
        events.append({
            "event_id": f"EVT_{i:05d}",
            "product_id": p_id,
            "timestamp": start_date + timedelta(minutes=np.random.randint(1, 43200)),
            "action_type": action,
            "location": loc,
            "expiry_date": expiry
        })
    
    df_events = pd.DataFrame(events)
    os.makedirs('data/raw', exist_ok=True)
    df_events.to_csv('data/raw/movements_raw.csv', index=False)
    print("Simulación de movimientos completada y guardada en data/raw/movements_raw.csv")

if __name__ == "__main__":
    simulate_kitchen_movements('data/raw/catalog_raw.csv')