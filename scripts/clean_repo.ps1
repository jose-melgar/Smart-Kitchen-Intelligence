# =============================================================
#  scripts/clean_repo.ps1 - SOLO limpia y ordena (no toca git)
# =============================================================
#  USO desde la RAIZ del repo:
#     PS> .\scripts\clean_repo.ps1
# =============================================================

$ErrorActionPreference = "Stop"

# Asegurar que corremos desde el repo root
if (-not (Test-Path "informe_hito4.tex")) {
    if (Test-Path "..\informe_hito4.tex") { Set-Location .. }
    else { Write-Error "Ejecuta desde la raiz del repo."; exit 1 }
}

Write-Host "========================================================="
Write-Host "  Limpieza y orden del repo SKI - sin tocar git"
Write-Host "========================================================="
Write-Host ""

# -------------------------------------------------------------
# 1. Borrar basura
# -------------------------------------------------------------
Write-Host "[1/4] Borrando basura..." -ForegroundColor Cyan

$junk = @(
    "informe_hito3.aux", "informe_hito3.log", "informe_hito3.out", "informe_hito3.toc",
    "informe_hito4.aux", "informe_hito4.log", "informe_hito4.out", "informe_hito4.toc",
    "lu4198qw.tmp",
    "pyproject.toml",
    ".~lock.Smart_Kitchen_Intelligence_Week5_Presentation.pdf#"
)
$borrados = 0
foreach ($f in $junk) {
    if (Test-Path $f) {
        Remove-Item $f -Force
        Write-Host "   - $f" -ForegroundColor DarkGray
        $borrados++
    }
}

foreach ($d in @("Resume", "quiz_unpacked")) {
    if (Test-Path $d) {
        $count = (Get-ChildItem $d -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
        if ($count -eq 0) {
            Remove-Item $d -Force -Recurse
            Write-Host "   - $d/ (dir vacio)" -ForegroundColor DarkGray
            $borrados++
        }
    }
}
Write-Host "   $borrados elementos eliminados." -ForegroundColor Green

# -------------------------------------------------------------
# 2. Mover legacy de Week 5 a legacy/
# -------------------------------------------------------------
Write-Host ""
Write-Host "[2/4] Moviendo legacy/ ..." -ForegroundColor Cyan

if (-not (Test-Path "legacy")) {
    New-Item -ItemType Directory -Path "legacy" | Out-Null
}

$legacyMoves = @(
    @{src="prepare_presentation.py"; dst="legacy\prepare_presentation.py"},
    @{src="validate_week5.py";       dst="legacy\validate_week5.py"},
    @{src="QUICK_STATUS.txt";        dst="legacy\QUICK_STATUS.txt"}
)
$movidos = 0
foreach ($m in $legacyMoves) {
    if (Test-Path $m.src) {
        Move-Item -Force $m.src $m.dst
        Write-Host ("   {0} -> {1}" -f $m.src, $m.dst) -ForegroundColor DarkGray
        $movidos++
    }
}

# README de legacy/ (array de lineas, sin heredoc para evitar problemas de encoding)
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
Write-Host "   $movidos archivos movidos + legacy/README.md creado." -ForegroundColor Green

# -------------------------------------------------------------
# 3. Mover material de Week 5 (PPT y docs) a artifacts/week5/
# -------------------------------------------------------------
Write-Host ""
Write-Host "[3/4] Consolidando PPT-WEEK5/ y doc-week5/ en artifacts/week5/ ..." -ForegroundColor Cyan

if (-not (Test-Path "artifacts\week5")) {
    New-Item -ItemType Directory -Path "artifacts\week5" -Force | Out-Null
}

if (Test-Path "PPT-WEEK5") {
    if (-not (Test-Path "artifacts\week5\presentation")) {
        Move-Item -Force "PPT-WEEK5" "artifacts\week5\presentation"
        Write-Host "   PPT-WEEK5/ -> artifacts/week5/presentation/" -ForegroundColor DarkGray
    }
}
if (Test-Path "doc-week5") {
    if (-not (Test-Path "artifacts\week5\docs")) {
        Move-Item -Force "doc-week5" "artifacts\week5\docs"
        Write-Host "   doc-week5/ -> artifacts/week5/docs/" -ForegroundColor DarkGray
    }
}
Write-Host "   material de Week 5 consolidado." -ForegroundColor Green

# -------------------------------------------------------------
# 4. Eliminar duplicados
# -------------------------------------------------------------
Write-Host ""
Write-Host "[4/4] Eliminando duplicados..." -ForegroundColor Cyan

if (Test-Path "push_hito4.ps1") {
    Remove-Item "push_hito4.ps1" -Force
    Write-Host "   - push_hito4.ps1 del root (ya esta en scripts/)" -ForegroundColor DarkGray
}

# -------------------------------------------------------------
# Reporte final
# -------------------------------------------------------------
Write-Host ""
Write-Host "========================================================="
Write-Host "  Estructura final del repo:" -ForegroundColor Green
Write-Host "========================================================="

function Show-Tree($path, $prefix = "", $depth = 0, $maxDepth = 1) {
    if ($depth -gt $maxDepth) { return }
    $items = Get-ChildItem $path -Force | Where-Object {
        $_.Name -ne ".git" -and $_.Name -notmatch "^\.~lock"
    } | Sort-Object @{Expression={!$_.PSIsContainer}}, Name
    $count = $items.Count
    $i = 0
    foreach ($item in $items) {
        $i++
        $isLast = ($i -eq $count)
        $connector = if ($isLast) { "+-- " } else { "|-- " }
        $icon = if ($item.PSIsContainer) { "[DIR] " } else { "" }
        Write-Host "$prefix$connector$icon$($item.Name)"
        if ($item.PSIsContainer -and $depth -lt $maxDepth) {
            $newPrefix = $prefix + $(if ($isLast) { "    " } else { "|   " })
            Show-Tree $item.FullName $newPrefix ($depth + 1) $maxDepth
        }
    }
}

Show-Tree "." "" 0 1

Write-Host ""
Write-Host "Listo. Estructura ordenada." -ForegroundColor Green
Write-Host "Para commitear y subir, corre: .\scripts\push_hito4.ps1" -ForegroundColor Yellow
