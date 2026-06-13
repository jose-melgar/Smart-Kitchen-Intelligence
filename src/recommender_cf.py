"""
recommender_cf.py — Hito 4 (Semana 10/11): filtrado colaborativo.

Dos enfoques:
  A) Ítem-ítem por dot product / cosine sim sobre R (Semana 10).
     "Productos similares = los que aparecen juntos en muchas sesiones."
  B) Factorización implícita con ALS (Alternating Least Squares) + barrido
     de λ (lambda iteration) para regularización.

ALS resuelve min sum_{u,i}  c_{ui} (p_{ui} - x_u · y_i)^2
                 + λ (||X||^2 + ||Y||^2)
donde p_{ui} = 1 si la sesión u tocó el producto i, 0 si no, y c_{ui} es la
confianza derivada de R (Hu, Koren, Volinsky 2008). La iteración alterna:
  x_u = (Y^T C^u Y + λI)^-1 Y^T C^u p_u
  y_i = (X^T C^i X + λI)^-1 X^T C^i p_i
y elegimos λ por hold-out de un porcentaje de interacciones medido por
precision@k y recall@k.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[1]
REC_DIR = ROOT / "data" / "recommender"


# ---------------------------------------------------------------------------
# A) Similitud ítem-ítem
# ---------------------------------------------------------------------------

def item_item_dot(R: sp.csr_matrix) -> np.ndarray:
    """Dot product = co-ocurrencia ponderada. Interpretación directa: nº de
    sesiones donde ambos productos aparecen."""
    sim = (R.T @ R).toarray()
    np.fill_diagonal(sim, 0.0)
    return sim


def item_item_cosine(R: sp.csr_matrix) -> np.ndarray:
    """Cosine sim sobre columnas de R: invariante al tamaño de sesión."""
    sim = cosine_similarity(R.T)
    np.fill_diagonal(sim, 0.0)
    return sim


# ---------------------------------------------------------------------------
# B) ALS implícito (Hu/Koren/Volinsky)
# ---------------------------------------------------------------------------

def als_implicit(
    R: sp.csr_matrix,
    factors: int = 16,
    reg: float = 0.1,
    alpha: float = 20.0,
    iterations: int = 12,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    R: matriz sesión × producto con valores ≥ 0 (preferencia implícita).
       Se transforma en p = 1{R>0} y confianza c = 1 + alpha * R.
    factors: tamaño del espacio latente.
    reg (λ): regularización L2 — el hiperparámetro que barreamos.
    """
    rng = np.random.default_rng(seed)
    n_u, n_i = R.shape
    P = (R > 0).astype(float).tocsr()
    C = R.copy().astype(float)
    C.data = 1.0 + alpha * C.data  # confianza incremental sobre la base
    # Para celdas vacías la confianza es 1 (manejado vía Cu_minus_I + I más abajo)

    X = rng.normal(scale=0.01, size=(n_u, factors))
    Y = rng.normal(scale=0.01, size=(n_i, factors))
    I_f = np.eye(factors) * reg

    P_csr, P_csc = P.tocsr(), P.tocsc()
    C_csr, C_csc = C.tocsr(), C.tocsc()

    for it in range(iterations):
        # Update X (sesiones)
        YtY = Y.T @ Y
        for u in range(n_u):
            start, end = C_csr.indptr[u], C_csr.indptr[u + 1]
            idx = C_csr.indices[start:end]
            c_u = C_csr.data[start:end]   # c_{ui} para i con interacción
            if len(idx) == 0:
                X[u] = 0.0
                continue
            Y_u = Y[idx]
            # Y^T (Cu - I) Y  =  Y_u^T diag(c_u - 1) Y_u
            A = YtY + Y_u.T @ ((c_u - 1.0)[:, None] * Y_u) + I_f
            b = Y_u.T @ (c_u * 1.0)  # p_{ui} = 1 para idx
            X[u] = np.linalg.solve(A, b)
        # Update Y (productos)
        XtX = X.T @ X
        for i in range(n_i):
            start, end = C_csc.indptr[i], C_csc.indptr[i + 1]
            idx = C_csc.indices[start:end]
            c_i = C_csc.data[start:end]
            if len(idx) == 0:
                Y[i] = 0.0
                continue
            X_i = X[idx]
            A = XtX + X_i.T @ ((c_i - 1.0)[:, None] * X_i) + I_f
            b = X_i.T @ (c_i * 1.0)
            Y[i] = np.linalg.solve(A, b)
    return X, Y


# ---------------------------------------------------------------------------
# Evaluación: hold-out por máscara aleatoria de interacciones
# ---------------------------------------------------------------------------

