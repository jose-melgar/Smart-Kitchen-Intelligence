"""
recommender_content.py — Hito 4 (Semana 11): recomendador basado en contenido.

Análogo del recomendador de Semana 9 ("Pachamix Lyrics"): en SKI, el "texto" de
cada ítem son los atributos *nominales* del producto (nombre, categoría,
clasificación de evento). TF-IDF construye un vector disperso por producto que
pondera tokens raros y penaliza los muy comunes.

Representación HÍBRIDA texto + numérico (corrección de la observación del
revisor sobre ortogonalidad):
  Las variables nutricionales (calories/proteins/carbs) y el nutriscore son
  variables ORDINALES/CONTINUAS. Discretizarlas en tokens independientes
  (cal_low/cal_mid/cal_high) hacía que TF-IDF las tratase como dimensiones
  estrictamente ortogonales — la distancia entre cal_low y cal_mid resultaba
  idéntica a la distancia entre cal_low y cal_high, perdiéndose la noción de
  orden e intervalo. La corrección: cada macro entra como UNA sola dimensión
  numérica escalada (MinMax) y el nutriscore como un eje ordinal (A→E).
  Estas dimensiones se concatenan al bloque TF-IDF y todo el vector se
  L2-normaliza, de modo que cal=180 y cal=190 quedan próximos mientras que
  cal=50 y cal=900 quedan lejos, preservando intervalo y orden.

Pipeline:
  1. Agregar atributos por producto (group by product_id).
  2. Bloque textual: TF-IDF sobre nombre + categoría + clasificación.
  3. Bloque numérico: macros continuas + nutriscore ordinal, escalados.
  4. Concatenar ambos bloques y L2-normalizar (cosine = dot product).
  5. Perfil de household = centroide ponderado por frecuencia de consumo.
  6. Recomendar top-N por similitud coseno, excluyendo productos consumidos.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, normalize
import scipy.sparse as sp

# Orden canónico del nutriscore (A = más saludable → E = menos saludable).
NUTRI_ORDER = {"a": 0.0, "b": 1.0, "c": 2.0, "d": 3.0, "e": 4.0}
# Columnas numéricas continuas tratadas como ejes ordenados.
MACRO_COLS = ["calories_100g", "proteins_100g", "carbs_100g"]
# Peso relativo del bloque numérico frente al bloque TF-IDF (ver build_item_matrix).
NUMERIC_WEIGHT = 0.5

ROOT = Path(__file__).resolve().parents[1]
DATA_PROC = ROOT / "data" / "processed" / "inventory_v1.csv"
OUT_DIR = ROOT / "data" / "recommender"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Catálogo de productos: texto descriptivo por producto
# ---------------------------------------------------------------------------

def build_product_catalog(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye un catálogo único por producto agregando atributos.
    El campo `doc` es el "documento" que TF-IDF vectorizará.
    """
    # group by producto: tomamos modo / primer valor de campos categóricos
    agg = (
        df.groupby("product_id")
        .agg(
            product_name=("product_name", "first"),
            category=("category", "first"),
            classification=("classification", lambda s: s.mode().iloc[0] if not s.mode().empty else ""),
            nutriscore=("nutriscore", lambda s: s.mode().iloc[0] if not s.mode().empty else ""),
            calories_100g=("calories_100g", "mean"),
            proteins_100g=("proteins_100g", "mean"),
            carbs_100g=("carbs_100g", "mean"),
        )
        .reset_index()
    )

    # Bloque TEXTUAL: solo atributos genuinamente nominales (sin orden interno).
    # Las macros y el nutriscore NO se tokenizan aquí: entran como dimensiones
    # numéricas ordenadas en build_item_matrix() para no romper su intervalo.
    def make_doc(row) -> str:
        tokens = [
            str(row["product_name"]).lower(),
            f"category_{row['category']}",
            f"class_{str(row['classification']).lower()}",
        ]
        return " ".join(t for t in tokens if t)

    agg["doc"] = agg.apply(make_doc, axis=1)

    # Eje ordinal del nutriscore (A→E). Se conserva como columna numérica.
    agg["nutri_ord"] = (
        agg["nutriscore"].astype(str).str.lower().map(NUTRI_ORDER)
    )
    return agg


# ---------------------------------------------------------------------------
# 2. TF-IDF
# ---------------------------------------------------------------------------

