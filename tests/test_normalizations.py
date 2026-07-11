"""
Tests unitarios de `src/normalizations.py` — las 5 normalizaciones de R
documentadas en `data/recommender/README.md`. Usan matrices sintéticas
pequeñas (no dependen de datos generados por el pipeline), verificando el
contrato matemático de cada función, no solo que "no truene".
"""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from normalizations import l2_row, log1p_norm, row_mean_center, summary, tfidf_R


@pytest.fixture
def toy_R() -> sp.csr_matrix:
    # 3 sesiones x 4 productos, densidad ~50%, escalas heterogéneas a propósito.
    dense = np.array(
        [
            [2.0, 0.0, 4.0, 0.0],
            [1.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 3.0],
        ]
    )
    return sp.csr_matrix(dense)


def test_row_mean_center_zeroes_row_mean_of_nonzero_entries(toy_R):
    out = row_mean_center(toy_R).toarray()
    # Fila 0: entradas no-cero [2, 4] -> media 3 -> [-1, 0, 1, 0]
    assert out[0, 0] == pytest.approx(-1.0)
    assert out[0, 2] == pytest.approx(1.0)
    assert out[0, 1] == pytest.approx(0.0)
    # Fila 2: una sola entrada no-cero -> centrada en 0
    assert out[2, 3] == pytest.approx(0.0)


def test_log1p_norm_matches_closed_form(toy_R):
    out = log1p_norm(toy_R).toarray()
    expected = np.log1p(toy_R.toarray())
    assert np.allclose(out, expected)


def test_log1p_norm_preserves_sparsity_pattern(toy_R):
    out = log1p_norm(toy_R)
    assert out.nnz == toy_R.nnz


def test_tfidf_R_penalizes_ubiquitous_products():
    # Producto 0 aparece en las 3 sesiones (ubicuo); producto 1 en 1 sola.
    dense = np.array(
        [
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 1.0],
        ]
    )
    R = sp.csr_matrix(dense)
    out = tfidf_R(R).toarray()
    # A igual conteo (1 evento), el producto ubicuo (col 0) debe puntuar
    # estrictamente menos que un producto raro (col 1) en la misma fila.
    assert out[0, 0] < out[0, 1]


def test_l2_row_produces_unit_norm_rows(toy_R):
    out = l2_row(toy_R).toarray()
    norms = np.linalg.norm(out, axis=1)
    # Todas las filas no vacías deben quedar en norma unitaria.
    assert np.allclose(norms, 1.0)


def test_l2_row_handles_all_zero_row_without_dividing_by_zero():
    R = sp.csr_matrix(np.array([[0.0, 0.0], [1.0, 1.0]]))
    out = l2_row(R).toarray()
    assert not np.isnan(out).any()
    assert np.allclose(out[0], [0.0, 0.0])


def test_summary_reports_expected_keys_and_values(toy_R):
    s = summary(toy_R)
    assert set(s.keys()) == {
        "shape", "nnz", "mean", "std", "min", "max", "median",
    }
    assert s["shape"] == list(toy_R.shape)
    assert s["nnz"] == toy_R.nnz
    assert s["min"] == pytest.approx(1.0)
    assert s["max"] == pytest.approx(4.0)


def test_summary_on_empty_matrix_does_not_crash():
    empty = sp.csr_matrix((2, 2))
    s = summary(empty)
    assert s["nnz"] == 0
    assert s["mean"] == 0.0
