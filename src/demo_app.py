"""
demo_app.py — Semana 14: demo final integrado (Streamlit).

Recorre las 5 capas del proyecto para un household elegido interactivamente:
  1. Catálogo / features        → data/features/*.npy, feature_names.json
  2. Clustering (DBSCAN)         → data/features/cluster_labels_refined.npy
  3. Recomendador híbrido v1     → data/recommender/{tfidf_items,als_Y,product_catalog}
  4. Grafo de co-ocurrencia      → data/recommender/kitchen_graph.gexf, graph_metrics.json

No escribe ningún artefacto ni depende de estado oculto de notebook: cada
recarga recalcula todo desde los artefactos ya persistidos en `data/`. Debe
ejecutarse desde la raíz del repositorio (mismas rutas relativas que el resto
del pipeline):

    streamlit run src/demo_app.py

Nota metodológica sobre el cluster asignado: DBSCAN etiqueta cada EVENTO
individual (fila de `inventory_v1.csv`), no cada household. El "cluster
asignado" que se muestra aquí es la moda de las etiquetas de cluster sobre
todos los eventos del household seleccionado, es decir, su perfil de
comportamiento dominante.
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

sys.path.insert(0, str(Path(__file__).parent))
from cluster_profiling import format_top_categories, load_inputs as load_cluster_inputs, profile_cluster
from recommender_content import build_household_profile
from recommender_hybrid import (hybrid_score, score_als_for_session,
                                 score_content_profile, score_expiry, score_pagerank)

ROOT = Path(__file__).resolve().parents[1]
REC_DIR = ROOT / "data" / "recommender"
DATA_PROC = ROOT / "data" / "processed" / "inventory_v1.csv"

REQUIRED_FILES = [
    DATA_PROC,
    ROOT / "data" / "features" / "cluster_labels_refined.npy",
    ROOT / "data" / "features" / "feature_matrix.npy",
    ROOT / "data" / "features" / "feature_names.json",
    REC_DIR / "product_catalog.csv",
    REC_DIR / "tfidf_items.npz",
    REC_DIR / "als_Y.npy",
    REC_DIR / "kitchen_graph.gexf",
]

st.set_page_config(page_title="SKI — Demo Final (Semana 14)", layout="wide")


def _check_artifacts() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED_FILES if not p.exists()]
    if missing:
        st.error(
            "Faltan artefactos requeridos (ejecuta el pipeline en el orden de `runbook.md`):\n\n"
            + "\n".join(f"- `{m}`" for m in missing)
        )
        st.stop()


@st.cache_data(show_spinner="Cargando artefactos del pipeline...")
def load_artifacts():
    df = pd.read_csv(DATA_PROC, parse_dates=["timestamp", "expiry_date"])
    catalog = pd.read_csv(REC_DIR / "product_catalog.csv")
    X_items = sp.load_npz(REC_DIR / "tfidf_items.npz")
    Y = np.load(REC_DIR / "als_Y.npy")
    graph = nx.read_gexf(REC_DIR / "kitchen_graph.gexf")
    labels, X_feat, feature_names, cluster_inventory = load_cluster_inputs()

    graph_metrics_path = REC_DIR / "graph_metrics.json"
    pagerank_by_pid = {}
    if graph_metrics_path.exists():
        with open(graph_metrics_path, "r", encoding="utf-8") as f:
            g_metrics = json.load(f)
        pagerank_by_pid = {
            int(pid_str) if pid_str.isdigit() else pid_str: m.get("pagerank", 0.0)
            for pid_str, m in g_metrics.get("node_metrics", {}).items()
        }

    hybrid_meta_path = REC_DIR / "hybrid_meta.json"
    weights_v1 = {"w_C": 0.35, "w_F": 0.45, "w_E": 0.20, "w_G": 0.0}
    if hybrid_meta_path.exists():
        with open(hybrid_meta_path, "r", encoding="utf-8") as f:
            hybrid_meta = json.load(f)
        weights_v1.update(hybrid_meta.get("weights_v1_hybrid", {}))

    return {
        "df": df, "catalog": catalog, "X_items": X_items, "Y": Y, "graph": graph,
        "labels": labels, "X_feat": X_feat, "feature_names": feature_names,
        "cluster_inventory": cluster_inventory, "pagerank_by_pid": pagerank_by_pid,
        "weights_v1": weights_v1,
    }


@st.cache_data(show_spinner=False)
def compute_graph_layout(_graph: nx.Graph):
    return nx.spring_layout(_graph, weight="weight", seed=42)


def assigned_cluster_for_household(household_id: int, labels: np.ndarray,
                                   cluster_inventory: pd.DataFrame) -> int:
    mask_hh = (cluster_inventory["household_id"] == household_id).to_numpy()
    hh_labels = labels[mask_hh]
    counts = pd.Series(hh_labels).value_counts()
    for cluster_id in counts.index:
        if cluster_id != -1:
            return int(cluster_id)
    return int(counts.index[0])  # todos los eventos del household cayeron en ruido


@st.cache_data(show_spinner=False)
def compute_hybrid_v1(household_id: int, _df: pd.DataFrame, _catalog: pd.DataFrame,
                       _X_items: sp.csr_matrix, _Y: np.ndarray,
                       pagerank_by_pid: dict, weights_v1: dict, ref_date) -> pd.DataFrame:
    profile_vec = build_household_profile(household_id, _df, _catalog, _X_items)

    pid_to_idx = {pid: i for i, pid in enumerate(_catalog["product_id"].tolist())}
    seed_items = (_df[(_df["household_id"] == household_id) & (_df["event_type"] == "OUT")]
                  .groupby("product_id").size().sort_values(ascending=False).head(5).index)
    p = np.zeros(len(_catalog))
    for pid in seed_items:
        if pid in pid_to_idx:
            p[pid_to_idx[pid]] = 1.0
    lam = 1.0
    x_sess = np.linalg.solve(_Y.T @ _Y + lam * np.eye(_Y.shape[1]), _Y.T @ p)

    s_content = score_content_profile(profile_vec, _X_items)
    s_cf = score_als_for_session(x_sess, _Y)
    s_exp = score_expiry(household_id, _df, _catalog, ref_date)
    s_pagerank = score_pagerank(_catalog)

    s_hyb = hybrid_score(s_content, s_cf, s_exp, s_pagerank,
                         w_C=weights_v1["w_C"], w_F=weights_v1["w_F"],
                         w_E=weights_v1["w_E"], w_G=weights_v1.get("w_G", 0.0))

    result = _catalog[["product_id", "product_name", "category", "nutriscore"]].copy()
    result["score_content"] = s_content
    result["score_cf"] = s_cf
    result["score_expiry"] = s_exp
    result["score_hybrid_v1"] = s_hyb
    return result.sort_values("score_hybrid_v1", ascending=False).reset_index(drop=True)


def render_network(graph: nx.Graph, pos: dict, top5_pids: list[str],
                   pid_to_name: dict, pagerank_by_pid: dict) -> go.Figure:
    weights = [d["weight"] for _, _, d in graph.edges(data=True)]
    threshold = float(np.quantile(weights, 0.90))
    top5_set = set(top5_pids)

    ctx_x, ctx_y = [], []
    for u, v, d in graph.edges(data=True):
        if d["weight"] >= threshold and u not in top5_set and v not in top5_set:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            ctx_x += [x0, x1, None]
            ctx_y += [y0, y1, None]

    hi_x, hi_y = [], []
    for u, v in graph.edges():
        if u in top5_set and v in top5_set:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            hi_x += [x0, x1, None]
            hi_y += [y0, y1, None]

    all_nodes = list(graph.nodes())
    bg_nodes = [n for n in all_nodes if n not in top5_set]

    def node_hover(n: str) -> str:
        pid = int(n) if n.isdigit() else n
        name = pid_to_name.get(pid, n)
        pr = pagerank_by_pid.get(pid, 0.0)
        return f"{name} (id {n})<br>PageRank: {pr:.4f}"

    ctx_edge_trace = go.Scatter(x=ctx_x, y=ctx_y, mode="lines",
                                line=dict(width=0.6, color="rgba(140,140,150,0.35)"),
                                hoverinfo="skip", showlegend=False)
    hi_edge_trace = go.Scatter(x=hi_x, y=hi_y, mode="lines",
                               line=dict(width=2.5, color="rgba(220,20,60,0.75)"),
                               hoverinfo="skip", showlegend=False)
    bg_node_trace = go.Scatter(
        x=[pos[n][0] for n in bg_nodes], y=[pos[n][1] for n in bg_nodes],
        mode="markers", marker=dict(size=9, color="#8899aa", line=dict(width=0.5, color="white")),
        text=[node_hover(n) for n in bg_nodes], hoverinfo="text", showlegend=False,
    )
    hi_node_trace = go.Scatter(
        x=[pos[n][0] for n in top5_pids], y=[pos[n][1] for n in top5_pids],
        mode="markers+text",
        marker=dict(size=24, color="crimson", line=dict(width=1.5, color="white")),
        text=[pid_to_name.get(int(n) if n.isdigit() else n, n) for n in top5_pids],
        textposition="top center",
        hovertext=[node_hover(n) for n in top5_pids], hoverinfo="text", showlegend=False,
    )

    fig = go.Figure(data=[ctx_edge_trace, hi_edge_trace, bg_node_trace, hi_node_trace])
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0), height=560,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def main() -> None:
    st.title("Smart Kitchen Intelligence — Demo Final (Semana 14)")
    st.caption(
        "Integra clustering (DBSCAN, Hito 3), recomendación híbrida (Hito 4) y el grafo de "
        "co-ocurrencia con PageRank (Hito 5) para un household elegido interactivamente. "
        "Todo se recalcula en vivo a partir de artefactos en `data/` — sin estado oculto."
    )

    _check_artifacts()
    art = load_artifacts()
    df, catalog = art["df"], art["catalog"]
    labels, X_feat, feature_names = art["labels"], art["X_feat"], art["feature_names"]
    cluster_inventory, graph = art["cluster_inventory"], art["graph"]
    pagerank_by_pid, weights_v1 = art["pagerank_by_pid"], art["weights_v1"]

    households = sorted(df["household_id"].unique().tolist())
    household_id = st.sidebar.selectbox("Household", households, index=0)
    st.sidebar.markdown(
        f"**Pesos híbrido v1 (producción):**\n\n"
        f"w_C={weights_v1['w_C']:.2f} · w_F={weights_v1['w_F']:.2f} · "
        f"w_E={weights_v1['w_E']:.2f} · w_G={weights_v1.get('w_G', 0.0):.2f}\n\n"
        "_(ganador de la ablación 4D — ver `reports/graph_analytics_report.md` §5)_"
    )

    ref_date = df["timestamp"].max()
    pid_to_name = dict(zip(catalog["product_id"], catalog["product_name"]))

    col_cluster, col_reco = st.columns([1, 1.4])

    with col_cluster:
        st.subheader(f"Perfil de comportamiento — Household {household_id}")
        assigned_cluster = assigned_cluster_for_household(household_id, labels, cluster_inventory)
        mask_hh = (cluster_inventory["household_id"] == household_id).to_numpy()
        n_hh_events = int(mask_hh.sum())
        n_hh_in_cluster = int((labels[mask_hh] == assigned_cluster).sum())

        if assigned_cluster == -1:
            st.warning("La mayoría de los eventos de este household cayeron en ruido DBSCAN (label -1).")
        else:
            global_mean = X_feat.mean(axis=0)
            mask_cluster = labels == assigned_cluster
            profile = profile_cluster(assigned_cluster, mask_cluster, X_feat, feature_names,
                                      cluster_inventory, global_mean)

            st.metric("Cluster asignado (moda)", f"#{assigned_cluster}")
            st.caption(
                f"{n_hh_in_cluster}/{n_hh_events} eventos de este household "
                f"({n_hh_in_cluster / max(n_hh_events, 1) * 100:.1f}%) caen en este cluster."
            )
            st.markdown(
                f"- **Tamaño del cluster:** {profile['n']} eventos ({profile['pct_total']:.2f}% del total)\n"
                f"- **Categorías dominantes:** {format_top_categories(profile['top_categories'])}\n"
                f"- **Feature más distintivo:** `{profile['top_feature']}` "
                f"(Δ={profile['top_feature_dev']:+.2f} vs. media global)\n"
                f"- **Hora media:** {profile['mean_hour']:.1f}h — **Día dominante:** {profile['dominant_day']}"
            )
            st.caption("Perfil completo por cluster: `reports/cluster_profiles.md` (`src/cluster_profiling.py`).")

    with col_reco:
        st.subheader("Top-5 recomendaciones — Híbrido v1 (producción)")
        reco = compute_hybrid_v1(household_id, df, catalog, art["X_items"], art["Y"],
                                 pagerank_by_pid, weights_v1, ref_date)
        top5 = reco.head(5)
        st.dataframe(
            top5[["product_id", "product_name", "category", "nutriscore", "score_hybrid_v1"]]
                .style.format({"score_hybrid_v1": "{:.4f}"}),
            hide_index=True, use_container_width=True,
        )
        with st.expander("Desglose por componente (contenido / CF / expiry)"):
            st.dataframe(
                top5[["product_name", "score_content", "score_cf", "score_expiry"]]
                    .style.format({"score_content": "{:.3f}", "score_cf": "{:.3f}", "score_expiry": "{:.3f}"}),
                hide_index=True, use_container_width=True,
            )

    st.subheader("Grafo de co-ocurrencia — top-5 recomendados resaltados")
    st.caption(
        "Layout por fuerzas (spring layout, ponderado por co-ocurrencia). Se muestran solo las "
        "aristas más fuertes (percentil 90) como contexto estructural — el grafo completo es "
        "denso (50 nodos, 1,225 aristas, ver `reports/graph_analytics_report.md`) y dibujarlo "
        "entero produciría una maraña ilegible."
    )
    top5_pids = [str(pid) for pid in top5["product_id"].tolist()]
    pos = compute_graph_layout(graph)
    fig = render_network(graph, pos, top5_pids, pid_to_name, pagerank_by_pid)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
