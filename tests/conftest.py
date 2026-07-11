"""
Configuración compartida de pytest para el proyecto SKI.

Añade `src/` al path para poder hacer `import recommender_hybrid`, etc.
directamente en los tests, igual que los propios scripts hacen entre sí
(ver `evaluation.py`, que inserta `src/` en `sys.path` para importar
`recommender_cf`).

Todos los tests que dependen de artefactos generados por el pipeline
(`data/features/*.npy`, `data/recommender/*`) se saltan automáticamente
(no fallan) si el artefacto no existe todavía — así `pytest` es utilizable
tanto en un clon fresco (antes de correr el pipeline) como después de una
corrida completa. La lógica de negocio pura (normalizaciones, scoring,
métricas, grafo) se testea siempre, sin depender de datos en disco.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def data_features() -> Path:
    return ROOT / "data" / "features"


@pytest.fixture(scope="session")
def data_recommender() -> Path:
    return ROOT / "data" / "recommender"


@pytest.fixture(scope="session")
def data_processed() -> Path:
    return ROOT / "data" / "processed"


def require_artifact(path: Path) -> Path:
    """Salta el test (no lo falla) si el artefacto del pipeline no existe."""
    if not path.exists():
        pytest.skip(f"Artefacto no generado todavía: {path.relative_to(ROOT)} "
                     f"(correr el pipeline, ver runbook.md)")
    return path
