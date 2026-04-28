import pandas as pd
import json
import uuid
import random
import os
from datetime import datetime, timedelta

# Configuración de Negocio: Shelf Life por Departamento (USDA/FoodKeeper)
FOODKEEPER_SHELF_LIFE = {
    4: 7,    # Produce (Frutas/Verduras)
    16: 12,  # Dairy (Lácteos)
    7: 30,   # Beverages (Bebidas)
    13: 120, # Pantry (Despensa)
    19: 45,  # Snacks
}

def load_patterns():
    """Carga los patrones probabilísticos de Instacart."""
    filepath = "data/raw/instacart_patterns.json"
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Falta el archivo {filepath}. Ejecuta extract_patterns.py primero.")
        
    with open(filepath, "r") as f:
        data = json.load(f)
    return data["distribucion_horas"], data["top_50_productos"]

def run_massive_simulation(num_households=10, days=90):
    """
    Simula múltiples hogares para generar un volumen de datos robusto (Escala Horizontal).
    """
    print(f"🚀 Iniciando simulación masiva: {num_households} hogares durante {days} días...")
    
    hour_dist, products_pool = load_patterns()
    movements = []
    
    # Referencia temporal: 90 días atrás desde hoy
    base_start_date = datetime.now() - timedelta(days=days)

    for h_id in range(num_households):
        print(f"🏠 Simulando Hogar ID: {h_id}...")
        inventory = [] # Cada hogar tiene su propio inventario independiente
        
        for d in range(days):
            current_date = base_start_date + timedelta(days=d)
            
            for hour in range(24):
                prob_purchase = hour_dist.get(str(hour), 0.05)
                
                # ---------------------------------------------------------
                # 1. EVENTOS DE ENTRADA (COMPRAS)
                # ---------------------------------------------------------
                if random.random() < (prob_purchase * 1.5): # Factor de escala para compras
                    # Simula una canasta de 5 a 12 productos
                    for _ in range(random.randint(5, 12)):
                        prod = random.choice(products_pool)
                        dept = prod['department_id']
                        shelf_life = FOODKEEPER_SHELF_LIFE.get(dept, 14)
                        
                        expiry = current_date + timedelta(days=shelf_life)
                        stock_id = str(uuid.uuid4())[:8]
                        qty = random.randint(1, 3)
                        
                        item_entry = {
                            'event_id': str(uuid.uuid4())[:10],
                            'household_id': h_id, # Nueva columna de dimensión social
                            'stock_id': stock_id,
                            'product_id': prod['product_id'],
                            'product_name': prod['product_name'],
                            'event_type': 'IN',
                            'quantity': qty,
                            'timestamp': current_date.replace(hour=hour, minute=random.randint(0,59)).strftime('%Y-%m-%d %H:%M:%S'),
                            'expiry_date': expiry.strftime('%Y-%m-%d'),
                            'classification': 'Purchase'
                        }
                        movements.append(item_entry)
                        
                        # Agregar al inventario local del hogar para seguimiento
                        inventory.append({
                            'stock_id': stock_id,
                            'product_id': prod['product_id'],
                            'expiry_date': expiry,
                            'current_qty': qty
                        })

                # ---------------------------------------------------------
                # 2. EVENTOS DE SALIDA (CONSUMO/DESPERDICIO)
                # ---------------------------------------------------------
                # Probabilidad de que el hogar use la cocina en esta hora
                if inventory and random.random() < 0.25:
                    # Selecciona 1-3 items del inventario para consumir
                    items_to_use = random.sample(inventory, min(len(inventory), random.randint(1, 3)))
                    
                    for item in items_to_use:
                        use_qty = random.randint(1, item['current_qty'])
                        item['current_qty'] -= use_qty
                        
                        is_waste = current_date > item['expiry_date']
                        
                        movements.append({
                            'event_id': str(uuid.uuid4())[:10],
                            'household_id': h_id,
                            'stock_id': item['stock_id'],
                            'product_id': item['product_id'],
                            'product_name': next(p['product_name'] for p in products_pool if p['product_id'] == item['product_id']),
                            'event_type': 'OUT',
                            'quantity': use_qty,
                            'timestamp': current_date.replace(hour=hour, minute=random.randint(0,59)).strftime('%Y-%m-%d %H:%M:%S'),
                            'expiry_date': item['expiry_date'].strftime('%Y-%m-%d'),
                            'classification': 'Waste' if is_waste else 'Consumption'
                        })
                        
                        if item['current_qty'] <= 0:
                            inventory.remove(item)

            # ---------------------------------------------------------
            # 3. LIMPIEZA FORZADA AL FINAL DEL DÍA
            # ---------------------------------------------------------
            for item in inventory[:]:
                # Si pasaron 2 días desde el vencimiento, limpieza automática
                if current_date > (item['expiry_date'] + timedelta(days=2)):
                    movements.append({
                        'event_id': str(uuid.uuid4())[:10],
                        'household_id': h_id,
                        'stock_id': item['stock_id'],
                        'product_id': item['product_id'],
                        'product_name': next(p['product_name'] for p in products_pool if p['product_id'] == item['product_id']),
                        'event_type': 'OUT',
                        'quantity': item['current_qty'],
                        'timestamp': current_date.strftime('%Y-%m-%d 23:59:59'),
                        'expiry_date': item['expiry_date'].strftime('%Y-%m-%d'),
                        'classification': 'Forced_Waste'
                    })
                    inventory.remove(item)

    # 4. Guardar resultados consolidados
    df_movements = pd.DataFrame(movements)
    os.makedirs("data/raw", exist_ok=True)
    df_movements.to_csv("data/raw/movements_raw.csv", index=False)
    
    print(f"\n✅ ¡Éxito! Se generaron {len(df_movements)} eventos transaccionales.")
    print(f"📊 Volumen final: {df_movements.memory_usage().sum() / 1024**2:.2f} MB en disco.")
    print(df_movements['classification'].value_counts())

if __name__ == "__main__":
    # Ajustamos a 10 hogares y 90 días para garantizar > 15,000 filas
    run_massive_simulation(num_households=10, days=90)