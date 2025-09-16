# PowerShell script to start ConcordBroker with proper data connection
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ConcordBroker Localhost Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check environment
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.new") {
        Write-Host "Using .env.new file..." -ForegroundColor Yellow
        Copy-Item ".env.new" ".env"
    } else {
        Write-Host "ERROR: No .env file found!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Checking database connection..." -ForegroundColor Yellow
python test_db_ready.py

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""

# Kill any existing processes on ports
$ports = @(8000, 5173)
foreach ($port in $ports) {
    $process = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "Killed process on port $port" -ForegroundColor Yellow
    }
}

# Start API with the localhost version that connects to Supabase
Write-Host "Starting API Server (with real database)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    cd apps/api
    Write-Host 'Starting API with Supabase connection...' -ForegroundColor Green
    python -m uvicorn main_localhost:app --reload --host 0.0.0.0 --port 8000
"@

Start-Sleep -Seconds 3

# Start Web server
Write-Host "Starting Web Server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    cd apps/web
    Write-Host 'Starting React app...' -ForegroundColor Green
    npm run dev
"@

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "  Web App:     http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "  API Stats:   http://localhost:8000/api/stats" -ForegroundColor White
Write-Host ""
Write-Host "Test endpoints:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000/api/properties" -ForegroundColor Gray
Write-Host "  http://localhost:8000/api/stats" -ForegroundColor Gray
Write-Host ""

# Open browser
$openBrowser = Read-Host "Open browser? (y/n)"
if ($openBrowser -eq 'y') {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8000/docs"
    Start-Sleep -Seconds 1
    Start-Process "http://localhost:5173"
}

Write-Host ""
Write-Host "To stop, close the PowerShell windows" -ForegroundColor Yellow
Read-Host "Press Enter to exit"