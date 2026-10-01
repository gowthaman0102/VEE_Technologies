Write-Host "Uninstalling Background Monitoring Tasks..." -ForegroundColor Cyan

Unregister-ScheduledTask -TaskName "NovaCops_CeleryWorker" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "NovaCops_CeleryBeat" -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "Background tasks uninstalled successfully." -ForegroundColor Green
