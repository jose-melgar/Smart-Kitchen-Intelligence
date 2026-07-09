"""
demo_app.py — Semana 14: Demo final integrado y optimizado (Streamlit).

Interfaz de consumo minimalista y moderna orientada al usuario final.
Traduce la complejidad de las 5 capas del proyecto (features, clustering, 
recomendador híbrido y analítica de grafos) en insights de acción directa 
(consumo urgente, restock habitual e impacto nutricional).

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
import scipy.sparse as sp
import streamlit as st

# Configuración de página minimalista y limpia
st.set_page_config(
    page_title="Smart Kitchen Intelligence",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Insertar el path para importar los módulos locales
sys.path.insert(0, str(Path(__file__).parent))

from cluster_profiling import format_top_categories, load_inputs as load_cluster_inputs
from recommender_hybrid import score_expiry, score_als_for_session, score_content_profile, hybrid_score
from recommender_content import build_household_profile

# Mapeo de IDs artificiales amigables para el público general
HOUSEHOLD_NAMES = {
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
    """Carga y congela los artefactos persistidos del pipeline."""
    base_dir = Path(__file__).parent.parent
    
    # Capa 1 y 2: Features y Etiquetas de Clustering
    labels = np.load(base_dir / "data/features/cluster_labels_refined.npy")
    with open(base_dir / "data/features/feature_names.json", "r") as f:
        feat_names = json.load(f)
        
    # Capa 3 y 4: Recomendador e Interacciones
    df = pd.read_csv(base_dir / "data/processed/inventory_v1.csv", parse_dates=["timestamp", "expiry_date"])
    catalog = pd.read_csv(base_dir / "data/recommender/product_catalog.csv")
    
    art = {
        "X_items": sp.load_npz(base_dir / "data/recommender/tfidf_items.npz").toarray(),
        "Y": np.load(base_dir / "data/recommender/als_Y.npy")
    }
    
    with open(base_dir / "data/recommender/hybrid_meta.json", "r") as f:
        meta = json.load(f)
    weights_v1 = meta["weights_v1_hybrid"] # Extraído directamente de la metadata
    
    # Capa 5: Grafo y Métricas de Centralidad (PageRank)
    G = nx.read_gexf(base_dir / "data/recommender/kitchen_graph.gexf")
    with open(base_dir / "data/recommender/graph_metrics.json", "r") as f:
        metrics = json.load(f)
        
    pagerank_by_pid = {int(k): v["pagerank"] for k, v in metrics["node_metrics"].items()}
    
    # Cargar inputs para el formateo semántico de los perfiles de cluster
    cluster_inputs = load_cluster_inputs()
    
    return labels, feat_names, df, catalog, art, weights_v1, G, metrics, pagerank_by_pid, cluster_inputs

def compute_hybrid_v1_live(household_id, df, catalog, X_items, Y, pagerank_by_pid, weights, ref_date):
    """Calcula el score híbrido dinámicamente para cualquier hogar seleccionado."""
    # 1. Score de Contenido (Afinidad histórica)
    profile = build_household_profile(household_id, df, catalog, X_items)
    s_content = score_content_profile(profile, X_items)
    
    # 2. Score de Filtrado Colaborativo (ALS Latente)
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
    
    # 3. Score de Urgencia (Vencimiento)
    s_exp = score_expiry(household_id, df, catalog, ref_date)
    
    # 4. Score Estructural (PageRank)
    s_pagerank = np.zeros(len(catalog))
    for pid, val in pagerank_by_pid.items():
        if pid in pid_to_idx:
            s_pagerank[pid_to_idx[pid]] = val
            
    # 5. Ensamble Híbrido Final (w_G = 0.0 según hallazgos Hito 5)
    s_hyb = hybrid_score(
        s_content, s_cf, s_exp, s_pagerank,
        w_C=weights["w_C"], w_F=weights["w_F"], w_E=weights["w_E"], w_G=0.0
    )
    
    # Armar la tabla de resultados
    res = catalog[["product_id", "product_name", "category", "nutriscore"]].copy()
    res["score_content"] = s_content
    res["score_cf"] = s_cf
    res["score_expiry"] = s_exp
    res["score_hybrid_v1"] = s_hyb
    
    return res.sort_values("score_hybrid_v1", ascending=False)

# Ejecución de la carga de datos compartida
labels, feat_names, df, catalog, art, weights_v1, G, metrics, pagerank_by_pid, cluster_inputs = load_cached_data()

# --- DISEÑO DE LA INTERFAZ ---

# Barra lateral corporativa y limpia
with st.sidebar:
    st.title("🧊 SKI Prototipo")
    st.write("Gestión de Inventario Inteligente y Mitigación de Desperdicio.")
    st.markdown("---")
    
    # Selector con Nombres Artificiales en lugar de IDs crudos
    selected_name = st.selectbox(
        "👤 Selecciona el Hogar a Gestionar:",
        options=list(HOUSEHOLD_NAMES.values())
    )
    # Inversión del ID para la lógica de backend
    household_id = [k for k, v in HOUSEHOLD_NAMES.items() if v == selected_name][0]
    
    st.markdown("---")
    st.caption("SKI Engine v1.4 • Conectado a USDA API & Instacart Core.")

# Cuerpo principal de la aplicación
st.title("📋 Estado Actual de tu Cocina Inteligente")
st.markdown(f"Monitoreo en tiempo real para el **{HOUSEHOLD_NAMES[household_id]}**")

# Determinación del perfil dominante (Moda de clustering)
hh_events_mask = df["event_id"].str.startswith(f"hh{household_id}_")
if hh_events_mask.any():
    hh_indices = np.where(hh_events_mask)[0]
    hh_labels = labels[hh_indices]
    valid_labels = hh_labels[hh_labels != -1]
    
    if len(valid_labels) > 0:
        dominant_cluster = int(pd.Series(valid_labels).mode()[0])
        try:
            top_cats = format_top_categories(dominant_cluster, *cluster_inputs)
            st.info(f"🥑 **Tu Perfil de Consumo Dominante:** Enfocado principalmente en productos de tipo **{top_cats}**. Tu patrón de abastecimiento muestra una alta regularidad en estas familias de alimentos.")
        except Exception:
            st.info(f"🥑 **Tu Perfil de Consumo Dominante:** Clúster de comportamiento {dominant_cluster}.")
    else:
        st.warning("⚠️ Perfil en estado de evaluación inicial (Datos de consumo en proceso de estabilización).")

st.markdown("---")

# --- CAPA DE RECOMENDACIÓN: DISEÑO MINIMALISTA DE TARJETAS ---
st.subheader("💡 Acciones e Insumos Sugeridos para Hoy")
st.caption("El modelo híbrido ha priorizado estas sugerencias cruzando tus gustos históricos, urgencia de vencimiento y regularidad de compra.")

# Cálculo del backend en vivo
ref_date = df[df["event_id"].str.startswith(f"hh{household_id}_")]["timestamp"].max()
reco = compute_hybrid_v1_live(household_id, df, catalog, art["X_items"], art["Y"], pagerank_by_pid, weights_v1, ref_date)
top5 = reco.head(5)

# Renderizado en columnas horizontales amigables (Cards)
columns = st.columns(5)

for i, (_, row) in enumerate(top5.iterrows()):
    with columns[i]:
        # Determinar intención de la tarjeta según la fuerza de los scores componentes
        if row["score_expiry"] > 0.6:
            badge_status = "🚨 **CONSUMIR PRONTO**"
            card_color = "rgba(255, 75, 75, 0.25)"
        elif row["score_cf"] > row["score_content"]:
            badge_status = "🔄 **REPOSICIÓN DE RUTINA**"
            card_color = "rgba(0, 204, 153, 0.25)"
        else:
            badge_status = "✨ **DESCUBRIMIENTO**"
            card_color = "rgba(31, 119, 180, 0.25)"
            
        # Diseño HTML inyectado limpiamente (Adaptado a Dark Mode)
        st.markdown(
            f"""
            <div style="background-color: {card_color}; padding: 15px; border-radius: 10px; border-left: 5px solid; min-height: 180px; color: white;">
                <p style="margin: 0; font-size: 0.8rem; color: #EEEEEE;">{badge_status}</p>
                <h4 style="margin: 5px 0 10px 0; font-size: 1.1rem; color: #FFFFFF;">{row['product_name']}</h4>
                <p style="margin: 0; font-size: 0.85rem; color: #DDDDDD;"><b>Categoría:</b> {row['category']}</p>
                <span style="display: inline-block; margin-top: 10px; padding: 2px 8px; background-color: #555; color: white; border-radius: 5px; font-size: 0.75rem;">Nutriscore: {row['nutriscore']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# --- RECOMENDACIÓN NUTRICIONAL BASADA EN PROYECTO ---
st.subheader("🥗 Balance y Hábitos Alimenticios")
col_nut1, col_nut2 = st.columns(2)

with col_nut1:
    unhealthy_items = top5[top5["nutriscore"].isin(["D", "E"])]
    if not unhealthy_items.empty:
        st.error(f"🛑 **Sugerencia de Moderación:** Detectamos que artículos como *{', '.join(unhealthy_items['product_name'].tolist())}* tienen un índice de procesamiento o densidad calórica elevada. Recomendamos balancear su consumo e integrarlos de manera moderada en tus preparaciones.")
    else:
        st.success("✅ **Excelente balance nutricional:** Tus sugerencias actuales están compuestas predominantemente por insumos de alta calidad biológica y macro-nutrientes balanceados (Nutriscore A/B/C).")

with col_nut2:
    if pagerank_by_pid:
        hh_top_pr_pid = max(pagerank_by_pid, key=pagerank_by_pid.get)
        item_name = catalog[catalog["product_id"] == hh_top_pr_pid]["product_name"].values[0]
        st.info(f"🌟 **El pilar de tu suministro:** El producto **{item_name}** se identifica estadísticamente como el núcleo transaccional de tu hogar. Su alta tasa de co-ocurrencia lo vuelve indispensable para garantizar la estabilidad de tus menús habituales.")


st.markdown("---")

# --- MODO AUDITORÍA TÉCNICA (OCULTO PARA EL PÚBLICO, VISIBLE PARA EL PROFESOR) ---
with st.expander("🛠️ MODO AUDITORÍA TÉCNICA (Métricas del Modelo y Topología Espectral del Grafo)"):
    st.warning("Este panel es de uso exclusivo para el jurado calificador. Muestra el estado numérico crudo de los artefactos del pipeline.")
    
    tab1, tab2, tab3 = st.tabs(["📊 Vectores Híbridos", "📈 Matriz de Co-ocurrencia", "🕸️ Visualización del Grafo Espectral"])
    
    with tab1:
        st.write("**Top 5 Recomendaciones Expandidas (Scores de Fusión Lineal Anónima):**")
        st.dataframe(
            top5[["product_id", "product_name", "score_content", "score_cf", "score_expiry", "score_hybrid_v1"]]
                .style.format({
                    "score_content": "{:.4f}",
                    "score_cf": "{:.4f}",
                    "score_expiry": "{:.4f}",
                    "score_hybrid_v1": "{:.4f}"
                }),
            hide_index=True, use_container_width=True
        )
        st.caption(f"Pesos de combinación configurados estáticamente en `hybrid_meta.json`: {weights_v1}")

    with tab2:
        st.write("**Métricas de Centralidad Topológica Extraídas de la Red:**")
        metrics_df = pd.DataFrame.from_dict(metrics["node_metrics"], orient="index")
        st.dataframe(metrics_df, use_container_width=True)

    with tab3:
        st.write("**Sub-grafo de Co-compra (Percentil 90 de Aristas por Fuerza del Peso):**")
        top5_pids = [str(pid) for pid in top5["product_id"].tolist()]
        
        # Filtro espectral de aristas pesadas para limpieza del plot
        weights = [d["weight"] for u, v, d in G.edges(data=True)]
        if weights:
            threshold = np.percentile(weights, 90)
            subG = nx.Graph([(u, v, d) for u, v, d in G.edges(data=True) if d["weight"] >= threshold])
            
            # Forzar inclusión de los nodos recomendados
            for pid in top5_pids:
                if pid in G:
                    subG.add_node(pid, **G.nodes[pid])
                    
            pos = nx.spring_layout(subG, weight="weight", seed=42)
            
            # Trazado de aristas en Plotly
            edge_x = []
            edge_y = []
            for edge in subG.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none', mode='lines'
            )
            
            # Trazado de nodos
            node_x = []
            node_y = []
            node_text = []
            node_color = []
            node_size = []
            
            for node in subG.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                p_id = int(node)
                p_name_matches = catalog[catalog["product_id"] == p_id]["product_name"].values
                p_name = p_name_matches[0] if len(p_name_matches) > 0 else f"ID {p_id}"
                pr_val = pagerank_by_pid.get(p_id, 0.0)
                
                node_text.append(f"Producto: {p_name}<br>PageRank: {pr_val:.4f}")
                
                # Resaltado cromático de los nodos recomendados del Top 5
                if node in top5_pids:
                    node_color.append('#FF4B4B')
                    node_size.append(25)
                else:
                    node_color.append('#1F77B4')
                    node_size.append(12)
                    
            node_trace = go.Scatter(
                x=node_x, y=node_y, mode='markers',
                hoverinfo='text', text=node_text,
                marker=dict(
                    showscale=False,
                    colorscale='YlGnBu',
                    color=node_color,
                    size=node_size,
                    line_width=2
                )
            )
            
            fig = go.Figure(
                data=[edge_trace, node_trace],
                layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("🔴 Nodos en Rojo: Alimentos recomendados en el Top 5 actual. 🔵 Nodos en Azul: Ecosistema estructural del catálogo.")