"""
Smoke tests sobre los artefactos persistidos por el pipeline
(`data/features/`, `data/recommender/`, `data/processed/`).

No vuelven a correr el pipeline (eso es responsabilidad de `runbook.md` /
el orquestador `run_pipeline.py`) — verifican que, si un artefacto existe,
tiene la forma, el tipo y el rango de valores documentado en
`data/recommender/README.md` y en los reportes. Cada test se salta
automaticamente (via `require_artifact`) si el archivo aun no fue generado,
para que la suite sea utilizable tanto en un clon fresco como despues de
una corrida completa.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from conftest import require_artifact

REQUIRED_EVAL_SYSTEMS = {
    "popularity", "pagerank", "content_tfidf", "cf_als", "hybrid", "hybrid_v2_graph",
}


def test_feature_matrix_has_no_nulls_and_matches_names(data_features):
    fm_path = require_artifact(data_features / "feature_matrix.npy")
    names_path = require_artifact(data_features / "feature_names.json")

    fm = np.load(fm_path)
    with open(names_path, encoding="utf-8") as f:
        names = json.load(f)

    assert fm.ndim == 2
    assert fm.shape[1] == len(names), (
        "El numero de columnas de feature_matrix.npy debe coincidir "
        "exactamente con feature_names.json"
    )
    assert not np.isnan(fm).any(), "feature_matrix.npy no debe contener NaN"
    assert not np.isinf(fm).any(), "feature_matrix.npy no debe contener infinitos"


def test_feature_matrix_reduced_has_fewer_columns_than_original(data_features):
    fm_path = require_artifact(data_features / "feature_matrix.npy")
    fmr_path = require_artifact(data_features / "feature_matrix_reduced.npy")

    fm = np.load(fm_path)
    fmr = np.load(fmr_path)

    assert fmr.shape[0] == fm.shape[0], "PCA no debe cambiar el numero de filas"
    assert fmr.shape[1] < fm.shape[1], "PCA debe reducir la dimensionalidad"
    assert not np.isnan(fmr).any()


def test_cluster_labels_refined_align_with_feature_matrix(data_features):
    fm_path = require_artifact(data_features / "feature_matrix.npy")
    labels_path = require_artifact(data_features / "cluster_labels_refined.npy")

    fm = np.load(fm_path)
    labels = np.load(labels_path)

    assert labels.shape == (fm.shape[0],), (
        "cluster_labels_refined.npy debe tener una etiqueta por evento "
        "de feature_matrix.npy (misma fuente de verdad)"
    )
    assert labels.min() >= -1, "DBSCAN solo produce -1 (ruido) o ids >= 0"
    assert labels.max() >= 0, "Debe existir al menos un cluster real (no todo ruido)"
    noise_ratio = float((labels == -1).mean())
    assert noise_ratio < 0.05, (
        f"El ruido de DBSCAN ({noise_ratio:.2%}) se disparo muy por encima "
        f"del ~0.28% documentado en reports/cluster_profiles.md; revisar "
        f"si cambiaron los hiperparametros (eps=2.7, min_samples=15)"
    )


@pytest.mark.parametrize("filename", [
    "R_restock_bin.npz",
    "R_restock_count.npz",
    "R_household_bin.npz",
])
def test_interaction_matrices_are_nonnegative(data_recommender, filename):
    path = require_artifact(data_recommender / filename)
    R = sp.load_npz(path)
    assert R.shape[1] == 50, "El catalogo del proyecto tiene 50 productos"
    assert R.nnz > 0, f"{filename} no puede estar vacia"
    assert (R.data >= 0).all(), f"{filename} no debe tener valores negativos"


def test_restock_bin_matrix_is_strictly_binary(data_recommender):
    path = require_artifact(data_recommender / "R_restock_bin.npz")
    R = sp.load_npz(path)
    values = np.unique(R.data)
    assert set(values.tolist()).issubset({0.0, 1.0}), (
        "R_restock_bin.npz debe ser estrictamente binaria (presencia/ausencia)"
    )


def test_als_factors_shapes_are_consistent(data_recommender):
    x_path = require_artifact(data_recommender / "als_X.npy")
    y_path = require_artifact(data_recommender / "als_Y.npy")
    r_path = require_artifact(data_recommender / "R_restock_bin.npz")

    X = np.load(x_path)
    Y = np.load(y_path)
    R = sp.load_npz(r_path)

    assert X.shape[0] == R.shape[0], "Factores de sesion deben alinear con filas de R"
    assert Y.shape[0] == R.shape[1], "Factores de producto deben alinear con columnas de R"
    assert X.shape[1] == Y.shape[1], "X e Y deben compartir el numero de dimensiones latentes (K)"
    assert not np.isnan(X).any() and not np.isnan(Y).any()


def test_evaluation_table_has_all_systems_and_valid_metric_ranges(data_recommender):
    path = require_artifact(data_recommender / "evaluation_table.csv")
    df = pd.read_csv(path)

    assert set(df["system"]) == REQUIRED_EVAL_SYSTEMS, (
        "evaluation_table.csv debe cubrir los 6 sistemas comparables bajo "
        "el mismo protocolo (ver docstring de evaluation.py)"
    )
    for col in ["precision@k", "recall@k", "nprecision@k", "map@k", "coverage@k"]:
        assert df[col].between(0.0, 1.0).all(), f"{col} debe estar en [0, 1]"

    # El hibrido de produccion debe tener 100% de coverage (documentado en
    # final_report.md sec. 10 y en el criterio de "sesgo de popularidad").
    hybrid_row = df[df["system"] == "hybrid"].iloc[0]
    assert hybrid_row["coverage@k"] == pytest.approx(1.0, abs=1e-6), (
        "El sistema hibrido de produccion debe cubrir el 100% del catalogo"
    )


def test_product_catalog_ids_are_unique_and_match_graph(data_recommender):
    catalog_path = require_artifact(data_recommender / "product_catalog.csv")
    catalog = pd.read_csv(catalog_path)

    assert catalog["product_id"].is_unique, "product_id debe ser clave unica del catalogo"
    assert len(catalog) == 50, "El catalogo del proyecto tiene 50 productos por diseno"


def test_graph_metrics_pagerank_covers_full_catalog(data_recommender):
    catalog_path = require_artifact(data_recommender / "product_catalog.csv")
    metrics_path = require_artifact(data_recommender / "graph_metrics.json")

    catalog = pd.read_csv(catalog_path)
    with open(metrics_path, encoding="utf-8") as f:
        metrics = json.load(f)

    node_metrics = metrics["node_metrics"]
    assert metrics["network_overview"]["num_nodes"] == len(catalog)
    assert len(node_metrics) == len(catalog)

    pagerank_sum = sum(m["pagerank"] for m in node_metrics.values())
    assert pagerank_sum == pytest.approx(1.0, abs=1e-3)


def test_inventory_v1_has_no_fully_null_required_columns(data_processed):
    path = require_artifact(data_processed / "inventory_v1.csv")
    df = pd.read_csv(path)

    required_cols = {
        "event_id", "household_id", "stock_id", "product_id", "event_type",
        "quantity", "timestamp", "expiry_date",
    }
    assert required_cols.issubset(df.columns)
    assert len(df) > 0
    for col in required_cols:
        assert df[col].notna().all(), f"{col} no debe tener nulos en el SSOT"
    assert set(df["event_type"].unique()).issubset({"IN", "OUT"})