def fit_tfidf(docs: list[str], min_df: int = 1, max_df: float = 0.95) -> tuple:
    """
    Ajusta TF-IDF sobre los documentos del catálogo de productos.

    Recordatorio matemático para defender en la presentación:
      tf(t, d)        = nº de veces que el token t aparece en doc d
      idf(t)          = log( (1 + N) / (1 + df(t)) ) + 1   (sublinear + smooth)
      tfidf(t, d)     = tf(t,d) * idf(t)
      Luego cada fila se L2-normaliza, así cosine_sim = dot product.

    IDF penaliza tokens comunes (ej. "organic" aparece en muchos productos →
    df alto → idf bajo) y premia tokens raros y discriminantes
    (ej. "cilantro", "category_8") que aportan más información al perfil.
    """
    vectorizer = TfidfVectorizer(
        lowercase=True,
        token_pattern=r"(?u)\b\w[\w_]+\b",
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=True,
        norm="l2",
        smooth_idf=True,
    )
    X = vectorizer.fit_transform(docs)
    return vectorizer, X


def build_numeric_block(catalog: pd.DataFrame,
                        numeric_weight: float = NUMERIC_WEIGHT) -> tuple:
    """
    Bloque numérico de features de contenido: macros continuas + nutriscore
    ordinal, escalados a [0,1] con MinMax. Cada variable física ocupa UNA sola
    dimensión ordenada (no tres tokens ortogonales), de forma que la distancia
    euclídea/coseno respeta el intervalo real: |cal=180 − cal=190| ≪ |cal=50 −
    cal=900|. Devuelve (X_num_sparse, scaler, col_names).
    """
    cols = MACRO_COLS + ["nutri_ord"]
    num = catalog[cols].astype(float).copy()
    # Imputación por mediana para no introducir un nivel ficticio.
    num = num.fillna(num.median(numeric_only=True))
    scaler = MinMaxScaler()
    num_scaled = scaler.fit_transform(num.values)
    X_num = sp.csr_matrix(num_scaled.astype(np.float64) * float(numeric_weight))
    return X_num, scaler, cols


def build_item_matrix(catalog: pd.DataFrame,
                      numeric_weight: float = NUMERIC_WEIGHT,
                      min_df: int = 1, max_df: float = 0.95) -> tuple:
    """
    Matriz de ítems HÍBRIDA: [bloque TF-IDF textual | bloque numérico escalado],
    L2-normalizada por fila para que cosine_similarity == dot product.

    El parámetro `numeric_weight` controla cuánto pesa el bloque numérico frente
    al textual. Esta representación corrige la ruptura de continuidad: las macros
    dejan de ser tokens ortogonales (cal_low/cal_mid/cal_high) y pasan a ser ejes
    continuos donde se preservan orden e intervalo.

    Devuelve (vectorizer, X, scaler, num_cols).
    """
    vectorizer, X_text = fit_tfidf(catalog["doc"].tolist(), min_df=min_df, max_df=max_df)
    X_num, scaler, num_cols = build_numeric_block(catalog, numeric_weight)
    X = sp.hstack([X_text, X_num], format="csr")
    X = normalize(X, norm="l2", axis=1)
    return vectorizer, X, scaler, num_cols


# ---------------------------------------------------------------------------
# 3. Perfil de household
# ---------------------------------------------------------------------------

def build_household_profile(
    household_id: int,
    df_events: pd.DataFrame,
    catalog: pd.DataFrame,
    X_items: sp.csr_matrix,
    use_out_only: bool = True,
) -> sp.csr_matrix:
    """
    Perfil del household = promedio ponderado por frecuencia de consumo de los
    vectores TF-IDF de los productos que ha consumido (eventos OUT por defecto).
    """
    ev = df_events[df_events["household_id"] == household_id]
    if use_out_only:
        ev = ev[ev["event_type"] == "OUT"]
    if ev.empty:
        return sp.csr_matrix(X_items.mean(axis=0))

    counts = ev["product_id"].value_counts().to_dict()
    pid_to_idx = {p: i for i, p in enumerate(catalog["product_id"].tolist())}
    rows, weights = [], []
    for pid, c in counts.items():
        if pid in pid_to_idx:
            rows.append(pid_to_idx[pid])
            weights.append(float(c))
    if not rows:
        return sp.csr_matrix(X_items.mean(axis=0))

    w = np.asarray(weights)
    w = w / w.sum()
    profile = (sp.diags(w) @ X_items[rows]).sum(axis=0)
    return sp.csr_matrix(profile)


# ---------------------------------------------------------------------------
# 4. Scoring y top-N
# ---------------------------------------------------------------------------

def score_catalog(profile: sp.csr_matrix, X_items: sp.csr_matrix) -> np.ndarray:
    """Cosine similarity entre perfil y todos los productos."""
    sims = cosine_similarity(profile, X_items).flatten()
    return sims


