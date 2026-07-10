"""
demo_app.py — Semana 14: Demo final integrado y optimizado (Streamlit).

Interfaz de consumo minimalista y moderna orientada al usuario final.
Integra módulos de:
  1. Sugerencias Inteligentes e ideas de Recetas Anti-Desperdicio.
  2. Estado de Despensa (Gráficos de caducidad temporal y Mapa Físico Treemap).
  3. Impacto Nutricional (Distribución de Nutriscore actual).
  4. Patrones de Vida (Mapa de calor de compras).

Ejecución:
    streamlit run src/demo_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import scipy.sparse as sp
import streamlit as st

# Configuración de página minimalista y limpia
st.set_page_config(
    page_title="Smart Kitchen Intelligence",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar estado de sesión para las Familias Nuevas
if "custom_households" not in st.session_state:
    st.session_state.custom_households = {}
if "custom_id_counter" not in st.session_state:
    st.session_state.custom_id_counter = 100

sys.path.insert(0, str(Path(__file__).parent))

from cluster_profiling import format_top_categories, load_inputs as load_cluster_inputs
from recommender_hybrid import score_expiry, score_als_for_session, score_content_profile, hybrid_score
from recommender_content import build_household_profile

BASE_HOUSEHOLD_NAMES = {
    0: "Hogar Melgar Puertas 🥑",
    1: "Familia Reyna Alvarado 🍎",
    2: "Hogar Gómez Silva 🥦",
    3: "Familia Flores Medina 🥖",
    4: "Hogar Castro Rubio 🥛",
    5: "Familia Benítez Vega 🍊",
    6: "Hogar Villanueva Ríos 🍳",
    7: "Familia Paredes Luna 🥩",
    8: "Hogar Gutiérrez Solís 🍅",
    9: "Familia Espinoza Cruz 🍇"
}

@st.cache_data
def load_cached_data():
    base_dir = Path(__file__).parent.parent
    
    labels = np.load(base_dir / "data/features/cluster_labels_refined.npy")
    with open(base_dir / "data/features/feature_names.json", "r") as f:
        feat_names = json.load(f)
        
    df = pd.read_csv(base_dir / "data/processed/inventory_v1.csv", parse_dates=["timestamp", "expiry_date"])
    catalog = pd.read_csv(base_dir / "data/recommender/product_catalog.csv")
    
    art = {
        "X_items": sp.load_npz(base_dir / "data/recommender/tfidf_items.npz").toarray(),
        "Y": np.load(base_dir / "data/recommender/als_Y.npy")
    }
    
    with open(base_dir / "data/recommender/hybrid_meta.json", "r") as f:
        meta = json.load(f)
    weights_v1 = meta["weights_v1_hybrid"]
    
    G = nx.read_gexf(base_dir / "data/recommender/kitchen_graph.gexf")
    with open(base_dir / "data/recommender/graph_metrics.json", "r") as f:
        metrics = json.load(f)
        
    pagerank_by_pid = {int(k): v["pagerank"] for k, v in metrics["node_metrics"].items()}
    cluster_inputs = load_cluster_inputs()
    
    return labels, feat_names, df, catalog, art, weights_v1, G, metrics, pagerank_by_pid, cluster_inputs

def compute_hybrid_v1_live(household_id, df, catalog, X_items, Y, pagerank_by_pid, weights, ref_date):
    profile = build_household_profile(household_id, df, catalog, X_items)
    s_content = score_content_profile(profile, X_items)
    
    p = np.zeros(len(catalog))
    seed_items = df[(df["household_id"] == household_id) & (df["event_type"] == "OUT")] \
        .groupby("product_id").size().sort_values(ascending=False).head(5).index
    pid_to_idx = {pid: i for i, pid in enumerate(catalog["product_id"].tolist())}
    
    for pid in seed_items:
        if pid in pid_to_idx:
            p[pid_to_idx[pid]] = 1.0
            
    lam = 1.0
    x_sess = np.linalg.solve(Y.T @ Y + lam * np.eye(Y.shape[1]), Y.T @ p)
    s_cf = score_als_for_session(x_sess, Y)
    
    s_exp = score_expiry(household_id, df, catalog, ref_date)
    
    s_pagerank = np.zeros(len(catalog))
    for pid, val in pagerank_by_pid.items():
        if pid in pid_to_idx:
            s_pagerank[pid_to_idx[pid]] = val
            
    s_hyb = hybrid_score(s_content, s_cf, s_exp, s_pagerank, **weights, w_G=0.0)
    
    res = catalog[["product_id", "product_name", "category", "nutriscore"]].copy()
    res["score_content"] = s_content
    res["score_cf"] = s_cf
    res["score_expiry"] = s_exp
    res["score_hybrid_v1"] = s_hyb
    
    return res.sort_values("score_hybrid_v1", ascending=False)

def compute_cold_start_live(seed_pids, catalog, X_items, Y, pagerank_by_pid, weights):
    pid_to_idx = {pid: i for i, pid in enumerate(catalog["product_id"].tolist())}
    seed_idx = [pid_to_idx[pid] for pid in seed_pids if pid in pid_to_idx]

    if seed_idx:
        profile = np.asarray(X_items[seed_idx].mean(axis=0)).reshape(1, -1)
    else:
        profile = np.zeros((1, X_items.shape[1]))
    s_content = score_content_profile(profile, X_items)

    p = np.zeros(len(catalog))
    for idx in seed_idx:
        p[idx] = 1.0
    lam = 1.0
    x_sess = np.linalg.solve(Y.T @ Y + lam * np.eye(Y.shape[1]), Y.T @ p)
    s_cf = score_als_for_session(x_sess, Y)

    s_exp = np.zeros(len(catalog))
    s_pagerank = np.zeros(len(catalog))
    for pid, val in pagerank_by_pid.items():
        if pid in pid_to_idx:
            s_pagerank[pid_to_idx[pid]] = val

    s_hyb = hybrid_score(s_content, s_cf, s_exp, s_pagerank, **weights, w_G=0.0)

    res = catalog[["product_id", "product_name", "category", "nutriscore"]].copy()
    res["score_content"] = s_content
    res["score_cf"] = s_cf
    res["score_expiry"] = s_exp
    res["score_hybrid_v1"] = s_hyb

    for idx in seed_idx:
        res.loc[idx, "score_hybrid_v1"] = -999

    return res.sort_values("score_hybrid_v1", ascending=False)

labels, feat_names, df, catalog, art, weights_v1, G, metrics, pagerank_by_pid, cluster_inputs = load_cached_data()

ALL_HOUSEHOLDS = BASE_HOUSEHOLD_NAMES.copy()
for cid, data in st.session_state.custom_households.items():
    ALL_HOUSEHOLDS[cid] = data["name"]

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🧊 SKI Prototipo")
    st.write("Gestión de Inventario Inteligente y Mitigación de Desperdicio.")
    st.markdown("---")
    
    selected_name = st.selectbox(
        "👤 Selecciona la Familia:",
        options=list(ALL_HOUSEHOLDS.values())
    )
    household_id = [k for k, v in ALL_HOUSEHOLDS.items() if v == selected_name][0]
    
    st.markdown("---")
    
    with st.expander("➕ Registrar Nueva Familia"):
        st.write("Añade un nuevo hogar al ecosistema.")
        new_name = st.text_input("Nombre / Apellido de Familia:")
        
        name_to_pid = dict(zip(catalog["product_name"], catalog["product_id"]))
        product_options = catalog["product_name"].tolist()
        
        selected_seeds = st.multiselect(
            "Selecciona 3 a 5 alimentos base que tengas hoy:",
            options=product_options,
            help="Usaremos tus compras iniciales para inferir tus gustos automáticamente."
        )
        
        if st.button("Registrar y Calcular", use_container_width=True):
            if new_name and len(selected_seeds) >= 3:
                new_id = st.session_state.custom_id_counter
                st.session_state.custom_households[new_id] = {
                    "name": new_name + " ✨",
                    "seeds": [name_to_pid[n] for n in selected_seeds]
                }
                st.session_state.custom_id_counter += 1
                st.success("Familia añadida. Actualizando...")
                st.rerun()
            else:
                st.error("Por favor ingresa un nombre y al menos 3 productos semilla.")

    st.markdown("---")
    st.caption("SKI Engine v1.5 • Conectado a USDA API & Instacart Core.")

# --- CUERPO PRINCIPAL ---
st.title("📋 Estado Actual de tu Cocina Inteligente")
st.markdown(f"Monitoreo en tiempo real para el **{ALL_HOUSEHOLDS[household_id]}**")

is_cold_start = household_id >= 100

if not is_cold_start:
    ref_date = df[df["household_id"] == household_id]["timestamp"].max()
else:
    ref_date = df["timestamp"].max()

# --- EXTRACCIÓN DEL INVENTARIO VIVO PARA LOS GRÁFICOS ---
if not is_cold_start:
    df_h = df[df["household_id"] == household_id].copy()
    df_h = df_h[df_h["timestamp"] <= ref_date]
    df_h["sign"] = np.where(df_h["event_type"] == "IN", 1, -1)
    
    stock_state = df_h.groupby(["product_id", "stock_id"]).agg(
        net=("sign", "sum"),
        expiry=("expiry_date", "first"),
    ).reset_index()
    
    alive_stock = stock_state[stock_state["net"] > 0].copy()
    
    if alive_stock.empty and not df_h[df_h["event_type"] == "IN"].empty:
        last_in = df_h[df_h["event_type"] == "IN"].tail(15).copy()
        last_in["days_to_expiry"] = (last_in["expiry_date"] - ref_date).dt.days.clip(lower=0)
        alive_stock = last_in.merge(catalog[["product_id", "product_name", "category", "nutriscore"]], on="product_id", how="left")
    elif not alive_stock.empty:
        alive_stock["days_to_expiry"] = (alive_stock["expiry"] - ref_date).dt.days.clip(lower=0)
        alive_stock = alive_stock.merge(catalog[["product_id", "product_name", "category", "nutriscore"]], on="product_id", how="left")
else:
    alive_stock = pd.DataFrame() 

# Asignador dinámico de ubicaciones para el Mapa Treemap
def asignar_ubicacion(categoria):
    cat = str(categoria).lower()
    if any(x in cat for x in ["dairy", "produce", "meat", "lácteo", "queso", "fruta", "verdura", "carne", "pollo"]):
        return "Refrigerador ❄️"
    elif any(x in cat for x in ["frozen", "hielo", "congelado", "ice"]):
        return "Congelador 🧊"
    else:
        return "Alacena 🥫"

if not alive_stock.empty:
    alive_stock["Ubicación"] = alive_stock["category"].apply(asignar_ubicacion)

# --- ORGANIZACIÓN EN PESTAÑAS (TABS) ---
tab_sug, tab_inv, tab_nutri, tab_habitos, tab_tech = st.tabs([
    "💡 Sugerencias y Recetas", 
    "⏳ Estado de Despensa", 
    "🥗 Impacto Nutricional", 
    "📅 Hábitos de Compra",
    "🛠️ Auditoría Técnica"
])

# ==========================================
# PESTAÑA 1: SUGERENCIAS Y RECETAS
# ==========================================
with tab_sug:
    if not is_cold_start:
        hh_indices = df.index[df["household_id"] == household_id].tolist()
        if len(hh_indices) > 0:
            valid_labels = labels[hh_indices]
            valid_labels = valid_labels[valid_labels != -1]
            if len(valid_labels) > 0:
                dom_cluster = int(pd.Series(valid_labels).mode()[0])
                try:
                    top_cats = format_top_categories(dom_cluster, *cluster_inputs)
                    st.info(f"🥑 **Perfil de Consumo:** Enfocado principalmente en **{top_cats}**.")
                except: pass
    else:
        seed_names = catalog[catalog["product_id"].isin(st.session_state.custom_households[household_id]["seeds"])]["product_name"].tolist()
        st.success(f"🌱 Hemos mapeado tu despensa base: *{', '.join(seed_names)}*. El algoritmo ha inferido tus patrones de compra.")

    st.subheader("💡 Insumos Sugeridos para Hoy")
    
    if is_cold_start:
        reco = compute_cold_start_live(st.session_state.custom_households[household_id]["seeds"], catalog, art["X_items"], art["Y"], pagerank_by_pid, weights_v1)
    else:
        reco = compute_hybrid_v1_live(household_id, df, catalog, art["X_items"], art["Y"], pagerank_by_pid, weights_v1, ref_date)

    top5 = reco.head(5)
    columns = st.columns(5)

    for i, (_, row) in enumerate(top5.iterrows()):
        with columns[i]:
            with st.container(border=True):
                if row["score_expiry"] > 0.6 and not is_cold_start:
                    st.markdown("<p style='color:#FF4B4B; font-size:0.8rem; margin:0;'>🚨 <b>URGENTE</b></p>", unsafe_allow_html=True)
                elif row["score_cf"] > row["score_content"]:
                    st.markdown("<p style='color:#00CC99; font-size:0.8rem; margin:0;'>🔄 <b>REPOSICIÓN</b></p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#1F77B4; font-size:0.8rem; margin:0;'>✨ <b>SUGERENCIA</b></p>", unsafe_allow_html=True)
                
                st.markdown(f"<h5 style='margin-top:5px; margin-bottom:10px;'>{row['product_name']}</h5>", unsafe_allow_html=True)
                st.write(f"Nutriscore: **{row['nutriscore']}**")
                
    st.markdown("---")
    
    col_nut1, col_nut2 = st.columns(2)
    with col_nut1:
        unhealthy_items = top5[top5["nutriscore"].isin(["D", "E"])]
        if not unhealthy_items.empty:
            st.warning(f"🛑 **Sugerencia de Moderación:** Detectamos que artículos como *{', '.join(unhealthy_items['product_name'].tolist())}* tienen un índice calórico elevado. Recomendamos integrarlos de manera moderada.")
        else:
            st.success("✅ **Excelente balance nutricional:** Tus sugerencias actuales están compuestas predominantemente por insumos de alta calidad biológica (Nutriscore A/B/C).")

    with col_nut2:
        if pagerank_by_pid:
            hh_top_pr_pid = max(pagerank_by_pid, key=pagerank_by_pid.get)
            item_name = catalog[catalog["product_id"] == hh_top_pr_pid]["product_name"].values[0]
            st.info(f"🌟 **El pilar global del suministro:** El producto **{item_name}** se identifica como el núcleo transaccional del sistema. Su alta co-ocurrencia lo vuelve indispensable.")

# ==========================================
# PESTAÑA 2: ESTADO DE DESPENSA (CON TREEMAP)
# ==========================================
with tab_inv:
    st.subheader("⏳ Control de Alertas Temporales")
    if is_cold_start or alive_stock.empty:
        st.info("Añade compras a tu despensa para comenzar a rastrear las fechas de caducidad y mapas físicos.")
    else:
        col_gauge, col_gantt = st.columns([1, 2])
        
        with col_gauge:
            avg_days = alive_stock["days_to_expiry"].mean()
            health_score = min(100, max(0, (avg_days / 14) * 100))
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = health_score,
                number = {'suffix': "%"},
                title = {'text': "Índice de Frescura", 'font': {'color': 'white'}},
                gauge = {
                    'axis': {'range': [0, 100], 'tickcolor': "white"},
                    'bar': {'color': "rgba(255,255,255,0.5)"},
                    'steps': [
                        {'range': [0, 30], 'color': "#FF4B4B"},
                        {'range': [30, 70], 'color': "#FFA500"},
                        {'range': [70, 100], 'color': "#00CC99"}
                    ]}
            ))
            fig_gauge.update_layout(template="plotly_dark", margin=dict(t=50, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with col_gantt:
            plot_df = alive_stock.copy()
            def map_urgency(days):
                if days <= 2: return "Crítico"
                if days <= 5: return "Atención"
                return "Fresco"
            plot_df["Estado"] = plot_df["days_to_expiry"].apply(map_urgency)
            plot_df = plot_df.sort_values("days_to_expiry", ascending=False).tail(10)
            
            color_map = {"Crítico": "#FF4B4B", "Atención": "#FFA500", "Fresco": "#00CC99"}
            fig_bar = px.bar(
                plot_df, x="days_to_expiry", y="product_name", color="Estado",
                color_discrete_map=color_map, orientation='h',
                title="Top 10 Insumos por Caducar (Días restantes)",
                labels={"days_to_expiry": "Días", "product_name": ""}
            )
            fig_bar.update_layout(template="plotly_dark", height=300, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.subheader("🗺️ Mapa Físico de tu Cocina (Anti-Desperdicio)")
        st.write("Haz clic en una sección (Refrigerador, Congelador o Alacena) para hacer zoom y ver qué alimentos debes consumir pronto. Los cuadros más **rojos** están próximos a caducar.")
        
        # Creación del Treemap (Mapa de Cajas)
        fig_tree = px.treemap(
            alive_stock,
            path=[px.Constant("Nuestra Cocina 🏠"), "Ubicación", "product_name"],
            color="days_to_expiry",
            color_continuous_scale="RdYlGn",
            custom_data=["days_to_expiry", "nutriscore"]
        )
        
        fig_tree.update_traces(
            hovertemplate="<b>%{label}</b><br>Caduca en: %{customdata[0]} días<br>Nutriscore: %{customdata[1]}<extra></extra>",
            textinfo="label+text"
        )
        fig_tree.update_layout(template="plotly_dark", margin=dict(t=20, l=0, r=0, b=0), height=500)
        st.plotly_chart(fig_tree, use_container_width=True)

# ==========================================
# PESTAÑA 3: SALUD Y NUTRICIÓN
# ==========================================
with tab_nutri:
    st.subheader("🥗 Dashboard de Impacto Nutricional")
    
    # Ahora usamos la base de datos viva (lo que hay en el inventario AHORA) en lugar del historial.
    if is_cold_start:
        nutri_df = catalog[catalog["product_id"].isin(st.session_state.custom_households[household_id]["seeds"])]
    else:
        nutri_df = alive_stock.copy()
        
    if nutri_df.empty or "nutriscore" not in nutri_df.columns:
        st.info("No hay datos suficientes para evaluar la calidad nutricional de tu inventario actual.")
    else:
        nutri_counts = nutri_df["nutriscore"].value_counts().reset_index()
        nutri_counts.columns = ["Nutriscore", "Cantidad"]
        
        color_nutri = {"A": "#00CC99", "B": "#7CFC00", "C": "#FFD700", "D": "#FFA500", "E": "#FF4B4B"}
        
        fig_pie = px.pie(
            nutri_counts, values="Cantidad", names="Nutriscore", hole=0.4,
            color="Nutriscore", color_discrete_map=color_nutri,
            title="Distribución de Calidad Alimentaria en tu Cocina Actual"
        )
        fig_pie.update_layout(template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("Nutriscore A/B indica alta calidad biológica. D/E indica ultra-procesados que deben consumirse con moderación.")

# ==========================================
# PESTAÑA 4: HÁBITOS DE COMPRA
# ==========================================
with tab_habitos:
    st.subheader("📅 Mapa de Hábitos y Patrones de Consumo")
    if is_cold_start:
         st.info("Al ser una familia nueva, el sistema necesita registrar compras reales durante algunas semanas para construir tu mapa de calor.")
    else:
        df_in = df_h[df_h["event_type"] == "IN"].copy()
        if not df_in.empty:
            df_in["hour"] = df_in["timestamp"].dt.hour
            df_in["day_name"] = df_in["timestamp"].dt.day_name()
            
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            day_map = dict(zip(days_order, days_es))
            df_in["Día"] = df_in["day_name"].map(day_map)
            
            heatmap_data = df_in.groupby(["Día", "hour"]).size().reset_index(name="Frecuencia")
            
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_data["Frecuencia"],
                x=heatmap_data["hour"],
                y=heatmap_data["Día"],
                colorscale="Teal",
                hoverongaps=False
            ))
            # Corrección del eje X para que vaya de 0 a 23 obligatoriamente
            fig_heat.update_layout(
                template="plotly_dark",
                title="Zonas de mayor actividad de abastecimiento en la cocina",
                xaxis=dict(title="Hora del Día", tickmode='linear', dtick=1, range=[0, 23]),
                yaxis=dict(categoryorder='array', categoryarray=days_es[::-1])
            )
            st.plotly_chart(fig_heat, use_container_width=True)
            
            # Nota explicativa
            st.caption("🔍 **Cómo leer este gráfico:** Las zonas más brillantes e intensas del mapa indican los días de la semana y las horas en las que tu hogar registra compras o repone su inventario con mayor frecuencia.")
        else:
            st.info("No hay eventos registrados de compras para generar el mapa de calor.")

# ==========================================
# PESTAÑA 5: AUDITORÍA TÉCNICA
# ==========================================
with tab_tech:
    st.warning("Panel de uso exclusivo para el jurado calificador. Muestra el estado numérico crudo de los artefactos del pipeline.")
    
    t1, t2, t3 = st.tabs(["📊 Vectores Híbridos", "📈 Matriz de Co-ocurrencia", "🕸️ Visualización del Grafo Espectral"])
    
    with t1:
        st.dataframe(
            top5[["product_id", "product_name", "score_content", "score_cf", "score_expiry", "score_hybrid_v1"]]
                .style.format({"score_content": "{:.4f}", "score_cf": "{:.4f}", "score_expiry": "{:.4f}", "score_hybrid_v1": "{:.4f}"}),
            hide_index=True, use_container_width=True
        )
    with t2:
        metrics_df = pd.DataFrame.from_dict(metrics["node_metrics"], orient="index")
        st.dataframe(metrics_df, use_container_width=True)
    with t3:
        st.write("Visualización simplificada (Percentil 90 de Aristas).")
        top5_pids = [str(pid) for pid in top5["product_id"].tolist()]
        weights = [d["weight"] for u, v, d in G.edges(data=True)]
        if weights:
            threshold = np.percentile(weights, 90)
            subG = nx.Graph([(u, v, d) for u, v, d in G.edges(data=True) if d["weight"] >= threshold])
            for pid in top5_pids:
                if pid in G: subG.add_node(pid, **G.nodes[pid])
            pos = nx.spring_layout(subG, weight="weight", seed=42)
            
            edge_x, edge_y = [], []
            for edge in subG.edges():
                x0, y0 = pos[edge[0]]; x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])
            edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')
            
            node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
            for node in subG.nodes():
                x, y = pos[node]
                node_x.append(x); node_y.append(y)
                p_id = int(node)
                p_name_matches = catalog[catalog["product_id"] == p_id]["product_name"].values
                p_name = p_name_matches[0] if len(p_name_matches) > 0 else f"ID {p_id}"
                pr_val = pagerank_by_pid.get(p_id, 0.0)
                node_text.append(f"Producto: {p_name}<br>PageRank: {pr_val:.4f}")
                
                if node in top5_pids:
                    node_color.append('#FF4B4B'); node_size.append(25)
                else:
                    node_color.append('#1F77B4'); node_size.append(12)
                    
            node_trace = go.Scatter(
                x=node_x, y=node_y, mode='markers', hoverinfo='text', text=node_text,
                marker=dict(showscale=False, colorscale='YlGnBu', color=node_color, size=node_size, line_width=2)
            )
            fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(
                showlegend=False, hovermode='closest', margin=dict(b=0, l=0, r=0, t=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
            ))
            st.plotly_chart(fig, use_container_width=True)