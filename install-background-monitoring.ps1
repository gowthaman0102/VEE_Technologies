$root = "D:\VEE_Technologies"
$backend = Join-Path $root "backend"
$activate = Join-Path $root ".venv\Scripts\Activate.ps1"

Write-Host "Installing Background Monitoring Tasks..." -ForegroundColor Cyan

$workerAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -Command `"& '$activate'; cd '$backend'; celery -A app.core.celery_app:celery_app worker --loglevel=info --pool=solo -Q media-intelligence`""
$beatAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -Command `"& '$activate'; cd '$backend'; celery -A app.core.celery_app:celery_app beat --loglevel=info`""

# Run at startup or logon
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName "NovaCops_CeleryWorker" -Action $workerAction -Trigger $trigger -Principal $principal -Description "Nova Cops Celery Worker" -Force
Register-ScheduledTask -TaskName "NovaCops_CeleryBeat" -Action $beatAction -Trigger $trigger -Principal $principal -Description "Nova Cops Celery Beat" -Force

Write-Host "Background tasks installed successfully." -ForegroundColor Green
Write-Host "You can start them immediately with: Start-ScheduledTask -TaskName 'NovaCops_CeleryWorker'"
