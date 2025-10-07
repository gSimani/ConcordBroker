# Kill processes on specific ports to avoid confusion
$ports = @(5173, 5174, 5176, 5178, 5181)

Write-Host "Cleaning up website instances on other ports..." -ForegroundColor Yellow

foreach ($port in $ports) {
    $process = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($process) {
        $processId = $process.OwningProcess
        Write-Host "Stopping process on port $port (PID: $processId)" -ForegroundColor Red
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`nPort 5175 is kept running as the main website" -ForegroundColor Green
Write-Host "Access the website at: http://localhost:5175/properties" -ForegroundColor Cyan