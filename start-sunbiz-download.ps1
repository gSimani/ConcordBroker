# Sunbiz SFTP Downloader PowerShell Launcher
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   SUNBIZ SFTP DOWNLOADER LAUNCHER   " -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Navigate to the project directory
Set-Location -Path "C:\Users\gsima\Documents\MyProject\ConcordBroker"

# Check if virtual environment exists
$venvPath = ".\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "Checking dependencies..." -ForegroundColor Green
pip install -q -r requirements-sunbiz.txt

# Install Playwright browsers if needed
Write-Host "Ensuring Playwright browsers are installed..." -ForegroundColor Green
playwright install chromium --quiet

# Create database directory if it doesn't exist
$dbPath = "C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE"
if (-not (Test-Path $dbPath)) {
    Write-Host "Creating database directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $dbPath -Force | Out-Null
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Choose an option:" -ForegroundColor Cyan
Write-Host "1. Run Basic Downloader (Simpler, fewer features)" -ForegroundColor White
Write-Host "2. Run Advanced MCP Agent (Full features, resume capability)" -ForegroundColor White
Write-Host "3. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Starting Basic Downloader..." -ForegroundColor Yellow
        python sunbiz_sftp_downloader.py
    }
    "2" {
        Write-Host ""
        Write-Host "Starting Advanced MCP Agent..." -ForegroundColor Yellow
        python sunbiz_mcp_agent.py
    }
    "3" {
        Write-Host "Exiting..." -ForegroundColor Gray
        exit 0
    }
    default {
        Write-Host "Invalid choice. Exiting..." -ForegroundColor Red
        exit 1
    }
}

# Keep window open after execution
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")