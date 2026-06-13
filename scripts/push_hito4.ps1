# =============================================================
#  scripts/push_hito4.ps1 - Limpieza + commits + push del Hito 4
# =============================================================
#  Hace todo en una corrida:
#   1. Desbloquea git
#   2. Borra basura (LaTeX aux, temp, lock, vacios)
#   3. Mueve legacy de Week 5 a legacy/
#   4. Renormaliza CRLF->LF
#   5. Descarta ruido CRLF en archivos no-Hito4
#   6. Crea branch Gabriel-hito4
#   7. Commits modulares
#   8. Push y link de PR
#
#  USO desde la RAIZ del repo (no desde scripts/):
#     PS> .\scripts\push_hito4.ps1
#
#  Si PowerShell bloquea ejecucion:
#     PS> Set-ExecutionPolicy -Scope Process Bypass
# =============================================================

$ErrorActionPreference = "Continue"
# Suprimir el patron donde PS trata stderr de git como error fatal
$PSNativeCommandUseErrorActionPreference = $false

# Asegurar que corremos desde el repo root (no desde scripts/)
if (-not (Test-Path "informe_hito4.tex")) {
    if (Test-Path "..\informe_hito4.tex") {
        Set-Location ..
    } else {
        Write-Error "Ejecuta este script desde la raiz del repo."
        exit 1
    }
}

# -------------------------------------------------------------
# Paso 0: Desbloquear git
# -------------------------------------------------------------
Write-Host "=== 0. Desbloquear git si quedo index.lock ==="
if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
    Write-Host "  -> .git/index.lock eliminado."
}

# -------------------------------------------------------------
# Paso 1: Borrar basura del root
# -------------------------------------------------------------
Write-Host "=== 1. Borrar basura (LaTeX aux, temp, lock, dirs vacios) ==="
$junk = @(
    "informe_hito3.aux", "informe_hito3.log", "informe_hito3.out", "informe_hito3.toc",
    "informe_hito4.aux", "informe_hito4.log", "informe_hito4.out", "informe_hito4.toc",
    "lu4198qw.tmp",
    "pyproject.toml",
    ".~lock.Smart_Kitchen_Intelligence_Week5_Presentation.pdf#"
)
foreach ($f in $junk) {
    if (Test-Path $f) {
        Remove-Item $f -Force
        Write-Host "  borrado: $f"
    }
}

# Dirs vacios
foreach ($d in @("Resume", "quiz_unpacked")) {
    if (Test-Path $d) {
        $count = (Get-ChildItem $d -Recurse -Force | Measure-Object).Count
        if ($count -eq 0) {
            Remove-Item $d -Force
            Write-Host "  borrado dir vacio: $d"
        } else {
            Write-Host "  SKIP $d (no esta vacio)"
        }
    }
}

# -------------------------------------------------------------
# Paso 2: Mover legacy de Week 5 a legacy/
# -------------------------------------------------------------
Write-Host "=== 2. Mover legacy de Week 5 a legacy/ ==="
if (-not (Test-Path "legacy")) { New-Item -ItemType Directory -Path "legacy" | Out-Null }

$legacyMoves = @(
    @{src="prepare_presentation.py"; dst="legacy\prepare_presentation.py"},
    @{src="validate_week5.py";       dst="legacy\validate_week5.py"},
    @{src="QUICK_STATUS.txt";        dst="legacy\QUICK_STATUS.txt"}
)
foreach ($m in $legacyMoves) {
    if (Test-Path $m.src) {
        # git mv preserva historial
        git mv -f $m.src $m.dst 2>$null
        if ($LASTEXITCODE -ne 0) {
            # si git mv falla (archivo no trackeado), hacer move plain
            Move-Item -Force $m.src $m.dst
        }
        Write-Host "  movido: $($m.src) -> $($m.dst)"
    }
}

# README explicativo en legacy/ (array de lineas en ASCII)
$legacyReadmeLines = @(
    "# legacy/",
    "",
    "Artefactos de etapas anteriores del proyecto (Week 5) que ya no forman parte",
    "del pipeline activo pero se mantienen para trazabilidad:",
    "",
    "- prepare_presentation.py: script que preparaba la presentacion de Week 5.",
    "- validate_week5.py: validador del estado de la entrega Week 5.",
    "- QUICK_STATUS.txt: resumen rapido del avance al cierre de Week 5.",
    "",
    "El estado actual del proyecto se documenta en el README.md raiz y en los",
    "informes informe_hito3.pdf (Semana 7) e informe_hito4.pdf (Semana 11)."
)
Set-Content -Path "legacy\README.md" -Value $legacyReadmeLines -Encoding UTF8

# Consolidar material de Week 5 (PPT + docs) en artifacts/week5/
Write-Host "  consolidando PPT-WEEK5/ y doc-week5/ en artifacts/week5/..."
if (-not (Test-Path "artifacts\week5")) {
    New-Item -ItemType Directory -Path "artifacts\week5" -Force | Out-Null
}
if ((Test-Path "PPT-WEEK5") -and (-not (Test-Path "artifacts\week5\presentation"))) {
    git mv -f "PPT-WEEK5" "artifacts\week5\presentation" 2>$null
    if ($LASTEXITCODE -ne 0) { Move-Item -Force "PPT-WEEK5" "artifacts\week5\presentation" }
    Write-Host "    PPT-WEEK5/ -> artifacts/week5/presentation/"
}
if ((Test-Path "doc-week5") -and (-not (Test-Path "artifacts\week5\docs"))) {
    git mv -f "doc-week5" "artifacts\week5\docs" 2>$null
    if ($LASTEXITCODE -ne 0) { Move-Item -Force "doc-week5" "artifacts\week5\docs" }
    Write-Host "    doc-week5/ -> artifacts/week5/docs/"
}

