"""
Tests unitarios de `src/recommender_hybrid.py` — normalización de scores,
ensamble lineal y el score de urgencia por vencimiento (`score_expiry`), que
es el componente diferencial anti-desperdicio de SKI frente al ejemplo de
música del curso. Todo con datos sintéticos, sin depender del pipeline.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from recommender_hybrid import (
    _normalize_scores,
    hybrid_score,
    score_expiry,
    weight_grid_4d,
)


def test_normalize_scores_maps_to_unit_range():
    x = np.array([2.0, 4.0, 10.0])
    out = _normalize_scores(x)
    assert out.min() == pytest.approx(0.0)
    assert out.max() == pytest.approx(1.0)
    assert np.all((out >= 0) & (out <= 1))


def test_normalize_scores_constant_vector_returns_zeros():
    # rango = 0 -> división por cero evitada, debe devolver ceros, no NaN.
    x = np.array([5.0, 5.0, 5.0])
    out = _normalize_scores(x)
    assert not np.isnan(out).any()
    assert np.allclose(out, 0.0)


def test_hybrid_score_default_weights_sum_reduces_to_v1():
    # Con w_G=0.0 (default de producción v1), el pagerank no debe influir
    # sin importar su valor -- es exactamente el resultado empírico
    # documentado en graph_analytics_report.md (w_G óptimo = 0.00).
    content = np.array([1.0, 0.0, 0.5])
    cf = np.array([0.2, 0.8, 0.4])
    expiry = np.array([0.0, 1.0, 0.5])
    pagerank_a = np.array([0.9, 0.9, 0.9])
    pagerank_b = np.array([0.1, 0.5, 0.99])

    score_a = hybrid_score(content, cf, expiry, pagerank_a)
    score_b = hybrid_score(content, cf, expiry, pagerank_b)
    assert np.allclose(score_a, score_b)


def test_hybrid_score_weights_matter_when_graph_enabled():
    content = np.array([1.0, 0.0])
    cf = np.array([0.0, 1.0])
    expiry = np.array([0.0, 0.0])
    pagerank = np.array([0.0, 1.0])

    only_content = hybrid_score(content, cf, expiry, pagerank,
                                 w_C=1.0, w_F=0.0, w_E=0.0, w_G=0.0)
    only_graph = hybrid_score(content, cf, expiry, pagerank,
                               w_C=0.0, w_F=0.0, w_E=0.0, w_G=1.0)
    assert np.allclose(only_content, [1.0, 0.0])
    assert np.allclose(only_graph, [0.0, 1.0])


def test_weight_grid_4d_covers_simplex_and_sums_to_one():
    grid = weight_grid_4d(step=0.25)
    assert len(grid) == 35  # documentado en el docstring: step=0.25 -> 35 combinaciones
    for combo in grid:
        assert sum(combo) == pytest.approx(1.0)
        assert all(w >= 0 for w in combo)
    # Los 4 extremos "solo una señal" deben estar presentes.
    assert (1.0, 0.0, 0.0, 0.0) in grid
    assert (0.0, 1.0, 0.0, 0.0) in grid
    assert (0.0, 0.0, 1.0, 0.0) in grid
    assert (0.0, 0.0, 0.0, 1.0) in grid


@pytest.fixture
def toy_inventory() -> pd.DataFrame:
    ref = pd.Timestamp("2026-01-10")
    rows = [
        # household 1, producto 10: compra viva, vence en 2 dias -> score alto
        dict(household_id=1, product_id=10, stock_id="s1", event_type="IN",
             timestamp=ref - pd.Timedelta(days=1),
             expiry_date=ref + pd.Timedelta(days=2)),
        # household 1, producto 20: compra viva, vence en 30 dias -> score bajo
        dict(household_id=1, product_id=20, stock_id="s2", event_type="IN",
             timestamp=ref - pd.Timedelta(days=1),
             expiry_date=ref + pd.Timedelta(days=30)),
        # household 1, producto 40: comprado y consumido por completo -> no debe puntuar
        dict(household_id=1, product_id=40, stock_id="s3", event_type="IN",
             timestamp=ref - pd.Timedelta(days=5),
             expiry_date=ref + pd.Timedelta(days=1)),
        dict(household_id=1, product_id=40, stock_id="s3", event_type="OUT",
             timestamp=ref - pd.Timedelta(days=2),
             expiry_date=ref + pd.Timedelta(days=1)),
        # household 2: inventario sin relación con household 1
        dict(household_id=2, product_id=10, stock_id="s4", event_type="IN",
             timestamp=ref - pd.Timedelta(days=1),
             expiry_date=ref + pd.Timedelta(days=1)),
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def toy_catalog() -> pd.DataFrame:
    return pd.DataFrame({"product_id": [10, 20, 30, 40]})


def test_score_expiry_prioritizes_soon_to_expire_products(toy_inventory, toy_catalog):
    ref = pd.Timestamp("2026-01-10")
    scores = score_expiry(household_id=1, df=toy_inventory, catalog=toy_catalog,
                          ref_date=ref)
    idx = {pid: i for i, pid in enumerate(toy_catalog["product_id"])}

    # Producto 10 (vence en 2 dias) debe puntuar mas alto que el 20 (30 dias).
    assert scores[idx[10]] > scores[idx[20]]
    # Score = 1 / (1 + dias) -- valor exacto verificable.
    assert scores[idx[10]] == pytest.approx(1.0 / (1.0 + 2))
    assert scores[idx[20]] == pytest.approx(1.0 / (1.0 + 30))
    # Producto 30 no esta en el inventario del household -> score 0.
    assert scores[idx[30]] == pytest.approx(0.0)
    # Producto 40 fue consumido por completo (net <= 0) -> no cuenta como vivo.
    assert scores[idx[40]] == pytest.approx(0.0)


def test_score_expiry_household_with_no_inventory_returns_zeros(toy_inventory, toy_catalog):
    ref = pd.Timestamp("2026-01-10")
    scores = score_expiry(household_id=999, df=toy_inventory, catalog=toy_catalog,
                          ref_date=ref)
    assert scores.shape == (len(toy_catalog),)
    assert np.allclose(scores, 0.0)


def test_score_expiry_is_isolated_per_household(toy_inventory, toy_catalog):
    ref = pd.Timestamp("2026-01-10")
    scores_h1 = score_expiry(1, toy_inventory, toy_catalog, ref)
    scores_h2 = score_expiry(2, toy_inventory, toy_catalog, ref)
    idx10 = {pid: i for i, pid in enumerate(toy_catalog["product_id"])}[10]
    # Mismo producto, distinta urgencia por household (2 dias vs 1 dia) -> distinto score.
    assert scores_h1[idx10] != scores_h2[idx10]