def top_n(
    scores: np.ndarray,
    catalog: pd.DataFrame,
    exclude_ids: set[int] | None = None,
    n: int = 10,
    group_by_category: bool = True,
) -> pd.DataFrame:
    """
    Devuelve top-N productos con scoring decreciente.
    `group_by_category` evita saturar con el mismo tipo de producto.
    """
    exclude_ids = exclude_ids or set()
    cat = catalog.copy()
    cat["score"] = scores
    cat = cat[~cat["product_id"].isin(exclude_ids)].sort_values("score", ascending=False)
    if group_by_category:
        cat = cat.groupby("category", group_keys=False).head(max(1, n // 4))
        cat = cat.sort_values("score", ascending=False)
    return cat.head(n)[["product_id", "product_name", "category", "nutriscore", "score"]]


# ---------------------------------------------------------------------------
# 5. Demo / persistencia
# ---------------------------------------------------------------------------

def main() -> None:
    # (regenera la matriz híbrida de contenido + artefactos derivados)
    df = pd.read_csv(DATA_PROC, parse_dates=["timestamp", "expiry_date"])
    catalog = build_product_catalog(df)
    print(f"[content] Catálogo: {len(catalog)} productos.")

    vec, X, scaler, num_cols = build_item_matrix(catalog, numeric_weight=NUMERIC_WEIGHT)
    n_text = len(vec.vocabulary_)
    print(f"[content] Matriz híbrida: shape={X.shape} "
          f"(texto={n_text} tokens + numérico={len(num_cols)} dims: {num_cols})")
    print(f"[content] Bloque numérico con peso={NUMERIC_WEIGHT} "
          f"(macros MinMax + nutriscore ordinal A->E).")
    print(f"[content] Tokens con menor IDF (más comunes): ", end="")
    idf = vec.idf_
    vocab_inv = {i: t for t, i in vec.vocabulary_.items()}
    bottom = np.argsort(idf)[:6]
    print(", ".join(f"{vocab_inv[i]}({idf[i]:.2f})" for i in bottom))
    top = np.argsort(idf)[-6:]
    print(f"[content] Tokens con mayor IDF (raros, discriminantes): ", end="")
    print(", ".join(f"{vocab_inv[i]}({idf[i]:.2f})" for i in top))

    # tfidf_items.npz ahora es la matriz híbrida texto+numérico (la que usan el
    # híbrido y la evaluación para la similitud de contenido).
    sp.save_npz(OUT_DIR / "tfidf_items.npz", X)
    with open(OUT_DIR / "tfidf_vocab.json", "w") as f:
        json.dump(vec.vocabulary_, f)
    with open(OUT_DIR / "content_features_meta.json", "w") as f:
        json.dump({
            "representation": "hybrid_tfidf_text + scaled_numeric",
            "text_block": {"n_tokens": n_text,
                           "fields": ["product_name", "category", "classification"]},
            "numeric_block": {"columns": num_cols,
                              "scaler": "MinMax[0,1]",
                              "nutriscore_encoding": NUTRI_ORDER,
                              "numeric_weight": NUMERIC_WEIGHT},
            "note": ("Las macros continuas y el nutriscore ordinal entran como "
                     "ejes numéricos ordenados (no tokens ortogonales), "
                     "preservando orden e intervalo; el vector completo se "
                     "L2-normaliza para que cosine == dot product.")
        }, f, indent=2)
    catalog.to_csv(OUT_DIR / "product_catalog.csv", index=False)

    # Item-item similarity (contenido): se reutiliza en el híbrido y la comparación.
    item_sim_content = cosine_similarity(X)
    np.save(OUT_DIR / "item_sim_content.npy", item_sim_content)
    print(f"[content] Item-item similarity (contenido) guardada.")

    # Demo: top-5 con hold-out de 20% del historial del household 0.
    rng = np.random.default_rng(42)
    hh0_out = df[(df["household_id"] == 0) & (df["event_type"] == "OUT")]["product_id"].unique()
    hidden = set(rng.choice(hh0_out, size=max(1, len(hh0_out) // 5), replace=False))
    print(f"\n[content] Demo hold-out: ocultando {len(hidden)}/{len(hh0_out)} productos al household 0.")

    df_visible = df[~((df["household_id"] == 0) & (df["product_id"].isin(hidden)))]
    profile = build_household_profile(0, df_visible, catalog, X)
    sims = score_catalog(profile, X)
    consumed_visible = set(
        df_visible[(df_visible["household_id"] == 0)
                   & (df_visible["event_type"] == "OUT")]["product_id"].unique()
    )
    rec = top_n(sims, catalog, exclude_ids=consumed_visible, n=5)
    rec["hit"] = rec["product_id"].isin(hidden)
    print("[content] Top-5 (excluyendo visibles) — 'hit'=acertó un producto oculto:")
    print(rec.to_string(index=False))


if __name__ == "__main__":
    main()
