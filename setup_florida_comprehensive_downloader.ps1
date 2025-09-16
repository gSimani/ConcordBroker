# Florida Comprehensive Data Downloader Setup Script
# This script installs dependencies and sets up the download environment

Write-Host "Setting up Florida Comprehensive Data Downloader..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install playwright aiohttp aiofiles asyncio pathlib

# Install Playwright browsers
Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
python -m playwright install chromium

# Create directory structure
Write-Host "Creating directory structure..." -ForegroundColor Yellow
$baseDir = "C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
if (!(Test-Path $baseDir)) {
    New-Item -ItemType Directory -Path $baseDir -Force
    Write-Host "Created base directory: $baseDir" -ForegroundColor Green
}

# Create PowerShell script to run the downloader
$runnerScript = @"
# Florida Revenue Data Downloader Runner
Write-Host "Starting Florida Revenue Comprehensive Downloader..." -ForegroundColor Green

# Change to the project directory
Set-Location "C:\Users\gsima\Documents\MyProject\ConcordBroker"

# Run the Python downloader
python florida_comprehensive_downloader.py

Write-Host "Download process completed. Check logs for details." -ForegroundColor Green
Pause
"@

$runnerScript | Out-File -FilePath "C:\Users\gsima\Documents\MyProject\ConcordBroker\run_florida_downloader.ps1" -Encoding UTF8

Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the downloader:" -ForegroundColor Yellow
Write-Host "1. Open PowerShell as Administrator"
Write-Host "2. Navigate to: C:\Users\gsima\Documents\MyProject\ConcordBroker"
Write-Host "3. Run: .\run_florida_downloader.ps1"
Write-Host "OR"
Write-Host "3. Run: python florida_comprehensive_downloader.py"
Write-Host ""
Write-Host "Files will be downloaded to:" -ForegroundColor Cyan
Write-Host "$baseDir\[COUNTY]\[DATA_TYPE]\"
Write-Host ""
Write-Host "The downloader will:" -ForegroundColor Yellow
Write-Host "- Download NAL, NAP, and SDF files for all 67 Florida counties"
Write-Host "- Skip already downloaded files"
Write-Host "- Extract ZIP files automatically"
Write-Host "- Create detailed logs"
Write-Host "- Handle errors gracefully"