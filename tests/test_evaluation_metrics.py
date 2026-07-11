"""
Test unitario de `precision_recall_map_at_k` en `src/evaluation.py` —
el corazón del protocolo de evaluación (Masked Basket Completion / Cloze
Task) usado para comparar los 6 sistemas del proyecto. Se construye un
escenario sintético de una sola sesión donde el resultado correcto de cada
métrica se puede calcular a mano, para verificar la fórmula, no solo su
ejecución.
"""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from evaluation import precision_recall_map_at_k


def test_precision_recall_map_matches_hand_computed_example():
    # 1 sesion, 5 productos. Columna 0 ya esta en train (debe enmascararse
    # con -inf sin importar su score, para no re-recomendar lo ya visto).
    scores = np.array([[100.0, 5.0, 4.0, 3.0, 2.0]])
    train = sp.csr_matrix(np.array([[1.0, 0.0, 0.0, 0.0, 0.0]]))
    test_by_user = {0: {1, 3}}  # productos 1 y 3 son la verdad oculta

    result = precision_recall_map_at_k(scores, train, test_by_user, k=3)

    # top-3 tras enmascarar la columna 0 -> [1, 2, 3] (por score descendente)
    # hits = {1, 3} interseccion top-3 = {1, 3} -> 2 aciertos
    assert result["precision@k"] == pytest.approx(2 / 3)
    assert result["recall@k"] == pytest.approx(1.0)          # 2 de 2 relevantes recuperados
    assert result["nprecision@k"] == pytest.approx(1.0)      # techo = min(3, 2) = 2
    # MAP: acierto en rank 1 (1/1) y rank 3 (2/3), dividido por techo=2
    assert result["map@k"] == pytest.approx((1 / 1 + 2 / 3) / 2)
    assert result["coverage@k"] == pytest.approx(3 / 5)      # 3 productos distintos recomendados
    assert result["n_eval_sessions"] == 1
    assert result["avg_truth_size"] == pytest.approx(2.0)


def test_masked_train_items_are_never_recommended():
    # Todo el catalogo salvo un item esta en train; el unico item libre debe
    # dominar el top-k sin importar que su score crudo sea bajo.
    scores = np.array([[10.0, 10.0, 10.0, 0.1]])
    train = sp.csr_matrix(np.array([[1.0, 1.0, 1.0, 0.0]]))
    test_by_user = {0: {3}}

    result = precision_recall_map_at_k(scores, train, test_by_user, k=1)
    assert result["recall@k"] == pytest.approx(1.0)
    assert result["precision@k"] == pytest.approx(1.0)


def test_perfect_ranking_yields_map_of_one():
    scores = np.array([[5.0, 4.0, 3.0, 2.0, 1.0]])
    train = sp.csr_matrix((1, 5))
    test_by_user = {0: {0, 1}}  # los dos items mas relevantes son justo el top-2

    result = precision_recall_map_at_k(scores, train, test_by_user, k=2)
    assert result["map@k"] == pytest.approx(1.0)
    assert result["precision@k"] == pytest.approx(1.0)
    assert result["recall@k"] == pytest.approx(1.0)


def test_no_hits_yields_zero_precision_and_map():
    scores = np.array([[5.0, 4.0, 3.0, 2.0, 1.0]])
    train = sp.csr_matrix((1, 5))
    test_by_user = {0: {4}}  # el unico relevante queda fuera del top-2

    result = precision_recall_map_at_k(scores, train, test_by_user, k=2)
    assert result["precision@k"] == pytest.approx(0.0)
    assert result["recall@k"] == pytest.approx(0.0)
    assert result["map@k"] == pytest.approx(0.0)
