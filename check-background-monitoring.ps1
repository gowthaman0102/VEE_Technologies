Write-Host "Checking Background Monitoring Status..." -ForegroundColor Cyan

$tasks = @("NovaCops_CeleryWorker", "NovaCops_CeleryBeat")

foreach ($taskName in $tasks) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "$taskName is Installed. Status: $($task.State)"
    } else {
        Write-Host "$taskName is NOT Installed." -ForegroundColor Yellow
    }
}