def train_test_split_interactions(R: sp.csr_matrix, test_frac: float = 0.2, seed: int = 42):
    rng = np.random.default_rng(seed)
    R_coo = R.tocoo()
    n_nnz = R_coo.nnz
    mask = rng.random(n_nnz) < test_frac
    train = sp.coo_matrix(
        (R_coo.data[~mask], (R_coo.row[~mask], R_coo.col[~mask])), shape=R.shape
    ).tocsr()
    test_idx = list(zip(R_coo.row[mask].tolist(), R_coo.col[mask].tolist()))
    return train, test_idx


def precision_recall_at_k(scores: np.ndarray, train: sp.csr_matrix, test_idx, k: int = 5):
    """scores: sesión × producto (mayor = más relevante)."""
    train_lil = train.tolil()
    # Mascarar interacciones ya vistas en train para no recomendarlas.
    scores = scores.copy()
    rows, cols = train.nonzero()
    scores[rows, cols] = -np.inf

    by_user = {}
    for u, i in test_idx:
        by_user.setdefault(u, set()).add(i)

    precisions, recalls = [], []
    for u, truth in by_user.items():
        topk = np.argpartition(-scores[u], k)[:k]
        topk = topk[np.argsort(-scores[u][topk])]
        hits = sum(1 for i in topk if i in truth)
        precisions.append(hits / k)
        recalls.append(hits / max(1, len(truth)))
    return float(np.mean(precisions)), float(np.mean(recalls))


# ---------------------------------------------------------------------------
# Barrido de λ
# ---------------------------------------------------------------------------

def lambda_sweep(
    R: sp.csr_matrix,
    lambdas: list[float],
    factors: int = 16,
    alpha: float = 20.0,
    iterations: int = 10,
    test_frac: float = 0.2,
    k: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """Barre λ, evalúa precision@k / recall@k sobre hold-out."""
    train, test_idx = train_test_split_interactions(R, test_frac=test_frac, seed=seed)
    rows = []
    for lam in lambdas:
        X, Y = als_implicit(train, factors=factors, reg=lam, alpha=alpha,
                            iterations=iterations, seed=seed)
        scores = X @ Y.T
        p, r = precision_recall_at_k(scores, train, test_idx, k=k)
        rows.append({"lambda": lam, "precision@k": p, "recall@k": r})
        print(f"  λ={lam:>8.4f}  precision@{k}={p:.4f}  recall@{k}={r:.4f}")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    R = sp.load_npz(REC_DIR / "R_restock_tfidf_R.npz")
    print(f"[cf] R cargada (tfidf_R sobre restock): shape={R.shape}, nnz={R.nnz}")

    # --- A) Similitudes ítem-ítem ---
    sim_dot = item_item_dot(sp.load_npz(REC_DIR / "R_restock_bin.npz"))
    sim_cos = item_item_cosine(sp.load_npz(REC_DIR / "R_restock_bin.npz"))
    np.save(REC_DIR / "item_sim_cf_dot.npy", sim_dot)
    np.save(REC_DIR / "item_sim_cf_cosine.npy", sim_cos)
    print(f"[cf] Item-item dot/cosine guardadas. "
          f"dot[0,1]={sim_dot[0,1]:.2f}, cos[0,1]={sim_cos[0,1]:.4f}")

    # --- B) ALS + barrido de λ ---
    lambdas = [0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0]
    print(f"\n[cf] Lambda iteration sobre {len(lambdas)} valores...")
    sweep = lambda_sweep(R, lambdas, factors=16, alpha=20.0,
                         iterations=8, k=5, seed=42)
    sweep.to_csv(REC_DIR / "lambda_sweep.csv", index=False)
    best = sweep.iloc[sweep["precision@k"].idxmax()]
    print(f"\n[cf] λ óptimo = {best['lambda']} (precision@5 = {best['precision@k']:.4f})")

    # Entrenamiento final con λ óptimo sobre R completa.
    X, Y = als_implicit(R, factors=16, reg=float(best["lambda"]),
                        alpha=20.0, iterations=12, seed=42)
    np.save(REC_DIR / "als_X.npy", X)
    np.save(REC_DIR / "als_Y.npy", Y)
    with open(REC_DIR / "als_meta.json", "w") as f:
        json.dump({
            "factors": 16,
            "alpha": 20.0,
            "lambda": float(best["lambda"]),
            "iterations": 12,
            "encoding": "R_restock_tfidf_R",
            "best_precision@5": float(best["precision@k"]),
            "best_recall@5": float(best["recall@k"]),
        }, f, indent=2)
    print(f"[cf] Factores ALS guardados (X={X.shape}, Y={Y.shape}).")


if __name__ == "__main__":
    main()
