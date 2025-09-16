# PowerShell script to start ConcordBroker on localhost
# This script starts all services needed for local development

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ConcordBroker Local Development" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.new") {
        Write-Host "Found .env.new - renaming to .env..." -ForegroundColor Yellow
        Rename-Item ".env.new" ".env"
    } else {
        Write-Host "ERROR: No .env file found!" -ForegroundColor Red
        Write-Host "Please create .env from .env.example and add your credentials" -ForegroundColor Yellow
        exit 1
    }
}

# Function to check if a port is in use
function Test-Port {
    param($Port)
    $connection = New-Object System.Net.Sockets.TcpClient
    try {
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# Check required ports
Write-Host "Checking required ports..." -ForegroundColor Yellow
$portsToCheck = @(
    @{Port=8000; Service="API"},
    @{Port=5173; Service="Web"}
)

foreach ($item in $portsToCheck) {
    if (Test-Port -Port $item.Port) {
        Write-Host "  Port $($item.Port) ($($item.Service)) is already in use" -ForegroundColor Red
        $kill = Read-Host "  Kill process on port $($item.Port)? (y/n)"
        if ($kill -eq 'y') {
            $process = Get-NetTCPConnection -LocalPort $item.Port -State Listen -ErrorAction SilentlyContinue
            if ($process) {
                Stop-Process -Id $process.OwningProcess -Force
                Write-Host "  Process killed" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  Port $($item.Port) ($($item.Service)) is available" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""

# Start API server
Write-Host "1. Starting API Server (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/api; Write-Host 'Starting FastAPI...' -ForegroundColor Green; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 2

# Start Web server
Write-Host "2. Starting Web Server (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/web; Write-Host 'Starting Vite...' -ForegroundColor Green; npm run dev"

Start-Sleep -Seconds 3

# Check if services are running
Write-Host ""
Write-Host "Checking services..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

$apiRunning = Test-Port -Port 8000
$webRunning = Test-Port -Port 5173

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Service Status" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

if ($apiRunning) {
    Write-Host "✅ API Server: http://localhost:8000" -ForegroundColor Green
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Gray
} else {
    Write-Host "❌ API Server: Not running" -ForegroundColor Red
}

if ($webRunning) {
    Write-Host "✅ Web App: http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "❌ Web App: Not running" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Database Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$setupDb = Read-Host "Do you want to set up the database? (y/n)"
if ($setupDb -eq 'y') {
    Write-Host "Running database setup..." -ForegroundColor Yellow
    python setup_database.py
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Development Environment Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Available URLs:" -ForegroundColor Cyan
Write-Host "  Web App:    http://localhost:5173" -ForegroundColor White
Write-Host "  API:        http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Supabase:   Check your Supabase dashboard" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services, close the PowerShell windows" -ForegroundColor Yellow
Write-Host ""

# Open browser
$openBrowser = Read-Host "Open web app in browser? (y/n)"
if ($openBrowser -eq 'y') {
    Start-Process "http://localhost:5173"
}

Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")