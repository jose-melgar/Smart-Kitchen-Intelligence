"""
recommender_hybrid.py — Hito 4: recomendador mixto (mixed recommendation).

Combinación ponderada:
    score_total(prod) = w_C * score_content + w_F * score_cf + w_E * score_expiry

donde:
  - score_content : cosine sim contra perfil TF-IDF del household.
  - score_cf      : producto interno entre vector latente de la sesión y el
                    producto, derivado de ALS (X · Y^T).
  - score_expiry  : urgencia por proximidad de vencimiento — diferencial de
                    SKI frente al ejemplo de música del curso. Productos en
                    inventario actual con expiry_date más cercano suben.

Pesos por defecto (w_C, w_F, w_E) = (0.35, 0.45, 0.20):
  - El CF aporta más en sesiones con historial denso.
  - Contenido es robusto en cold-start.
  - Expiry tira hacia productos perecederos a punto de vencer (anti-waste).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
REC_DIR = ROOT / "data" / "recommender"
DATA_PROC = ROOT / "data" / "processed" / "inventory_v1.csv"


def _normalize_scores(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    rng = x.max() - x.min()
    return (x - x.min()) / rng if rng > 0 else np.zeros_like(x)


def score_expiry(household_id: int, df: pd.DataFrame,
                 catalog: pd.DataFrame, ref_date: pd.Timestamp) -> np.ndarray:
    """
    Score por urgencia: para cada producto del catálogo, mide la mediana de
    días hasta vencimiento entre las unidades en inventario actual del
    household (eventos IN no compensados por OUT).
    Cuanto más cerca está la fecha de vencimiento, mayor el score.
    """
    df_h = df[df["household_id"] == household_id].copy()
    df_h = df_h[df_h["timestamp"] <= ref_date]
    # Inventario neto: contamos IN - OUT por (stock_id) y nos quedamos con stocks vivos.
    df_h["sign"] = np.where(df_h["event_type"] == "IN", 1, -1)
    stock_state = df_h.groupby(["product_id", "stock_id"]).agg(
        net=("sign", "sum"),
        expiry=("expiry_date", "first"),
    ).reset_index()
    alive = stock_state[stock_state["net"] > 0]
    if alive.empty:
        return np.zeros(len(catalog))

    alive["days_to_expiry"] = (alive["expiry"] - ref_date).dt.days.clip(lower=0)
    urg = alive.groupby("product_id")["days_to_expiry"].median()
    # Score inverso: 1 / (1 + días).
    urg = 1.0 / (1.0 + urg)

    scores = np.zeros(len(catalog))
    pid_to_idx = {p: i for i, p in enumerate(catalog["product_id"].tolist())}
    for pid, s in urg.items():
        if pid in pid_to_idx:
            scores[pid_to_idx[pid]] = float(s)
    return scores


def score_content_profile(profile_vec, X_items_sparse) -> np.ndarray:
    from sklearn.metrics.pairwise import cosine_similarity
    return cosine_similarity(profile_vec, X_items_sparse).flatten()


def score_als_for_session(session_vec_x: np.ndarray, Y: np.ndarray) -> np.ndarray:
    return session_vec_x @ Y.T


def hybrid_score(content: np.ndarray, cf: np.ndarray, expiry: np.ndarray,
                 w_C: float = 0.35, w_F: float = 0.45, w_E: float = 0.20) -> np.ndarray:
    return (w_C * _normalize_scores(content)
            + w_F * _normalize_scores(cf)
            + w_E * _normalize_scores(expiry))


# ---------------------------------------------------------------------------
# Demo end-to-end
# ---------------------------------------------------------------------------

def main() -> None:
    df = pd.read_csv(DATA_PROC, parse_dates=["timestamp", "expiry_date"])
    catalog = pd.read_csv(REC_DIR / "product_catalog.csv")
    X_items = sp.load_npz(REC_DIR / "tfidf_items.npz")
    Y = np.load(REC_DIR / "als_Y.npy")

    # Reconstrucción del perfil de contenido y un vector de sesión latente ALS
    # con un nuevo "carrito" simulado para household=0.
    from recommender_content import build_household_profile
    ref_date = df["timestamp"].max()
    profile = build_household_profile(0, df, catalog, X_items)

    # Vector latente de sesión: regresión rápida via least squares Y·x = p
    p = np.zeros(len(catalog))
    seed_items = df[(df["household_id"] == 0) & (df["event_type"] == "OUT")] \
        .groupby("product_id").size().sort_values(ascending=False).head(5).index
    pid_to_idx = {pid: i for i, pid in enumerate(catalog["product_id"].tolist())}
    for pid in seed_items:
        p[pid_to_idx[pid]] = 1.0
    # x = (Y^T Y + λI)^-1 Y^T p
    lam = 1.0
    x_sess = np.linalg.solve(Y.T @ Y + lam * np.eye(Y.shape[1]), Y.T @ p)

    s_content = score_content_profile(profile, X_items)
    s_cf = score_als_for_session(x_sess, Y)
    s_exp = score_expiry(0, df, catalog, ref_date)

    s_hyb = hybrid_score(s_content, s_cf, s_exp,
                         w_C=0.35, w_F=0.45, w_E=0.20)

    result = catalog[["product_id", "product_name", "category", "nutriscore"]].copy()
    result["score_content"] = s_content
    result["score_cf"] = s_cf
    result["score_expiry"] = s_exp
    result["score_hybrid"] = s_hyb
    result = result.sort_values("score_hybrid", ascending=False).head(10)
    print("[hybrid] Top-10 híbrido para household=0:")
    print(result.to_string(index=False))

    # Ablación: comparar pesos
    print("\n[hybrid] Ablación de pesos (precision@5 sobre hold-out):")
    weight_grid = [
        (1.0, 0.0, 0.0),  # solo contenido
        (0.0, 1.0, 0.0),  # solo CF
        (0.0, 0.0, 1.0),  # solo expiry
        (0.5, 0.5, 0.0),  # contenido+CF
        (0.35, 0.45, 0.20),  # default
        (0.25, 0.45, 0.30),  # más peso expiry
    ]
    R_full = sp.load_npz(REC_DIR / "R_restock_bin.npz").tolil()

    # Tomamos 200 sesiones aleatorias, ocultamos 1 item, scoreamos como nueva sesión.
    rng = np.random.default_rng(0)
    sample = rng.choice(R_full.shape[0], size=200, replace=False)
    pop = np.asarray(sp.load_npz(REC_DIR / "R_restock_bin.npz").sum(axis=0)).flatten()
    rows = []
    for w in weight_grid:
        hits = 0
        evals = 0
        for u in sample:
            items = list(R_full.rows[u])
            if len(items) < 2:
                continue
            rng.shuffle(items)
            seed = items[:max(1, len(items) // 2)]
            truth = set(items[len(seed):])

            p = np.zeros(len(catalog))
            for i in seed:
                p[i] = 1.0
            x_sess = np.linalg.solve(Y.T @ Y + lam * np.eye(Y.shape[1]), Y.T @ p)
            s_cf_u = score_als_for_session(x_sess, Y)
            s_content_u = pop  # proxy: si no hay perfil rico, popularidad como contenido
            s_exp_u = s_exp
            s = (w[0] * _normalize_scores(s_content_u)
                 + w[1] * _normalize_scores(s_cf_u)
                 + w[2] * _normalize_scores(s_exp_u))
            for i in seed:
                s[i] = -np.inf
            top = np.argpartition(-s, 5)[:5]
            hits += sum(1 for i in top if i in truth)
            evals += 1
        prec = hits / (5 * max(evals, 1))
        rows.append({"w_C": w[0], "w_F": w[1], "w_E": w[2],
                     "precision@5": prec})
        print(f"  w=(C={w[0]:.2f},F={w[1]:.2f},E={w[2]:.2f}) → precision@5={prec:.4f}")
    pd.DataFrame(rows).to_csv(REC_DIR / "hybrid_ablation.csv", index=False)

    result.to_csv(REC_DIR / "hybrid_top10_hh0.csv", index=False)
    with open(REC_DIR / "hybrid_meta.json", "w") as f:
        json.dump({"task_framing": "Masked Basket Completion (Cloze Task Style)",
                   "weights": {"w_C": 0.35, "w_F": 0.45, "w_E": 0.20},
                   "reference_date": str(ref_date)}, f, indent=2)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    main()