# Borrar el push_hito4.ps1 viejo del root si quedo ahi
if (Test-Path "push_hito4.ps1") {
    Remove-Item "push_hito4.ps1" -Force
    Write-Host "  borrado script viejo: push_hito4.ps1 (ahora en scripts/)"
}

# -------------------------------------------------------------
# Paso 3: Renormalizar line endings segun .gitattributes
# -------------------------------------------------------------
Write-Host "=== 3. Renormalizar CRLF -> LF ==="
git add --renormalize . | Out-Null

# -------------------------------------------------------------
# Paso 4: Descartar ruido CRLF-only en archivos no relacionados con Hito 4
# -------------------------------------------------------------
Write-Host "=== 4. Descartar cambios CRLF-only fuera del Hito 4 ==="
$revertList = @(
    "artifacts/validation_report.json",
    "data/processed/inventory_v1.csv",
    "data/raw/catalog_raw.csv",
    "data/raw/instacart_patterns.json",
    "data/raw/movements_raw.csv",
    "notebooks/03_presentation_demo.ipynb",
    "reports/clustering_experiments.md",
    "reports/data_dictionary.md",
    "reports/dimensionality_reduction_report.md",
    "reports/ethics_note.md",
    "reports/final_model_selection.md",
    "reports/proposal.md",
    "reports/scale_analysis.md",
    "reports/schema_draft.md",
    "reports/source_inventory.md",
    "src/clustering.py",
    "src/clustering_refinement.py",
    "src/extract_patterns.py",
    "src/features.py",
    "src/ingestion.py",
    "src/preprocessing.py",
    "src/reduction.py",
    "src/simulation.py"
)
foreach ($f in $revertList) {
    if (Test-Path $f) { git checkout -- $f 2>$null }
}

# -------------------------------------------------------------
# Paso 5: Crear branch
# -------------------------------------------------------------
Write-Host "=== 5. Crear branch Gabriel-hito4 ==="
$currentBranch = git branch --show-current
if ($currentBranch -ne "Gabriel-hito4") {
    git checkout -b Gabriel-hito4 2>$null
    if ($LASTEXITCODE -ne 0) {
        # branch ya existe
        git checkout Gabriel-hito4
    }
}

# -------------------------------------------------------------
# Paso 6: Commits modulares
# -------------------------------------------------------------
Write-Host "=== 6. Commits modulares ==="

function Try-Commit($files, $message) {
    foreach ($f in $files) { if (Test-Path $f) { git add $f 2>$null } }
    git diff --cached --quiet 2>$null
    if ($LASTEXITCODE -ne 0) {
        git commit -m $message
        Write-Host "  commit: $message"
    } else {
        Write-Host "  SKIP (nada que commitear): $message"
    }
}

Try-Commit @(".gitattributes", ".gitignore") `
    "chore: gitattributes LF + gitignore reforzado (LaTeX aux, pycache)"

Try-Commit @("src/build_R.py", "src/recommender_content.py", "src/normalizations.py",
             "src/recommender_cf.py", "src/cold_start.py", "src/recommender_hybrid.py",
             "src/evaluation.py", "src/generate_hito4_figures.py") `
    "feat(hito4): pipeline recomendacion - TF-IDF, ALS, cold-start, hibrido, eval consolidada"

Try-Commit @("data/recommender/") `
    "data(hito4): matrices R, factores ALS, similitudes item-item, evaluation_table"

Try-Commit @("reports/figures/hito4/") `
    "docs(hito4): figuras del informe (sparsity, lambda, cold-start, ablacion)"

Try-Commit @("informe_hito4.tex", "informe_hito4.pdf", "notebooks/04_recommender_experiments.ipynb") `
    "docs(hito4): informe tecnico (19 pags) + notebook de experimentos"

Try-Commit @("README.md", "runbook.md") `
    "docs(hito4): README y runbook con pasos del recomendador"

Try-Commit @("legacy/", "scripts/", "QUICK_STATUS.txt", "prepare_presentation.py", "validate_week5.py",
             "informe_hito3.aux", "informe_hito3.log", "informe_hito3.out", "informe_hito3.toc",
             "informe_hito4.aux", "informe_hito4.log", "informe_hito4.out", "informe_hito4.toc",
             "lu4198qw.tmp", "pyproject.toml", "Resume", "quiz_unpacked", "push_hito4.ps1") `
    "chore: limpieza root - legacy/ + scripts/ + borrar aux LaTeX y vacios"

# -------------------------------------------------------------
# Paso 7: Push
# -------------------------------------------------------------
Write-Host "=== 7. Push branch Gabriel-hito4 ==="
git push -u origin Gabriel-hito4

# -------------------------------------------------------------
# Fin
# -------------------------------------------------------------
Write-Host ""
Write-Host "=== HECHO ==="
Write-Host "Branch subida: Gabriel-hito4"
Write-Host "PR: https://github.com/jose-melgar/Smart-Kitchen-Intelligence/compare/main...Gabriel-hito4"
