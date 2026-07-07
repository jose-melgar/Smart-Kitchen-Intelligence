# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Smart Kitchen Intelligence (SKI) is a UPC Big Data course project (2-person team: Gabriel Reyna Alvarado, José Melgar Puertas), not a production application. It is a sequential, script-based data pipeline that simulates household kitchen-inventory transactions and builds progressively more advanced analytics on top: feature engineering → PCA/t-SNE → DBSCAN clustering → a 3-layer hybrid recommender (content + collaborative filtering + expiry-urgency) → a product co-occurrence graph with PageRank centrality. There is no application server, API, or frontend — the deliverables are the `src/` scripts, the artifacts they write to `data/`, and the reports/informes derived from those artifacts.

The course brief expects a specific shape (catalog / feature / interaction / graph / pipeline layers) and milestone cadence (Weeks 3, 5, 7, 10, 12, 14 — called Hito 1–5 in this repo, with Week 14 = final integrated delivery still pending). `PLAN_MAESTRO_ENTREGA_FINAL.md` (untracked, local-only) contains a full audit of gaps against the brief as of 2026-07-04 and a phased plan to close them — read it before doing final-delivery work, since it lists specific known issues (e.g. numeric inconsistencies between README/runbook/reports, empty notebooks, missing cluster-profile analysis).

## Running the pipeline

There is no build system, package entry point, or test suite — this is a sequence of standalone Python scripts, each read/writing specific paths under `data/`. **Every script must be run from the repository root** (paths like `data/recommender/R_restock_bin.npz` are hardcoded relative paths, not resolved via `__file__` or a config). There is no `argparse`/CLI config in any script — hyperparameters and file paths are hardcoded constants at the top of each `main()`-style function.

```bash
python3 -m venv venv
source venv/bin/activate     # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Full sequential pipeline (each step consumes artifacts the previous step wrote — order matters, there is no dependency graph/Makefile):

```
extract_patterns.py → simulation.py → ingestion.py → preprocessing.py       # Hito 1: data/processed/inventory_v1.csv
features.py → reduction.py                                                  # Hito 2: PCA/t-SNE on feature_matrix.npy
clustering.py → clustering_refinement.py                                    # Hito 3: DBSCAN, cluster_labels_refined.npy
build_R.py → recommender_content.py → normalizations.py →
  recommender_cf.py → cold_start.py → recommender_hybrid.py → evaluation.py # Hito 4: recommender + offline eval
graph_construction.py → graph_analytics.py                                  # Hito 5: co-occurrence graph + PageRank
                                                                              # (re-run evaluation.py after to compare PageRank vs hybrid)
```

The exact command sequence with inputs/outputs per step is documented in `runbook.md` (kept current through Hito 4 only) and the README Quick Start (which also covers Hito 5) — check both, and see `PLAN_MAESTRO_ENTREGA_FINAL.md` for the known runbook/README/reports numeric-consistency gaps before quoting metrics.

`ingestion.py` and `extract_patterns.py` need external credentials: a Kaggle `~/.kaggle/kaggle.json` and a `.env` with `USDA_API_KEY` (USDA FoodData Central). `ingestion.py` has a documented fallback to local mock data if the API is unavailable.

No test suite exists. There is no lint/format tooling configured. "Verification" for this repo means re-running the relevant script(s) and checking the printed console summary / regenerated artifact against the expected values noted in `runbook.md` (e.g. Silhouette ≈ 0.6549, λ optimal = 1.0, MAP@5 = 0.0539) — do not assume success without checking these numbers, since they're the actual acceptance criteria in an academic pipeline like this.

## Architecture

Everything flows through **`data/processed/inventory_v1.csv`** as the single source of truth (star-schema-like, joined on `stock_id`), produced by the ingestion/ETL layer and consumed by every downstream layer.

- **Ingestion & simulation** (`extract_patterns.py`, `simulation.py`, `ingestion.py`, `preprocessing.py`): synthetic 90-day transactional IN/OUT log for 10 households × 50 products, parameterized from real Instacart purchase-pattern distributions, enriched with real USDA nutrition data via API (with mock fallback). `preprocessing.py` performs the ETL join/cleanup into `inventory_v1.csv`.
- **Feature engineering & dimensionality reduction** (`features.py`, `reduction.py`): builds a dense 72,000×61 ML matrix (Polars, CatBoost Encoding for high-cardinality categoricals), then PCA to 30 components (90% variance) plus t-SNE for visualization. Outputs in `data/features/`.
- **Clustering** (`clustering.py`, `clustering_refinement.py`): benchmarks K-Means/GMM/DBSCAN/HDBSCAN over the PCA space; `clustering_refinement.py` is the authoritative final model (DBSCAN, eps=2.7, min_samples=15) and writes `cluster_labels_refined.npy`, the single source of truth consumed by any downstream cluster-aware code.
- **Recommender engine** (`build_R.py`, `recommender_content.py`, `normalizations.py`, `recommender_cf.py`, `cold_start.py`, `recommender_hybrid.py`, `evaluation.py`) — the largest and most layered part of the codebase:
  - `build_R.py` collapses raw transactions into session-level interaction matrices (10 variants: restock/kitchen/household session windows × binary/count/qty/freq encodings), all in `data/recommender/`.
  - Content layer: TF-IDF over product-attribute pseudo-documents → item-item cosine similarity.
  - CF layer: implicit ALS (Hu/Koren/Volinsky formulation) over a TF-IDF-normalized restock matrix, with a logarithmic λ sweep for regularization selection.
  - `recommender_hybrid.py` linearly blends content + CF + an expiry-urgency term (`w_C=0.35, w_F=0.45, w_E=0.20`) — this is the production-facing scorer.
  - `evaluation.py` runs one shared offline protocol (Masked Basket Completion / Cloze-task style, 20% held-out non-zero interactions, seed 42, fixed candidate pool) across all systems (popularity, content, CF, hybrid, and pagerank once Hito 5 lands) so metrics are directly comparable — always evaluate new recommender variants through this script rather than a bespoke metric, to keep numbers commensurable with the existing report tables.
  - `data/recommender/README.md` documents every artifact's shape/encoding/generating script — treat it as the canonical reference and keep it updated when adding new artifacts there (it's the best-maintained doc in the repo and the intended model for documenting other `data/` subfolders).
- **Graph analytics** (`graph_construction.py`, `graph_analytics.py`): derives a product-product co-occurrence graph via `R^T @ R` on the restock binary matrix, exports `kitchen_graph.gexf`, then computes structural metrics and PageRank centrality (`graph_metrics.json`) to identify "bridge products" across consumption clusters. The planned-but-not-yet-implemented next step is folding PageRank in as a fourth term in `recommender_hybrid.py`'s ensemble — check `reports/graph_analytics_report.md` §5 and `PLAN_MAESTRO_ENTREGA_FINAL.md` Fase 3 before doing this, since the weighting/ablation approach is already designed there.

`legacy/` holds Week 5 scripts/status snapshots that are no longer part of the active pipeline (kept for traceability only — do not treat `legacy/QUICK_STATUS.txt` or `artifacts/validation_report.json` as reflecting current project state, both predate Hito 2).

`reports/*.md` are topical technical write-ups (data dictionary, clustering, recommender experiments, graph analytics, ethics); `Informes/*.tex/.pdf/.pptx` are the formal per-milestone defense documents. Both exist in parallel and sometimes restate the same results — when updating metrics, update both, or at minimum check for drift.
