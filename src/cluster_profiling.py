"""
Módulo de Perfilado de Clusters (Cluster Profiling — Hito 3, deuda técnica)
Calcula, para cada cluster DBSCAN definitivo, la media de las características
originales y las categorías de producto dominantes. Realiza además un
análisis de fallos (failure analysis) sobre los puntos de ruido (label -1),
respaldando con evidencia trazable las descripciones cualitativas que hoy
solo aparecen de forma ilustrativa en el README.
"""

import json
import os

import numpy as np
import pandas as pd

DAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def load_inputs():
    labels = np.load("data/features/cluster_labels_refined.npy")
    X = np.load("data/features/feature_matrix.npy")
    with open("data/features/feature_names.json", encoding="utf-8") as f:
        feature_names = json.load(f)
    inventory = pd.read_csv("data/processed/inventory_v1.csv")

    if not (len(labels) == X.shape[0] == len(inventory)):
        raise ValueError(
            f"Desalineación de filas entre artefactos: "
            f"labels={len(labels)}, feature_matrix={X.shape[0]}, inventory={len(inventory)}"
        )

    inventory = inventory.reset_index(drop=True)
    inventory["timestamp"] = pd.to_datetime(inventory["timestamp"])
    inventory["hour_of_day"] = inventory["timestamp"].dt.hour
    inventory["day_of_week"] = inventory["timestamp"].dt.dayofweek

    return labels, X, feature_names, inventory


def profile_cluster(cluster_id, mask, X, feature_names, inventory, global_mean):
    n = int(mask.sum())
    total = mask.shape[0]

    cluster_mean = X[mask].mean(axis=0)
    deviation = cluster_mean - global_mean
    top_idx = int(np.argmax(np.abs(deviation)))

    categories = inventory.loc[mask, "category"].to_numpy()
    cat_counts = pd.Series(categories).value_counts()
    top_categories = [
        (int(cat), count, count / n * 100) for cat, count in cat_counts.head(3).items()
    ]

    mean_hour = float(inventory.loc[mask, "hour_of_day"].mean())
    dominant_day = DAY_NAMES[int(inventory.loc[mask, "day_of_week"].mode().iloc[0])]
    dominant_share = top_categories[0][2] if top_categories else float("nan")

    return {
        "cluster": cluster_id,
        "n": n,
        "pct_total": n / total * 100,
        "n_distinct_categories": int(cat_counts.shape[0]),
        "top_categories": top_categories,
        "dominant_category_share": dominant_share,
        "top_feature": feature_names[top_idx],
        "top_feature_dev": float(deviation[top_idx]),
        "mean_hour": mean_hour,
        "dominant_day": dominant_day,
    }


def format_top_categories(top_categories):
    if not top_categories:
        return "—"
    return ", ".join(f"category_{cat} ({pct:.1f}%)" for cat, _, pct in top_categories)


def build_cluster_table(profiles):
    lines = [
        "| Cluster | N | % Total | Categorías Dominantes (top 3) | Feature Más Distintivo (Δ vs. media global) | Hora Media | Día Dominante |",
        "| :--- | ---: | ---: | :--- | :--- | ---: | :--- |",
    ]
    for p in profiles:
        lines.append(
            f"| {p['cluster']} | {p['n']} | {p['pct_total']:.2f}% "
            f"| {format_top_categories(p['top_categories'])} "
            f"| `{p['top_feature']}` ({p['top_feature_dev']:+.2f}) "
            f"| {p['mean_hour']:.1f}h | {p['dominant_day']} |"
        )
    return "\n".join(lines)


def build_failure_analysis(mask_noise, X, feature_names, inventory, global_mean, cluster_profiles):
    total = mask_noise.shape[0]
    n_noise = int(mask_noise.sum())

    noise_profile = profile_cluster(-1, mask_noise, X, feature_names, inventory, global_mean)

    real_dominances = [p["dominant_category_share"] for p in cluster_profiles]
    avg_real_dominance = float(np.mean(real_dominances))

    quantity_noise_mean = float(inventory.loc[mask_noise, "quantity"].mean())
    quantity_global_mean = float(inventory["quantity"].mean())

    real_n_categories = [p["n_distinct_categories"] for p in cluster_profiles]
    avg_real_n_categories = float(np.mean(real_n_categories))

    return {
        "n_noise": n_noise,
        "pct_noise": n_noise / total * 100,
        "profile": noise_profile,
        "avg_real_dominance": avg_real_dominance,
        "avg_real_n_categories": avg_real_n_categories,
        "quantity_noise_mean": quantity_noise_mean,
        "quantity_global_mean": quantity_global_mean,
    }


