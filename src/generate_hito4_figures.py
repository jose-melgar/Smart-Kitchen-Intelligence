"""
generate_hito4_figures.py — Hito 4: figuras para el reporte LaTeX.

Genera todas las figuras en `reports/figures/hito4/`:
  - sparsity_density.png   : comparativa de densidad/sparsity por encoding y unidad.
  - normalization_dist.png : distribución del valor de R por normalización.
  - lambda_sweep.png       : precision@k vs λ.
  - cold_start_compare.png : comparativa de estrategias cold-start.
  - hybrid_ablation.png    : precision@5 por combinación de pesos.
  - tfidf_idf.png          : tokens con mayor/menor IDF en el catálogo.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
REC_DIR = ROOT / "data" / "recommender"
FIG_DIR = ROOT / "reports" / "figures" / "hito4"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 140,
                     "axes.spines.top": False, "axes.spines.right": False})


def fig_sparsity():
    with open(REC_DIR / "sparsity_report.json") as f:
        rep = json.load(f)
    df = pd.DataFrame(rep)
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(df["matrix"], df["density"], color="#1f77b4")
    ax.set_ylabel("Densidad (fracción no-cero)")
    ax.set_title("Densidad / sparsity por variante de R")
    ax.set_xticklabels(df["matrix"], rotation=30, ha="right")
    for b, d, s in zip(bars, df["density"], df["sparsity"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01,
                f"{d:.3f}", ha="center", fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "sparsity_density.png")
    plt.close()


def fig_normalizations():
    fig, axes = plt.subplots(1, 5, figsize=(15, 3), sharey=False)
    for ax, name in zip(axes, ["raw", "row_mean_center", "log1p", "tfidf_R", "l2_row"]):
        M = sp.load_npz(REC_DIR / f"R_restock_{name}.npz")
        data = M.data
        ax.hist(data, bins=40, color="#2ca02c", alpha=0.85)
        ax.set_title(name, fontsize=10)
        ax.set_xlabel("valor")
    axes[0].set_ylabel("frecuencia")
    fig.suptitle("Distribución de valores no-cero por normalización (R_restock_count)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "normalization_dist.png")
    plt.close()


def fig_lambda_sweep():
    df = pd.read_csv(REC_DIR / "lambda_sweep.csv")
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.semilogx(df["lambda"], df["precision@k"], "o-", color="#d62728",
                 label="precision@5")
    ax1.set_xlabel("λ (regularización)")
    ax1.set_ylabel("precision@5", color="#d62728")
    ax2 = ax1.twinx()
    ax2.semilogx(df["lambda"], df["recall@k"], "s--", color="#1f77b4",
                 label="recall@5")
    ax2.set_ylabel("recall@5", color="#1f77b4")
    best = df.iloc[df["precision@k"].idxmax()]
    ax1.axvline(best["lambda"], color="gray", ls=":", alpha=0.6)
    ax1.set_title(f"Lambda iteration (ALS) — óptimo λ = {best['lambda']}")
    fig.tight_layout()
    plt.savefig(FIG_DIR / "lambda_sweep.png")
    plt.close()


def fig_cold_start():
    df1 = pd.read_csv(REC_DIR / "cold_start_session.csv")
    df2 = pd.read_csv(REC_DIR / "cold_start_session_2seed.csv")
    strategies = ["popularity", "partial_cf", "content_only", "mixed"]
    means_1 = [df1[f"prec@5_{s}"].mean() for s in strategies]
    means_2 = [df2[f"prec@5_{s}"].mean() for s in strategies]
    x = np.arange(len(strategies))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - w/2, means_1, w, label="1 seed item", color="#ff7f0e")
    ax.bar(x + w/2, means_2, w, label="2 seed items", color="#1f77b4")
    ax.set_xticks(x); ax.set_xticklabels(strategies)
    ax.set_ylabel("precision@5")
    ax.set_title("Estrategias de cold-start (sesión cold)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "cold_start_compare.png")
    plt.close()


def fig_hybrid_ablation():
    df = pd.read_csv(REC_DIR / "hybrid_ablation.csv")
    labels = [f"({r.w_C:.2f},{r.w_F:.2f},{r.w_E:.2f})"
              for _, r in df.iterrows()]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, df["precision@5"], color="#9467bd")
    ax.set_ylabel("precision@5")
    ax.set_title("Ablación de pesos del recomendador híbrido (w_C, w_F, w_E)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "hybrid_ablation.png")
    plt.close()


def fig_tfidf_idf():
    """IDF de los tokens del catálogo (top y bottom)."""
    import json
    vocab = json.load(open(REC_DIR / "tfidf_vocab.json"))
    inv = {i: t for t, i in vocab.items()}
    # Reconstruimos idf desde X / tfidf_items (heurística rápida).
    X = sp.load_npz(REC_DIR / "tfidf_items.npz")
    # Aproximación: idf relativo = inversa de col_density.
    col_density = np.asarray((X > 0).sum(axis=0)).flatten() / X.shape[0]
    idf_proxy = np.log(1.0 / np.maximum(col_density, 1e-6))
    order = np.argsort(idf_proxy)
    bottom = order[:10]
    top = order[-10:]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].barh([inv[i] for i in bottom], idf_proxy[bottom], color="#bcbd22")
    axes[0].set_title("Tokens con menor IDF (comunes)")
    axes[0].invert_yaxis()
    axes[1].barh([inv[i] for i in top], idf_proxy[top], color="#17becf")
    axes[1].set_title("Tokens con mayor IDF (raros/discriminantes)")
    axes[1].invert_yaxis()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "tfidf_idf.png")
    plt.close()


def main() -> None:
    fig_sparsity()
    fig_normalizations()
    fig_lambda_sweep()
    fig_cold_start()
    fig_hybrid_ablation()
    fig_tfidf_idf()
    print(f"[figures] Figuras guardadas en {FIG_DIR}")
    for p in sorted(FIG_DIR.glob("*.png")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
