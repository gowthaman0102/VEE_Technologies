$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "AI Media Intelligence - Readiness Check" -ForegroundColor Cyan
Write-Host "======================================="
Write-Host ""

$allReady = $true


function Show-Result {
    param(
        [string]$Name,
        [bool]$Success,
        [string]$Detail
    )

    if ($Success) {
        Write-Host "[READY] " -NoNewline -ForegroundColor Green
        Write-Host "$Name - $Detail"
    }
    else {
        Write-Host "[FAIL]  " -NoNewline -ForegroundColor Red
        Write-Host "$Name - $Detail"
        $script:allReady = $false
    }
}


# PostgreSQL
$postgres = Test-NetConnection `
    -ComputerName 127.0.0.1 `
    -Port 5432 `
    -WarningAction SilentlyContinue

Show-Result `
    "PostgreSQL" `
    $postgres.TcpTestSucceeded `
    "127.0.0.1:5432"


# Redis
$redis = Test-NetConnection `
    -ComputerName 127.0.0.1 `
    -Port 6379 `
    -WarningAction SilentlyContinue

Show-Result `
    "Redis" `
    $redis.TcpTestSucceeded `
    "127.0.0.1:6379"


# Ollama
$ollamaReady = $false

try {
    $response = Invoke-RestMethod `
        -Uri "http://127.0.0.1:11434/api/tags" `
        -Method Get `
        -TimeoutSec 5

    $ollamaReady = $true
}
catch {
    $ollamaReady = $false
}

Show-Result `
    "Ollama" `
    $ollamaReady `
    "127.0.0.1:11434"


# Qwen model
$modelReady = $false

if ($ollamaReady) {
    $modelReady = @(
        $response.models |
        Where-Object {
            $_.name -like "qwen2.5:7b*"
        }
    ).Count -gt 0
}

Show-Result `
    "Qwen2.5 7B" `
    $modelReady `
    "Local LLM model"


# FastAPI
$apiReady = $false

try {
    $api = Invoke-WebRequest `
        -Uri "http://127.0.0.1:8000/api/v1/dashboard/overview" `
        -UseBasicParsing `
        -TimeoutSec 5

    $apiReady = (
        $api.StatusCode -eq 200
    )
}
catch {
    $apiReady = $false
}

Show-Result `
    "FastAPI" `
    $apiReady `
    "http://127.0.0.1:8000"


# Frontend
$frontendReady = $false

try {
    $frontend = Invoke-WebRequest `
        -Uri "http://127.0.0.1:3000" `
        -UseBasicParsing `
        -TimeoutSec 10

    $frontendReady = (
        $frontend.StatusCode -eq 200
    )
}
catch {
    $frontendReady = $false
}

Show-Result `
    "Dashboard" `
    $frontendReady `
    "http://127.0.0.1:3000"


# Celery
$celeryProcesses = @(
    Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        $_.CommandLine -match "celery" -and
        $_.CommandLine -match "app\.core\.celery_app"
    }
)

$celeryReady = (
    $celeryProcesses.Count -gt 0
)

Show-Result `
    "Celery Worker" `
    $celeryReady `
    "media-intelligence queue"


Write-Host ""
Write-Host "======================================="

if ($allReady) {
    Write-Host "SYSTEM READY FOR DEMO" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "SYSTEM NOT FULLY READY" -ForegroundColor Red
    exit 1
}
