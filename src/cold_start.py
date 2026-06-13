"""
cold_start.py — Hito 4: estrategias frente al problema cold-start.

Escenarios:
  (A) Producto cold: producto nuevo sin historial en R.
  (B) Sesión cold:    nueva sesión de despensa con poquísimos productos
                      conocidos (≤2 items).

Estrategias evaluadas y comparadas con hold-out:
  1. popularity     — score = popularidad global del producto.
  2. partial_cf     — k-NN ítem-ítem CF: si la sesión cold tiene ≥1 producto,
                      recomienda lo más similar a esos productos.
  3. content_only   — score = cosine sim contra centroide de productos vistos
                      (perfil basado en TF-IDF de contenido).
  4. mixed          — combinación lineal popularity*α + content*(1-α).

La elección final se justifica con precision@k y coverage en el reporte.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
REC_DIR = ROOT / "data" / "recommender"


# ---------------------------------------------------------------------------
# Estrategias
# ---------------------------------------------------------------------------

def score_popularity(R: sp.csr_matrix) -> np.ndarray:
    """Popularidad = frecuencia global de cada producto en R."""
    pop = np.asarray(R.sum(axis=0)).flatten()
    return pop / max(pop.sum(), 1.0)


def score_partial_cf(known_items: list[int], item_sim_cf: np.ndarray) -> np.ndarray:
    """Si ya conocemos k items de la sesión cold, agregamos su fila de
    similitud ítem-ítem CF (promedio)."""
    if not known_items:
        return np.zeros(item_sim_cf.shape[0])
    return item_sim_cf[known_items].mean(axis=0)


def score_content(known_items: list[int], item_sim_content: np.ndarray) -> np.ndarray:
    """Similitud por contenido (TF-IDF del catálogo). Útil para producto cold:
    se calcula su similitud contra todo el catálogo y se rankean."""
    if not known_items:
        return item_sim_content.mean(axis=0)
    return item_sim_content[known_items].mean(axis=0)


def score_mixed(known_items: list[int], pop: np.ndarray,
                item_sim_content: np.ndarray, alpha: float = 0.4) -> np.ndarray:
    """Mezcla popularidad + contenido."""
    content = score_content(known_items, item_sim_content)
    # Normaliza al [0,1] para combinar a escalas comparables.
    def norm(x):
        x = np.asarray(x, dtype=float)
        rng = x.max() - x.min()
        return (x - x.min()) / rng if rng > 0 else np.zeros_like(x)
    return alpha * norm(pop) + (1 - alpha) * norm(content)


# ---------------------------------------------------------------------------
# Evaluación
# ---------------------------------------------------------------------------

def evaluate_session_cold(
    R: sp.csr_matrix,
    item_sim_cf: np.ndarray,
    item_sim_content: np.ndarray,
    pop: np.ndarray,
    seed_items_per_session: int = 1,
    k: int = 5,
    n_sample: int = 400,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Para cada sesión multi-producto, "ocultamos" todos menos
    `seed_items_per_session` items, y medimos precision@k para 4 estrategias.
    """
    rng = np.random.default_rng(seed)
    R_lil = R.tolil()
    n_u, n_i = R.shape

    # Sesiones candidatas: las que tienen al menos seed_items+1 productos.
    sess_with_enough = [u for u in range(n_u)
                        if len(R_lil.rows[u]) >= seed_items_per_session + 1]
    if len(sess_with_enough) > n_sample:
        sess_with_enough = rng.choice(sess_with_enough, n_sample, replace=False).tolist()

    rows = []
    for u in sess_with_enough:
        items = list(R_lil.rows[u])
        rng.shuffle(items)
        known = items[:seed_items_per_session]
        truth = set(items[seed_items_per_session:])

        def topk(scores):
            scores = scores.copy()
            for i in known:
                scores[i] = -np.inf
            top = np.argpartition(-scores, k)[:k]
            top = top[np.argsort(-scores[top])]
            return top

        results = {
            "popularity": topk(pop),
            "partial_cf": topk(score_partial_cf(known, item_sim_cf)),
            "content_only": topk(score_content(known, item_sim_content)),
            "mixed": topk(score_mixed(known, pop, item_sim_content)),
        }
        row = {"session_idx": u, "n_known": len(known), "n_truth": len(truth)}
        for name, rec in results.items():
            hits = sum(1 for i in rec if i in truth)
            row[f"prec@{k}_{name}"] = hits / k
            row[f"rec@{k}_{name}"] = hits / max(1, len(truth))
        rows.append(row)

    return pd.DataFrame(rows)


