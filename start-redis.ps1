# Start Redis portable
$redisPath = "D:\VEE_Technologies\redis\redis-server.exe"

if (Test-Path $redisPath) {
    Write-Host "Starting Redis server..." -ForegroundColor Green
    Start-Process -FilePath $redisPath -WindowStyle Minimized
    Start-Sleep -Seconds 2
    
    # Test connection
    $test = & "D:\VEE_Technologies\redis\redis-cli.exe" ping 2>$null
    if ($test -eq "PONG") {
        Write-Host "[READY] Redis is running on 127.0.0.1:6379" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Redis started (may take a moment)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] Redis not found at $redisPath" -ForegroundColor Red
    Write-Host "Please extract redis.zip to D:\VEE_Technologies\redis\" -ForegroundColor Yellow
}
