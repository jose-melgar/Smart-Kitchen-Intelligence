"""
run_pipeline.py — Orquestador de un solo comando para el pipeline SKI.

Reemplaza la ejecución manual de los 20+ comandos documentados en
`runbook.md` por un único punto de entrada, reduciendo el riesgo de que la
demo en vivo de la defensa final se rompa por un paso saltado, un orden
incorrecto o un typo (criterio "-50 puntos si algo está roto" de Semana 14).

Uso:
    python run_pipeline.py                  # corre todo el pipeline (Hito 1-6)
    python run_pipeline.py --list           # lista las etapas sin ejecutar nada
    python run_pipeline.py --stage hito4     # corre solo un hito
    python run_pipeline.py --from hito4      # corre desde un hito en adelante
    python run_pipeline.py --skip-ingestion  # empieza en preprocessing.py
                                              # (usa data/raw/ ya existente;
                                              # evita requerir credenciales
                                              # de Kaggle/USDA en la defensa)

Cada etapa se ejecuta como `python src/<script>.py` desde la raíz del repo
(igual que exige el runbook), en un subproceso propio, y el orquestador
aborta con un mensaje claro en el primer fallo — no continúa a ciegas.
Al final imprime una tabla de tiempos por script, el mismo dato que
`PLAN_MAESTRO_ENTREGA_FINAL.md` (Fase 7) pedía dejar documentado como
evidencia de una corrida limpia.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# La consola de Windows (cmd/PowerShell) no usa UTF-8 por defecto y mangla
# tildes/ñ en el output de este script; forzarlo evita que un caracter no
# imprimible rompa el print() en medio de una demo en vivo.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# Cada etapa: (script, descripcion, requiere_credenciales)
Stage = tuple[str, str, bool]

HITOS: dict[str, list[Stage]] = {
    "hito1": [
        ("extract_patterns.py", "Patrones de compra desde Instacart (Kaggle)", True),
        ("simulation.py", "Simulación de movimientos de inventario (90 días)", False),
        ("ingestion.py", "Enriquecimiento nutricional (USDA API, con fallback mock)", True),
        ("preprocessing.py", "ETL -> data/processed/inventory_v1.csv", False),
    ],
    "hito2": [
        ("features.py", "Feature engineering -> feature_matrix.npy", False),
        ("reduction.py", "PCA (30 comp., 90% var.) + t-SNE", False),
    ],
    "hito3": [
        ("clustering.py", "Benchmark K-Means/GMM/DBSCAN", False),
        ("clustering_refinement.py", "DBSCAN refinado -> cluster_labels_refined.npy", False),
    ],
    "hito4": [
        ("build_R.py", "Matrices de interacción R (10 variantes)", False),
        ("recommender_content.py", "Capa de contenido TF-IDF", False),
        ("normalizations.py", "5 normalizaciones de R", False),
        ("recommender_cf.py", "ALS implícito + barrido de lambda", False),
        ("cold_start.py", "Estrategias de arranque en frío", False),
        ("recommender_hybrid.py", "Ensamble híbrido v1/v2 + ablación 4D", False),
        ("evaluation.py", "Protocolo de evaluación consolidado (6 sistemas)", False),
        ("generate_hito4_figures.py", "Figuras de Hito 4", False),
    ],
    "hito5": [
        ("graph_construction.py", "Grafo de co-ocurrencia (R^T R) -> GEXF", False),
        ("graph_analytics.py", "Componentes conexas, grado, PageRank", False),
        ("generate_hito5_figures.py", "Figuras de Hito 5", False),
    ],
    "hito6": [
        ("cluster_profiling.py", "Perfiles de cluster + failure analysis", False),
        ("recommender_hybrid.py", "Re-ablación 4D con grafo (hybrid_v2_graph)", False),
        ("evaluation.py", "Re-evaluación de los 6 sistemas", False),
    ],
}

STAGE_ORDER = ["hito1", "hito2", "hito3", "hito4", "hito5", "hito6"]

# Scripts explícitamente fuera del pipeline batch (no generan artefactos
# nuevos / no son deterministas / requieren red de terceros) — se listan
# para que quien lea este archivo sepa que la omisión es intencional, no
# un olvido.
EXCLUDED = {
    "demo_app.py": "Streamlit, solo lectura de artefactos ya generados. "
                    "Correr manualmente con: streamlit run src/demo_app.py",
    "translate_catalog.py": "Utilidad puntual (traduce el catálogo vía Google "
                             "Translate). No determinista / requiere red externa; "
                             "no forma parte de la reproducibilidad científica del "
                             "pipeline. Correr manualmente si se necesita.",
}


def flatten(stage_names: list[str]) -> list[tuple[str, Stage]]:
    return [(hito, s) for hito in stage_names for s in HITOS[hito]]


def run_stage(hito: str, stage: Stage) -> float:
    script, desc, needs_creds = stage
    script_path = SRC / script
    if not script_path.exists():
        print(f"[FALLO] {script} no existe en src/")
        sys.exit(1)

    print(f"\n{'=' * 70}\n[{hito}] {script} — {desc}\n{'=' * 70}")
    t0 = time.time()
    result = subprocess.run([sys.executable, str(script_path)], cwd=ROOT)
    elapsed = time.time() - t0

    if result.returncode != 0:
        hint = (
            " (requiere credenciales: ~/.kaggle/kaggle.json y/o .env con "
            "USDA_API_KEY — ver runbook.md §1.2)" if needs_creds else ""
        )
        print(f"\n[FALLO] {script} terminó con código {result.returncode}{hint}")
        print("Pipeline detenido. Corrige el error antes de continuar "
              "(no se avanza a ciegas al siguiente paso).")
        sys.exit(result.returncode)

    print(f"[ok] {script} completado en {elapsed:.1f}s")
    return elapsed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Orquestador de un solo comando para el pipeline SKI.")
    parser.add_argument("--list", action="store_true",
                        help="Lista las etapas y sale, sin ejecutar nada.")
    parser.add_argument("--stage", choices=STAGE_ORDER,
                        help="Corre solo un hito.")
    parser.add_argument("--from", dest="from_stage", choices=STAGE_ORDER,
                        help="Corre desde este hito hasta el final.")
    parser.add_argument("--skip-ingestion", action="store_true",
                        help="Salta extract_patterns.py/ingestion.py "
                             "(requieren credenciales Kaggle/USDA); usa "
                             "data/raw/ ya existente y arranca en simulation.py "
                             "de todas formas si ya tienes instacart_patterns.json, "
                             "o directamente en preprocessing.py si data/raw/ "
                             "ya está completo.")
    args = parser.parse_args()

    if args.stage:
        stages_to_run = [args.stage]
    elif args.from_stage:
        idx = STAGE_ORDER.index(args.from_stage)
        stages_to_run = STAGE_ORDER[idx:]
    else:
        stages_to_run = STAGE_ORDER

    plan = flatten(stages_to_run)

    if args.skip_ingestion:
        plan = [(h, s) for h, s in plan if s[0] not in
                {"extract_patterns.py", "ingestion.py"}]

    if args.list:
        print("Plan de ejecución:\n")
        for hito, (script, desc, needs_creds) in plan:
            flag = " [requiere credenciales]" if needs_creds else ""
            print(f"  [{hito}] {script:<28} {desc}{flag}")
        print("\nExcluidos del pipeline batch (correr manualmente si se necesitan):")
        for script, why in EXCLUDED.items():
            print(f"  {script:<28} {why}")
        return

    print(f"Ejecutando {len(plan)} scripts desde la raíz: {ROOT}")
    t_start = time.time()
    timings: list[tuple[str, float]] = []
    for hito, stage in plan:
        elapsed = run_stage(hito, stage)
        timings.append((stage[0], elapsed))
    total = time.time() - t_start

    print(f"\n{'=' * 70}\nResumen de tiempos\n{'=' * 70}")
    for script, elapsed in timings:
        print(f"  {script:<28} {elapsed:>8.1f}s")
    print(f"  {'TOTAL':<28} {total:>8.1f}s")
    print(f"\nPipeline completo. {len(plan)} scripts ejecutados sin errores.")


if __name__ == "__main__":
    main()