def evaluate_product_cold(
    R: sp.csr_matrix,
    item_sim_content: np.ndarray,
    k: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Para cada producto, simulamos que es 'nuevo' (cero historial) y medimos
    si la sesión correcta lo recupera basándose solo en contenido (vecinos
    cercanos del producto cold deberían estar entre los más probables).
    """
    rng = np.random.default_rng(seed)
    n_u, n_i = R.shape
    R_csc = R.tocsc()
    rows = []
    for i in range(n_i):
        # popularidad sin el producto i (fallback)
        rest = list(range(n_i))
        rest.remove(i)
        # vecinos por contenido
        sim_to_i = item_sim_content[i]
        nbrs = np.argsort(-sim_to_i)[:k]
        # ¿están entre los productos realmente co-ocurrentes en sesiones que tocaron i?
        sessions_with_i = R_csc.indices[R_csc.indptr[i]: R_csc.indptr[i + 1]]
        if len(sessions_with_i) == 0:
            continue
        # set de productos co-ocurrentes reales
        co_occ = set()
        R_csr = R.tocsr()
        for u in sessions_with_i:
            co_occ.update(R_csr.indices[R_csr.indptr[u]: R_csr.indptr[u + 1]])
        co_occ.discard(i)
        hits = sum(1 for n in nbrs if n in co_occ)
        rows.append({"product_idx": i, "n_neighbors_hit": hits,
                     "precision_content@k": hits / k})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    R = sp.load_npz(REC_DIR / "R_restock_bin.npz")
    item_sim_cf = np.load(REC_DIR / "item_sim_cf_cosine.npy")
    item_sim_content = np.load(REC_DIR / "item_sim_content.npy")
    pop = score_popularity(R)
    print(f"[cold] R={R.shape}, popularity head: "
          f"{[(int(i), float(pop[i])) for i in np.argsort(-pop)[:3]]}")

    # --- Sesión cold ---
    print("\n[cold] Evaluando sesión cold (1 seed item conocido) ...")
    df_sess = evaluate_session_cold(R, item_sim_cf, item_sim_content, pop,
                                    seed_items_per_session=1, k=5,
                                    n_sample=400, seed=42)
    print(df_sess.filter(regex="prec@5").mean().round(4))
    df_sess.to_csv(REC_DIR / "cold_start_session.csv", index=False)

    print("\n[cold] Evaluando sesión cold (2 seed items conocidos) ...")
    df_sess2 = evaluate_session_cold(R, item_sim_cf, item_sim_content, pop,
                                     seed_items_per_session=2, k=5,
                                     n_sample=400, seed=42)
    print(df_sess2.filter(regex="prec@5").mean().round(4))
    df_sess2.to_csv(REC_DIR / "cold_start_session_2seed.csv", index=False)

    # --- Producto cold ---
    print("\n[cold] Evaluando producto cold (content-only) ...")
    df_prod = evaluate_product_cold(R, item_sim_content, k=5)
    print(f"  precision_content@5 (avg) = {df_prod['precision_content@k'].mean():.4f}")
    df_prod.to_csv(REC_DIR / "cold_start_product.csv", index=False)

    # Conclusión: guardar JSON con la decisión.
    means_1seed = df_sess.filter(regex="prec@5").mean().to_dict()
    means_2seed = df_sess2.filter(regex="prec@5").mean().to_dict()
    winner = max(means_2seed, key=means_2seed.get)
    summary = {
        "session_cold_1seed": means_1seed,
        "session_cold_2seed": means_2seed,
        "product_cold_content_only_precision@5": float(df_prod['precision_content@k'].mean()),
        "selected_strategy": winner.replace("prec@5_", ""),
        "rationale": ("Se selecciona la estrategia con mayor precision@5 sobre "
                      "hold-out de 400 sesiones con 2 productos seed. "
                      "Para producto cold, content-only es la única viable "
                      "porque no hay historial CF."),
    }
    with open(REC_DIR / "cold_start_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[cold] Estrategia ganadora: {summary['selected_strategy']}")


if __name__ == "__main__":
    main()
