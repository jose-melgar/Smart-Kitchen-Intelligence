"""
recommender_content.py — Hito 4 (Semana 11): recomendador basado en contenido.

Análogo del recomendador de Semana 9 ("Pachamix Lyrics"): en SKI, el "texto" de
cada ítem son los atributos descriptivos del producto (nombre, categoría,
clasificación de evento, nutriscore como token). TF-IDF construye un vector
disperso por producto que pondera tokens raros y penaliza los muy comunes.

Pipeline:
  1. Concatenar atributos textuales por producto (group by product_id).
  2. Tokenizar y vectorizar con TF-IDF (term-frequency × IDF).
  3. Construir el perfil de un household como centroide (TF-IDF promedio) de
     los productos que ha consumido históricamente.
  4. Recomendar top-N por similitud coseno entre perfil y catálogo, excluyendo
     productos ya consumidos.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import scipy.sparse as sp

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

    def macro_bucket(v, edges, names):
        if pd.isna(v):
            return ""
        for e, n in zip(edges, names):
            if v <= e:
                return n
        return names[-1]

    # Discretizamos macros en tokens (low/mid/high) para que TF-IDF los capture.
    agg["cal_token"] = agg["calories_100g"].apply(
        lambda v: macro_bucket(v, [50, 200, 1000], ["cal_low", "cal_mid", "cal_high"])
    )
    agg["prot_token"] = agg["proteins_100g"].apply(
        lambda v: macro_bucket(v, [2, 10, 100], ["prot_low", "prot_mid", "prot_high"])
    )
    agg["carb_token"] = agg["carbs_100g"].apply(
        lambda v: macro_bucket(v, [5, 20, 100], ["carb_low", "carb_mid", "carb_high"])
    )

    def make_doc(row) -> str:
        tokens = [
            str(row["product_name"]).lower(),
            f"category_{row['category']}",
            f"class_{str(row['classification']).lower()}",
            f"nutri_{str(row['nutriscore']).lower()}",
            row["cal_token"],
            row["prot_token"],
            row["carb_token"],
        ]
        return " ".join(t for t in tokens if t)

    agg["doc"] = agg.apply(make_doc, axis=1)
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
    df = pd.read_csv(DATA_PROC, parse_dates=["timestamp", "expiry_date"])
    catalog = build_product_catalog(df)
    print(f"[content] Catálogo: {len(catalog)} productos.")

    vec, X = fit_tfidf(catalog["doc"].tolist())
    print(f"[content] TF-IDF: vocabulario={len(vec.vocabulary_)}, shape={X.shape}")
    print(f"[content] Tokens con menor IDF (más comunes): ", end="")
    idf = vec.idf_
    vocab_inv = {i: t for t, i in vec.vocabulary_.items()}
    bottom = np.argsort(idf)[:6]
    print(", ".join(f"{vocab_inv[i]}({idf[i]:.2f})" for i in bottom))
    top = np.argsort(idf)[-6:]
    print(f"[content] Tokens con mayor IDF (raros, discriminantes): ", end="")
    print(", ".join(f"{vocab_inv[i]}({idf[i]:.2f})" for i in top))

    sp.save_npz(OUT_DIR / "tfidf_items.npz", X)
    with open(OUT_DIR / "tfidf_vocab.json", "w") as f:
        json.dump(vec.vocabulary_, f)
    catalog.to_csv(OUT_DIR / "product_catalog.csv", index=False)

    # Item-item similarity (contenido): se reutiliza en el híbrido y la comparación.
    item_sim_content = cosine_similarity(X)
    np.save(OUT_DIR / "item_sim_content.npy", item_sim_content)
    print(f"[content] Item-item similarity (contenido) guardada.")

    # Demo: top-5 con hold-out de 20% del historial del household 0.
    # (En SKI todos los households han tocado los 50 productos al menos una vez;
    # para una demo realista se simula que parte del historial es desconocido.)
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
"\n[content] Demo hold-out: ocultando {len(hidden)}/{len(hh0_out)} productos al household 0.")

    df_visible = df[~((df["household_id"] == 0) & (df["product_id"].isin(hidden)))]
    profile = build_household_profile(0, df_visible, catalog, X)
    sims = score_catalog(profile, X)
    consumed_visible = set(
        df_visible[(df_visible["household_id"] == 0) &
                   (df_visible["event_type"] == "OUT")]["product_id"].unique()
    )
    rec = top_n(sims, catalog, exclude_ids=consumed_visible, n=5)
    rec["hit"] = rec["product_id"].isin(hidden)
    print(f"[content] Top-5 (excluyendo visibles) — 'hit'=acertó un producto oculto:")
    print(rec.to_string(index=False))


if __name__ == "__main__":
    main()
