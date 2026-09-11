$ErrorActionPreference = "SilentlyContinue"

Write-Host "Stopping AI Media Intelligence..." -ForegroundColor Yellow

$processes = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and (
            (
                $_.CommandLine -match "uvicorn" -and
                $_.CommandLine -match "app\.main:app"
            ) -or
            (
                $_.CommandLine -match "celery" -and
                $_.CommandLine -match "app\.core\.celery_app"
            ) -or
            (
                $_.CommandLine -match "next" -and
                $_.CommandLine -match "VEE_Technologies"
            )
        )
    }

if (-not $processes) {
    Write-Host "No project application processes found."
}
else {
    foreach ($process in $processes) {
        Write-Host (
            "Stopping PID {0}" -f
            $process.ProcessId
        )

        taskkill.exe `
            /PID $process.ProcessId `
            /T `
            /F | Out-Null
    }
}

Start-Sleep -Seconds 2

$remaining = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and (
            (
                $_.CommandLine -match "uvicorn" -and
                $_.CommandLine -match "app\.main:app"
            ) -or
            (
                $_.CommandLine -match "celery" -and
                $_.CommandLine -match "app\.core\.celery_app"
            ) -or
            (
                $_.CommandLine -match "next" -and
                $_.CommandLine -match "VEE_Technologies"
            )
        )
    }

Write-Host ""

if ($remaining) {
    Write-Host "Some application processes are still running:" -ForegroundColor Red

    $remaining |
        Select-Object ProcessId, Name, CommandLine |
        Format-Table -AutoSize
}
else {
    Write-Host "AI Media Intelligence stopped." -ForegroundColor Green
}
