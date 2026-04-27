import pandas as pd
import json
import uuid
import random
import os
from datetime import datetime, timedelta

# Reglas de negocio de FoodKeeper basadas en Instacart department_id
# 4: Produce (Verduras/Frutas), 16: Dairy (Lácteos), 7: Beverages, 13: Pantry
FOODKEEPER_SHELF_LIFE = {
    4: 7,    # Produce -> 7 días
    16: 10,  # Dairy eggs -> 10 días
    7: 30,   # Beverages -> 30 días
    13: 180, # Pantry -> 180 días
    19: 45,  # Snacks -> 45 días
}

def load_patterns():
    # Leer la inteligencia de negocio pre-calculada
    filepath = "data/raw/instacart_patterns.json"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Falta el archivo {filepath}. Ejecuta extract_patterns.py primero.")
        
    with open(filepath, "r") as f:
        data = json.load(f)
    return data["distribucion_horas"], data["top_50_productos"]

def run_smart_simulation(days=30):
    print("Iniciando simulación estocástica basada en Instacart y FoodKeeper...")
    hour_dist, products_pool = load_patterns()
    
    start_date = datetime(2025, 9, 1)
    inventory = []   # Lo que hay físicamente en la cocina
    movements = []   # El registro histórico de la base de datos
    
    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        
        # ---------------------------------------------------------
        # 1. EVENTO 'IN' (COMPRAS BASADAS EN HORA REAL)
        # ---------------------------------------------------------
        for hour in range(24):
            # Obtener probabilidad de esa hora específica del JSON
            prob_hour = hour_dist.get(str(hour), 0.01) 
            
            # Factor multiplicador para que ocurran compras (Ajustable)
            if random.random() < (prob_hour * 2.5): 
                # Es momento de compra. Llenamos una canasta de 2 a 6 productos
                basket_size = random.randint(2, 6)
                purchased_items = random.sample(products_pool, basket_size)
                
                timestamp = current_date.replace(hour=hour, minute=random.randint(0,59))
                
                for item in purchased_items:
                    stock_id = str(uuid.uuid4())[:8] # Lote único
                    qty = random.randint(1, 4)       # Granularidad de compra
                    
                    # Calcular caducidad basada en FoodKeeper
                    shelf_life = FOODKEEPER_SHELF_LIFE.get(item['department_id'], 14)
                    expiry = timestamp + timedelta(days=shelf_life)
                    
                    # 1A. Registrar en el inventario físico
                    inventory.append({
                        'stock_id': stock_id,
                        'product_id': item['product_id'],
                        'current_qty': qty,
                        'expiry_date': expiry
                    })
                    
                    # 1B. Escribir el log en la base de datos
                    movements.append({
                        'event_id': str(uuid.uuid4())[:10],
                        'stock_id': stock_id,
                        'product_id': item['product_id'],
                        'event_type': 'IN',
                        'quantity': qty,
                        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'expiry_date': expiry.strftime('%Y-%m-%d'),
                        'classification': 'Purchase'
                    })

        # ---------------------------------------------------------
        # 2. EVENTO 'OUT' (CONSUMO Y DESPERDICIO GRANULAR)
        # ---------------------------------------------------------
        if inventory:
            # Simulamos que en el día se consumen productos en 2-4 "Kitchen Sessions"
            for _ in range(random.randint(2, 4)):
                if not inventory: break
                
                # Consumo inteligente: El usuario intenta comer lo que vence primero
                inventory.sort(key=lambda x: x['expiry_date'])
                
                # Agarramos el producto con más riesgo
                target_item = inventory[0]
                
                # Solo consumimos 1 unidad (Depleción parcial)
                consume_qty = 1 
                target_item['current_qty'] -= consume_qty
                
                consume_time = current_date.replace(hour=random.randint(12, 20), minute=random.randint(0,59))
                
                # Etiquetado para Machine Learning: ¿Se consumió a tiempo o estaba vencido?
                is_waste = consume_time > target_item['expiry_date']
                
                movements.append({
                    'event_id': str(uuid.uuid4())[:10],
                    'stock_id': target_item['stock_id'],
                    'product_id': target_item['product_id'],
                    'event_type': 'OUT',
                    'quantity': consume_qty,
                    'timestamp': consume_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'expiry_date': target_item['expiry_date'].strftime('%Y-%m-%d'),
                    'classification': 'Waste' if is_waste else 'Consumption'
                })
                
                # Si se acabó todo el paquete, lo sacamos de la cocina
                if target_item['current_qty'] <= 0:
                    inventory.pop(0)
                    
            # ---------------------------------------------------------
            # 3. LIMPIEZA FORZADA (El usuario bota lo que lleva días podrido)
            # ---------------------------------------------------------
            for item in inventory[:]:
                # Si pasaron 2 días desde que venció, se va directo a la basura (OUT total)
                if current_date > (item['expiry_date'] + timedelta(days=2)):
                    movements.append({
                        'event_id': str(uuid.uuid4())[:10],
                        'stock_id': item['stock_id'],
                        'product_id': item['product_id'],
                        'event_type': 'OUT',
                        'quantity': item['current_qty'], # Botamos todo lo que sobra
                        'timestamp': current_date.strftime('%Y-%m-%d 23:59:59'),
                        'expiry_date': item['expiry_date'].strftime('%Y-%m-%d'),
                        'classification': 'Forced_Waste'
                    })
                    inventory.remove(item)

    # 4. Guardar resultados
    df_movements = pd.DataFrame(movements)
    os.makedirs("data/raw", exist_ok=True)
    df_movements.to_csv("data/raw/movements_raw.csv", index=False)
    print(f"✅ Éxito: Se generaron {len(df_movements)} eventos transaccionales realistas.")
    print("Muestra de los eventos:")
    print(df_movements[['event_type', 'classification', 'quantity']].value_counts().head())

if __name__ == "__main__":
    run_smart_simulation()