$root = "D:\VEE_Technologies"
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$activate = Join-Path $root ".venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Starting AI Media Intelligence..." -ForegroundColor Cyan
Write-Host "================================="
Write-Host ""


function Test-Port {
    param(
        [int]$Port
    )

    return [bool](
        Get-NetTCPConnection `
            -LocalPort $Port `
            -State Listen `
            -ErrorAction SilentlyContinue
    )
}

function Get-ProjectProcessMatches {
    param(
        [string]$Pattern
    )

    return @(
        Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match $Pattern
        }
    )
}

function Stop-ProjectProcesses {
    param(
        [string]$Pattern,
        [string]$Label
    )

    $matches = Get-ProjectProcessMatches -Pattern $Pattern

    if ($matches.Count -eq 0) {
        return
    }

    Write-Host "Stopping stale $Label processes..." -ForegroundColor Yellow

    foreach ($process in $matches) {
        Write-Host ("Stopping PID {0}" -f $process.ProcessId)
        taskkill.exe /PID $process.ProcessId /T /F | Out-Null
    }
}

# Ollama
if (-not (Test-Port 11434)) {
    Write-Host "Starting Ollama..." -ForegroundColor Yellow

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "ollama serve"
    )

    Start-Sleep -Seconds 4
}
else {
    Write-Host "Ollama already running." -ForegroundColor Green
}

# FastAPI
$fastapiProcessPattern = "uvicorn.*app\.main:app"
$fastapiMatches = Get-ProjectProcessMatches -Pattern $fastapiProcessPattern

if (-not (Test-Port 8000)) {
    if ($fastapiMatches.Count -gt 0) {
        Stop-ProjectProcesses -Pattern $fastapiProcessPattern -Label "FastAPI"
    }

    Write-Host "Starting FastAPI..." -ForegroundColor Yellow

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "& '$activate'; cd '$backend'; uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
    )

    Start-Sleep -Seconds 2
}
else {
    Write-Host "FastAPI already running." -ForegroundColor Green
}

# Celery Worker
$celeryWorkerPattern = "celery.*app\.core\.celery_app.*\bworker\b.*media-intelligence|celery.*app\.core\.celery_app.*media-intelligence.*\bworker\b"
$celeryWorker = Get-ProjectProcessMatches -Pattern $celeryWorkerPattern

if ($celeryWorker.Count -eq 0) {
    Write-Host "Starting Celery worker..." -ForegroundColor Yellow

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "& '$activate'; cd '$backend'; celery -A app.core.celery_app:celery_app worker --loglevel=info --pool=solo -Q media-intelligence"
    )

    Start-Sleep -Seconds 2
}
else {
    Write-Host "Celery worker already running." -ForegroundColor Green
}

# Celery Beat
$celeryBeatPattern = "celery.*app\.core\.celery_app.*\bbeat\b"
$celeryBeat = Get-ProjectProcessMatches -Pattern $celeryBeatPattern

if ($celeryBeat.Count -eq 0) {
    Write-Host "Starting Celery Beat..." -ForegroundColor Yellow

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "& '$activate'; cd '$backend'; celery -A app.core.celery_app:celery_app beat --loglevel=info"
    )

    Start-Sleep -Seconds 2
}
else {
    Write-Host "Celery Beat already running." -ForegroundColor Green
}

# Frontend
$frontendProcessPattern = "next.*(VEE_Technologies|\bfrontend\b)|npm.*run.*dev"
$frontendMatches = Get-ProjectProcessMatches -Pattern $frontendProcessPattern

if (-not (Test-Port 3000)) {
    if ($frontendMatches.Count -gt 0) {
        Stop-ProjectProcesses -Pattern $frontendProcessPattern -Label "dashboard"
    }

    Write-Host "Starting dashboard..." -ForegroundColor Yellow

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command",
        "cd '$frontend'; npm run dev"
    )

    Start-Sleep -Seconds 4
}
else {
    Write-Host "Dashboard already running." -ForegroundColor Green
}

Write-Host ""
Write-Host "Running readiness check..." -ForegroundColor Cyan
Write-Host ""

& "$root\check-media-intelligence.ps1"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Opening dashboard..." -ForegroundColor Green

    Start-Process "http://localhost:3000"
}
else {
    Write-Host ""
    Write-Host "Dashboard was not opened because the system is not fully ready." -ForegroundColor Red
}
