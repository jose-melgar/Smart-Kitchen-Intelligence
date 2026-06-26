"""
generate_hito5_figures.py — Genera las figuras del informe del Hito 5.

Produce 4 visualizaciones en reports/figures/hito5/:
  1. graph_network.png      — Red de co-ocurrencia con PageRank como tamaño de nodo
  2. degree_distribution.png — Distribución de grado ponderado
  3. pagerank_bar.png        — Top-15 productos por centralidad PageRank
  4. system_comparison.png   — Comparativa de los 5 sistemas de evaluación
"""

import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "data" / "recommender"
FIG_DIR = ROOT / "reports" / "figures" / "hito5"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ---------- cargar datos ----------
G = nx.read_gexf(REC / "kitchen_graph.gexf")
with open(REC / "graph_metrics.json", "r", encoding="utf-8") as f:
    metrics = json.load(f)
catalog = pd.read_csv(REC / "product_catalog.csv")
pid_to_name = dict(zip(catalog["product_id"].astype(str), catalog["product_name"]))

eval_table = pd.read_csv(REC / "evaluation_table.csv")

# ===================================================================
# Figura 1: Red de co-ocurrencia
# ===================================================================
fig, ax = plt.subplots(figsize=(10, 10))
pos = nx.spring_layout(G, seed=42, k=0.35)

pageranks = nx.pagerank(G, weight="weight")
node_sizes = [pageranks.get(n, 0.02) * 15000 for n in G.nodes()]

w_degrees = dict(G.degree(weight="weight"))
max_wd = max(w_degrees.values())
min_wd = min(w_degrees.values())
node_colors = [(w_degrees[n] - min_wd) / (max_wd - min_wd) for n in G.nodes()]

edge_weights = [G[u][v].get("weight", 1) for u, v in G.edges()]
max_ew = max(edge_weights) if edge_weights else 1
edge_widths = [0.3 + 2.0 * w / max_ew for w in edge_weights]
edge_alphas = [0.08 + 0.25 * w / max_ew for w in edge_weights]

nx.draw_networkx_edges(G, pos, ax=ax, width=edge_widths,
                       alpha=0.15, edge_color="gray")
nodes = nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes,
                               node_color=node_colors, cmap=plt.cm.YlOrRd,
                               edgecolors="black", linewidths=0.5)

labels = {n: pid_to_name.get(n, n)[:12] for n in G.nodes()}
nx.draw_networkx_labels(G, pos, labels, font_size=6, ax=ax)

ax.set_title("Red de Co-ocurrencia de Productos\n(tamaño = PageRank, color = grado ponderado)",
             fontsize=13, fontweight="bold")
plt.colorbar(nodes, ax=ax, label="Grado ponderado (normalizado)", shrink=0.7)
ax.axis("off")
fig.tight_layout()
fig.savefig(FIG_DIR / "graph_network.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"[OK] graph_network.png")

# ===================================================================
# Figura 2: Distribución de grado ponderado
# ===================================================================
fig, ax = plt.subplots(figsize=(8, 4.5))
wd_vals = sorted(w_degrees.values())
ax.bar(range(len(wd_vals)), wd_vals, color="#4C78A8", edgecolor="white", linewidth=0.3)
ax.set_xlabel("Producto (ordenado por grado ponderado)", fontsize=11)
ax.set_ylabel("Grado ponderado (frecuencia de co-compra)", fontsize=11)
ax.set_title("Distribución de Grado Ponderado en la Red", fontsize=13, fontweight="bold")
ax.axhline(np.mean(wd_vals), color="red", linestyle="--", linewidth=1, label=f"Media = {np.mean(wd_vals):.0f}")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(FIG_DIR / "degree_distribution.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"[OK] degree_distribution.png")

# ===================================================================
# Figura 3: Top-15 productos por PageRank
# ===================================================================
pr_sorted = sorted(pageranks.items(), key=lambda x: x[1], reverse=True)[:15]
names = [pid_to_name.get(pid, pid)[:20] for pid, _ in pr_sorted]
scores = [s for _, s in pr_sorted]

fig, ax = plt.subplots(figsize=(8, 5.5))
colors = plt.cm.YlOrRd(np.linspace(0.4, 0.9, len(names)))
bars = ax.barh(range(len(names)), scores, color=colors, edgecolor="white", linewidth=0.5)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("PageRank Score", fontsize=11)
ax.set_title("Top-15 Productos por Centralidad PageRank", fontsize=13, fontweight="bold")
for i, (bar, s) in enumerate(zip(bars, scores)):
    ax.text(bar.get_width() + 0.0001, bar.get_y() + bar.get_height()/2,
            f"{s:.4f}", va="center", fontsize=8)
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(FIG_DIR / "pagerank_bar.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"[OK] pagerank_bar.png")

# ===================================================================
# Figura 4: Comparativa de sistemas
# ===================================================================
fig, axes = plt.subplots(1, 3, figsize=(14, 5))

system_order = ["popularity", "pagerank", "content_tfidf", "cf_als", "hybrid"]
display_names = ["Popularity", "PageRank", "Content\n(TF-IDF)", "CF\n(ALS)", "Hybrid"]
colors_sys = ["#A0A0A0", "#F28E2B", "#4C78A8", "#59A14F", "#E15759"]

df = eval_table.set_index("system").loc[system_order]

for ax_i, (metric, label) in enumerate([
    ("precision@k", "Precision@5"),
    ("map@k", "MAP@5"),
    ("coverage@k", "Coverage@5")
]):
    vals = df[metric].values
    bars = axes[ax_i].bar(range(len(vals)), vals, color=colors_sys, edgecolor="white", linewidth=0.5)
    axes[ax_i].set_xticks(range(len(vals)))
    axes[ax_i].set_xticklabels(display_names, fontsize=8)
    axes[ax_i].set_title(label, fontsize=12, fontweight="bold")
    axes[ax_i].grid(axis="y", alpha=0.3)
    for bar, v in zip(bars, vals):
        axes[ax_i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                        f"{v:.3f}", ha="center", va="bottom", fontsize=8)

fig.suptitle("Comparativa de Sistemas de Recomendación (Hito 4 + 5)",
             fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(FIG_DIR / "system_comparison.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"[OK] system_comparison.png")

print(f"\n[DONE] 4 figuras generadas en {FIG_DIR}")
