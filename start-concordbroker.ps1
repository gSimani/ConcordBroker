# ConcordBroker Startup Script - Ensures correct Supabase connection
# This script unsets any system environment variables that might override .env

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Starting ConcordBroker Services" -ForegroundColor Cyan
Write-Host "   Project: pmispwtdngkcmsrsjwbp" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Unset system environment variables that might conflict
Write-Host "Clearing conflicting environment variables..." -ForegroundColor Yellow
$env:SUPABASE_URL = $null
$env:SUPABASE_SERVICE_ROLE_KEY = $null
$env:SUPABASE_ANON_KEY = $null
$env:SUPABASE_KEY = $null

Write-Host "✓ Environment cleaned" -ForegroundColor Green
Write-Host ""

# Check if ports are available
Write-Host "Checking required ports..." -ForegroundColor Yellow
$apiPort = 8000
$webPort = 5173

$apiInUse = Get-NetTCPConnection -LocalPort $apiPort -ErrorAction SilentlyContinue
$webInUse = Get-NetTCPConnection -LocalPort $webPort -ErrorAction SilentlyContinue

if ($apiInUse) {
    Write-Host "⚠ Port $apiPort is in use. Stopping existing process..." -ForegroundColor Yellow
    $process = Get-Process -Id $apiInUse.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process.Id -Force
        Start-Sleep -Seconds 2
    }
}

if ($webInUse) {
    Write-Host "⚠ Port $webPort is in use. Stopping existing process..." -ForegroundColor Yellow
    $process = Get-Process -Id $webInUse.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process.Id -Force
        Start-Sleep -Seconds 2
    }
}

Write-Host "✓ Ports are available" -ForegroundColor Green
Write-Host ""

# Start API server in new window
Write-Host "Starting API Server (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    cd 'C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\api'
    Write-Host 'ConcordBroker API Server' -ForegroundColor Cyan
    Write-Host 'Using Supabase Project: pmispwtdngkcmsrsjwbp' -ForegroundColor Green
    Write-Host ''
    # Clear any system env vars
    `$env:SUPABASE_URL = `$null
    `$env:SUPABASE_SERVICE_ROLE_KEY = `$null
    python -m uvicorn main_simple:app --reload --host 0.0.0.0 --port 8000
"@

# Wait a moment for API to start
Start-Sleep -Seconds 3

# Start web server in new window
Write-Host "Starting Web Server (Port 5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
    cd 'C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web'
    Write-Host 'ConcordBroker Web Application' -ForegroundColor Cyan
    Write-Host 'Using Supabase Project: pmispwtdngkcmsrsjwbp' -ForegroundColor Green
    Write-Host ''
    npm run dev
"@

# Wait for services to start
Start-Sleep -Seconds 5

# Display status
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   ConcordBroker Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Available URLs:" -ForegroundColor Cyan
Write-Host "  Web App:    " -NoNewline; Write-Host "http://localhost:5173" -ForegroundColor Yellow
Write-Host "  API:        " -NoNewline; Write-Host "http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs:   " -NoNewline; Write-Host "http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  Supabase:   " -NoNewline; Write-Host "https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp" -ForegroundColor Yellow
Write-Host "  Production: " -NoNewline; Write-Host "https://www.concordbroker.com" -ForegroundColor Yellow
Write-Host ""
Write-Host "Database Info:" -ForegroundColor Cyan
Write-Host "  Project:    pmispwtdngkcmsrsjwbp"
Write-Host "  Table:      florida_parcels"
Write-Host ""
Write-Host "Press any key to open the web app in your browser..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open browser
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "To stop all services, close the PowerShell windows" -ForegroundColor Yellow
Read-Host "Press Enter to exit this window"