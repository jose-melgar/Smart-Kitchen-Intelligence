"""
normalizations.py — Hito 4: normalizaciones aplicadas a la matriz R.

Justificación por método (defendible en presentación):

  1. raw            : sin tocar. Línea base para medir el efecto.
  2. row_mean_center: x'_ui = x_ui - mean(x_u, no-zero).
                      Útil cuando las filas tienen escalas diferentes
                      (sesiones más activas pesan menos los productos comunes).
  3. log1p          : x'_ui = log(1 + x_ui).
                      Comprime distribuciones largas en `R_count` / `R_qty`
                      donde 1 evento vs 5 eventos no es lineal en preferencia.
  4. tfidf_R        : aplica TF-IDF tratando cada sesión como un "documento" y
                      cada producto como un "término".
                      idf(prod) penaliza productos ubicuos (ej. leche en todas
                      las sesiones de restock) y sube los discriminantes.
  5. l2_row         : x'_u = x_u / ||x_u||_2.
                      Equivalente a usar cosine sim como dot product de filas
                      normalizadas. Estándar antes de factorización.

`l2_row` se usa por defecto en el CF ítem-ítem porque convierte el dot product
en cosine similarity, que es invariante al tamaño de la sesión.
`tfidf_R` se usa antes de ALS porque equilibra productos populares vs raros.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
REC_DIR = ROOT / "data" / "recommender"


def row_mean_center(R: sp.csr_matrix) -> sp.csr_matrix:
    """Resta la media de las entradas no-cero por fila."""
    R = R.tolil(copy=True).astype(float)
    for i in range(R.shape[0]):
        row = R.rows[i]
        data = R.data[i]
        if data:
            mu = sum(data) / len(data)
            R.data[i] = [v - mu for v in data]
    return R.tocsr()


def log1p_norm(R: sp.csr_matrix) -> sp.csr_matrix:
    out = R.copy().astype(float)
    out.data = np.log1p(out.data)
    return out


def tfidf_R(R: sp.csr_matrix) -> sp.csr_matrix:
    """TF-IDF tratando la matriz R como (sesión × producto)."""
    n = R.shape[0]
    df = np.asarray((R != 0).sum(axis=0)).flatten()
    idf = np.log((1 + n) / (1 + df)) + 1.0
    R_log = log1p_norm(R)
    return R_log.multiply(idf).tocsr()


def l2_row(R: sp.csr_matrix) -> sp.csr_matrix:
    norms = np.sqrt(np.asarray(R.multiply(R).sum(axis=1)).flatten())
    norms[norms == 0] = 1.0
    inv = sp.diags(1.0 / norms)
    return (inv @ R).tocsr()


def summary(R: sp.csr_matrix) -> dict:
    """Métricas para incluir en el reporte."""
    data = R.data
    return {
        "shape": list(R.shape),
        "nnz": int(R.nnz),
        "mean": float(data.mean()) if data.size else 0.0,
        "std": float(data.std()) if data.size else 0.0,
        "min": float(data.min()) if data.size else 0.0,
        "max": float(data.max()) if data.size else 0.0,
        "median": float(np.median(data)) if data.size else 0.0,
    }


def main() -> None:
    R = sp.load_npz(REC_DIR / "R_restock_count.npz")
    print(f"[norm] Cargada R_restock_count: shape={R.shape}, nnz={R.nnz}")

    variants = {
        "raw": R,
        "row_mean_center": row_mean_center(R),
        "log1p": log1p_norm(R),
        "tfidf_R": tfidf_R(R),
        "l2_row": l2_row(R),
    }
    metrics = {name: summary(M) for name, M in variants.items()}

    for name, M in variants.items():
        sp.save_npz(REC_DIR / f"R_restock_{name}.npz", M)
    with open(REC_DIR / "normalization_summary.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n[norm] === Resumen estadístico por normalización ===")
    print(f"  {'variant':<18} {'mean':>10} {'std':>10} {'min':>10} {'max':>10}")
    for name, m in metrics.items():
        print(f"  {name:<18} {m['mean']:>10.4f} {m['std']:>10.4f} "
              f"{m['min']:>10.4f} {m['max']:>10.4f}")


if __name__ == "__main__":
    main()
