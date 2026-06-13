"""
build_R.py — Hito 4 (Semana 11): Construcción de la matriz de interacción R.

Define la unidad de "sesión" para SKI (análogo al "playlist" del ejemplo del curso)
y produce R = sesiones × productos en 4 encodings distintos. Calcula sparsity y
densidad de cada variante, base para justificar la elección en el reporte.

Sesiones (definidas en proposal.md):
  - Restock Window: eventos IN dentro de 60 min por household → 1.177 sesiones
  - Kitchen Session: eventos OUT dentro de 15 min por household → 8.075 sesiones
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[1]
DATA_PROC = ROOT / "data" / "processed" / "inventory_v1.csv"
OUT_DIR = ROOT / "data" / "recommender"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def assign_sessions(df: pd.DataFrame, gap_minutes: int, label: str) -> pd.DataFrame:
    """Asigna session_id agrupando eventos consecutivos por household
    cuyo gap temporal sea <= gap_minutes."""
    df_s = df.sort_values(["household_id", "timestamp"]).copy()
    diff_min = (
        df_s.groupby("household_id")["timestamp"].diff().dt.total_seconds().div(60).fillna(0)
    )
    new_sess = ((diff_min > gap_minutes) | (df_s.groupby("household_id").cumcount() == 0)).astype(int)
    df_s["session_local"] = df_s.groupby("household_id")[new_sess.name if new_sess.name else "x"].apply(lambda _: None) if False else None
    df_s["_new_sess"] = new_sess.values
    df_s["_sess_idx"] = df_s.groupby("household_id")["_new_sess"].cumsum()
    df_s["session_id"] = label + "_" + df_s["household_id"].astype(str) + "_" + df_s["_sess_idx"].astype(str)
    return df_s.drop(columns=["_new_sess", "_sess_idx"])


def build_R_variants(events: pd.DataFrame, products: list[int]) -> dict:
    """Construye 4 encodings de R sobre el mismo conjunto de sesiones × productos."""
    sessions = events["session_id"].unique().tolist()
    sess_idx = {s: i for i, s in enumerate(sessions)}
    prod_idx = {p: i for i, p in enumerate(products)}

    rows = events["session_id"].map(sess_idx).to_numpy()
    cols = events["product_id"].map(prod_idx).to_numpy()
    qty = events["quantity"].to_numpy(dtype=float)

    n, m = len(sessions), len(products)
    # 1) binaria: presencia/ausencia
    R_bin = sp.coo_matrix((np.ones_like(rows, dtype=float), (rows, cols)), shape=(n, m))
    R_bin.sum_duplicates()
    R_bin.data = np.minimum(R_bin.data, 1.0)
    # 2) count: nº de eventos del producto en la sesión
    R_cnt = sp.coo_matrix((np.ones_like(rows, dtype=float), (rows, cols)), shape=(n, m))
    R_cnt.sum_duplicates()
    # 3) qty: cantidad total sumada
    R_qty = sp.coo_matrix((qty, (rows, cols)), shape=(n, m))
    R_qty.sum_duplicates()
    # 4) freq: frecuencia normalizada por tamaño de sesión (row-stochastic sobre conteos)
    R_freq = R_cnt.tocsr().astype(float).copy()
    row_sums = np.asarray(R_freq.sum(axis=1)).flatten()
    row_sums[row_sums == 0] = 1.0
    R_freq = R_freq.multiply(1.0 / row_sums[:, None]).tocsr()

    return {
        "R_bin": R_bin.tocsr(),
        "R_count": R_cnt.tocsr(),
        "R_qty": R_qty.tocsr(),
        "R_freq": R_freq,
        "sessions": sessions,
        "products": products,
    }


def sparsity_report(name: str, R: sp.csr_matrix) -> dict:
    n, m = R.shape
    nnz = R.nnz
    density = nnz / (n * m)
    sparsity = 1.0 - density
    row_nnz = np.asarray((R != 0).sum(axis=1)).flatten()
    col_nnz = np.asarray((R != 0).sum(axis=0)).flatten()
    return {
        "matrix": name,
        "shape": [int(n), int(m)],
        "nnz": int(nnz),
        "density": float(density),
        "sparsity": float(sparsity),
        "row_nnz_mean": float(row_nnz.mean()),
        "row_nnz_min": int(row_nnz.min()) if len(row_nnz) else 0,
        "row_nnz_max": int(row_nnz.max()) if len(row_nnz) else 0,
        "col_nnz_mean": float(col_nnz.mean()),
        "col_nnz_min": int(col_nnz.min()) if len(col_nnz) else 0,
        "col_nnz_max": int(col_nnz.max()) if len(col_nnz) else 0,
    }


def main() -> None:
    df = pd.read_csv(DATA_PROC, parse_dates=["timestamp", "expiry_date"])
    print(f"[build_R] Cargados {len(df):,} eventos, "
          f"{df['household_id'].nunique()} households, "
          f"{df['product_id'].nunique()} productos únicos.")

    # Catálogo estable: usar todos los productos vistos en data, ordenados por id.
    products = sorted(df["product_id"].unique().tolist())

    # --- Restock sessions (60 min, eventos IN) ---
    df_in = df[df["event_type"] == "IN"].copy()
    df_in = assign_sessions(df_in, gap_minutes=60, label="rest")
    print(f"[build_R] Restock sessions: {df_in['session_id'].nunique():,}")
    R_rest = build_R_variants(df_in, products)

    # --- Kitchen sessions (15 min, eventos OUT) ---
    df_out = df[df["event_type"] == "OUT"].copy()
    df_out = assign_sessions(df_out, gap_minutes=15, label="kit")
    print(f"[build_R] Kitchen sessions: {df_out['session_id'].nunique():,}")
    R_kit = build_R_variants(df_out, products)

    # --- Caso base degenerado: household × producto ---
    hh_idx = {h: i for i, h in enumerate(sorted(df["household_id"].unique().tolist()))}
    prod_idx = {p: i for i, p in enumerate(products)}
    rows = df["household_id"].map(hh_idx).to_numpy()
    cols = df["product_id"].map(prod_idx).to_numpy()
    R_hh_bin = sp.coo_matrix((np.ones_like(rows, dtype=float), (rows, cols)),
                              shape=(len(hh_idx), len(prod_idx))).tocsr()
    R_hh_bin.data = np.minimum(R_hh_bin.data, 1.0)
    R_hh_cnt = sp.coo_matrix((np.ones_like(rows, dtype=float), (rows, cols)),
                              shape=(len(hh_idx), len(prod_idx))).tocsr()

    # --- Guardar matrices ---
    sp.save_npz(OUT_DIR / "R_restock_bin.npz", R_rest["R_bin"])
    sp.save_npz(OUT_DIR / "R_restock_count.npz", R_rest["R_count"])
    sp.save_npz(OUT_DIR / "R_restock_qty.npz", R_rest["R_qty"])
    sp.save_npz(OUT_DIR / "R_restock_freq.npz", R_rest["R_freq"])
    sp.save_npz(OUT_DIR / "R_kitchen_bin.npz", R_kit["R_bin"])
    sp.save_npz(OUT_DIR / "R_kitchen_count.npz", R_kit["R_count"])
    sp.save_npz(OUT_DIR / "R_household_bin.npz", R_hh_bin)
    sp.save_npz(OUT_DIR / "R_household_count.npz", R_hh_cnt)

    with open(OUT_DIR / "products.json", "w") as f:
        json.dump({"products": products}, f)
    with open(OUT_DIR / "sessions_restock.json", "w") as f:
        json.dump({"sessions": R_rest["sessions"]}, f)
    with open(OUT_DIR / "sessions_kitchen.json", "w") as f:
        json.dump({"sessions": R_kit["sessions"]}, f)

    # --- Reporte de sparsity ---
    reports = [
        sparsity_report("R_restock_bin", R_rest["R_bin"]),
        sparsity_report("R_restock_count", R_rest["R_count"]),
        sparsity_report("R_restock_qty", R_rest["R_qty"]),
        sparsity_report("R_restock_freq", R_rest["R_freq"]),
        sparsity_report("R_kitchen_bin", R_kit["R_bin"]),
        sparsity_report("R_kitchen_count", R_kit["R_count"]),
        sparsity_report("R_household_bin", R_hh_bin),
        sparsity_report("R_household_count", R_hh_cnt),
    ]
    with open(OUT_DIR / "sparsity_report.json", "w") as f:
        json.dump(reports, f, indent=2)

    print("\n[build_R] === Sparsity / densidad ===")
    for r in reports:
        print(f"  {r['matrix']:<22} shape={tuple(r['shape'])!s:<12} "
              f"density={r['density']:.4f}  sparsity={r['sparsity']:.4f}  "
              f"nnz={r['nnz']}")

    print(f"\n[build_R] Matrices guardadas en {OUT_DIR}")


if __name__ == "__main__":
    main()