def build_failure_section(failure):
    p = failure["profile"]
    dominance_gap = failure["avg_real_dominance"] - p["dominant_category_share"]
    category_spread_gap = p["n_distinct_categories"] - failure["avg_real_n_categories"]
    quantity_gap = failure["quantity_noise_mean"] - failure["quantity_global_mean"]

    if p["dominant_category_share"] < 60:
        dominance_note = (
            f"el ruido no tiene una categoría dominante clara: la más frecuente concentra solo "
            f"{p['dominant_category_share']:.1f}% de sus puntos, frente a un promedio de "
            f"{failure['avg_real_dominance']:.1f}% en los clusters reales."
        )
    elif dominance_gap > 5:
        dominance_note = (
            f"el ruido sigue teniendo una categoría mayoritaria ({p['dominant_category_share']:.1f}%), "
            f"pero **menos concentrada** que el promedio de los clusters reales "
            f"({failure['avg_real_dominance']:.1f}%), es decir, mezcla proporcionalmente más categorías "
            "minoritarias que un cluster típico."
        )
    else:
        dominance_note = (
            f"la concentración de categoría dominante en el ruido ({p['dominant_category_share']:.1f}%) "
            f"es comparable a la de los clusters reales (promedio {failure['avg_real_dominance']:.1f}%), "
            "por lo que la categoría de producto por sí sola no explica la caída en ruido."
        )

    if category_spread_gap > 0.5:
        spread_note = (
            f"Los puntos de ruido mezclan {p['n_distinct_categories']} categorías distintas, "
            f"más que el promedio de {failure['avg_real_n_categories']:.1f} categorías por cluster real, "
            "consistente con una mezcla heterogénea de eventos que no encajan en ninguna densidad local."
        )
    else:
        spread_note = (
            f"El número de categorías presentes en el ruido ({p['n_distinct_categories']}) es similar "
            f"al promedio de los clusters reales ({failure['avg_real_n_categories']:.1f})."
        )

    if abs(quantity_gap) >= 0.05:
        direction = "mayor" if quantity_gap > 0 else "menor"
        quantity_note = (
            f"La cantidad (`quantity`) media en el ruido es {failure['quantity_noise_mean']:.3f}, "
            f"{direction} que la media global ({failure['quantity_global_mean']:.3f}), sugiriendo que "
            "eventos con volúmenes de movimiento atípicos contribuyen a la caída en ruido."
        )
    else:
        quantity_note = (
            f"La cantidad (`quantity`) media en el ruido ({failure['quantity_noise_mean']:.3f}) no difiere "
            f"de forma relevante de la media global ({failure['quantity_global_mean']:.3f}), por lo que el "
            "volumen de movimiento no parece ser la causa principal del ruido."
        )

    return f"""## 3. Análisis de Fallos (Ruido, label = -1)

DBSCAN clasificó **{failure['n_noise']} eventos ({failure['pct_noise']:.2f}% del total)** como ruido
(label `-1`), es decir, puntos que no alcanzan la densidad mínima (`min_samples=15`) dentro del radio
`eps=2.7` de ningún cluster.

- **Categorías dominantes en el ruido:** {format_top_categories(p['top_categories'])}
- **Feature más distintivo del ruido:** `{p['top_feature']}` (Δ={p['top_feature_dev']:+.2f} vs. media global)
- **Hora media de los eventos de ruido:** {p['mean_hour']:.1f}h — **Día dominante:** {p['dominant_day']}

**Hipótesis de causa:**

1. {dominance_note}
2. {spread_note}
3. {quantity_note}

En conjunto, el ruido no se explica por una única variable, sino por combinaciones poco frecuentes
de categoría, franja horaria y volumen de movimiento que no forman una vecindad densa suficiente
según los hiperparámetros del modelo ganador (DBSCAN, eps=2.7, min_samples=15).
"""


def build_report(profiles, failure, n_total, n_clusters):
    header = f"""# Perfiles de Clusters DBSCAN (Hito 3 — Cluster Profiling)

> Generado automáticamente por `src/cluster_profiling.py`. Fuentes: `data/features/cluster_labels_refined.npy`,
> `data/features/feature_matrix.npy`, `data/features/feature_names.json`, `data/processed/inventory_v1.csv`.
> No contiene datos de relleno: cada cifra se calcula directamente sobre la distribución real de clusters.

## 1. Resumen General

- Eventos totales: **{n_total}**
- Clusters identificados (excluyendo ruido): **{n_clusters}**
- Puntos de ruido (label -1): **{failure['n_noise']}** ({failure['pct_noise']:.2f}% del total)

## 2. Perfil por Cluster

Para cada cluster se reporta el tamaño, las hasta 3 categorías de producto más frecuentes
(`category_<id>`, identificador USDA/Instacart del catálogo — no existe un mapeo textual de
categorías en el repositorio), la característica original con mayor desviación respecto a la
media global del dataset (`Δ` en unidades estandarizadas, ya que `feature_matrix.npy` está escalado
con `StandardScaler`), y el patrón temporal dominante.

{build_cluster_table(profiles)}

"""
    return header + build_failure_section(failure)


def main():
    print("Iniciando Cluster Profiling (Hito 3 — deuda técnica de perfilado)...")
    labels, X, feature_names, inventory = load_inputs()

    global_mean = X.mean(axis=0)
    unique_labels = sorted(l for l in set(labels.tolist()) if l != -1)
    print(f"Clusters detectados: {len(unique_labels)} (+ ruido si aplica)")

    profiles = []
    for cluster_id in unique_labels:
        mask = labels == cluster_id
        profiles.append(profile_cluster(cluster_id, mask, X, feature_names, inventory, global_mean))

    mask_noise = labels == -1
    failure = build_failure_analysis(mask_noise, X, feature_names, inventory, global_mean, profiles)

    report = build_report(profiles, failure, n_total=len(labels), n_clusters=len(unique_labels))

    out_path = "reports/cluster_profiles.md"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("-" * 40)
    print("Cluster Profiling Completado")
    print(f"Clusters perfilados: {len(profiles)}")
    print(f"Puntos de ruido: {failure['n_noise']} ({failure['pct_noise']:.2f}%)")
    print(f"Reporte exportado en: {out_path}")
    print("-" * 40)


if __name__ == "__main__":
    main()
