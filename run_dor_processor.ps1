# DOR Data Processor Setup and Test Script
# Processes Florida Department of Revenue data into Supabase

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DOR Data Processor - Setup & Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Python installation
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Navigate to DOR processor directory
$processorPath = "apps\workers\dor_processor"
if (Test-Path $processorPath) {
    Set-Location $processorPath
    Write-Host "Changed to DOR processor directory" -ForegroundColor Green
} else {
    Write-Host "DOR processor directory not found!" -ForegroundColor Red
    exit 1
}

# Install required packages
Write-Host "`nInstalling required packages..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install packages" -ForegroundColor Red
    exit 1
}
Write-Host "Packages installed successfully" -ForegroundColor Green

# Create data directories
Write-Host "`nCreating data directories..." -ForegroundColor Yellow
$dataDir = "data\dor"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
New-Item -ItemType Directory -Force -Path "$dataDir\raw" | Out-Null
New-Item -ItemType Directory -Force -Path "$dataDir\processed" | Out-Null
New-Item -ItemType Directory -Force -Path "$dataDir\archive" | Out-Null
New-Item -ItemType Directory -Force -Path "$dataDir\metadata" | Out-Null
Write-Host "Data directories created" -ForegroundColor Green

# Check environment variables
Write-Host "`nChecking environment variables..." -ForegroundColor Yellow
$requiredVars = @("SUPABASE_URL", "SUPABASE_ANON_KEY", "DATABASE_URL")
$missingVars = @()

foreach ($var in $requiredVars) {
    if (-not [Environment]::GetEnvironmentVariable($var)) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "Missing environment variables:" -ForegroundColor Red
    $missingVars | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host "`nPlease set these in your .env file" -ForegroundColor Yellow
    
    # Check if .env exists in root
    if (Test-Path "..\..\..\..\.env") {
        Write-Host "Loading from root .env file..." -ForegroundColor Yellow
        Get-Content "..\..\..\..\.env" | ForEach-Object {
            if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
                [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
            }
        }
        Write-Host "Environment variables loaded" -ForegroundColor Green
    }
}

# Menu
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Select an option:" -ForegroundColor Cyan
Write-Host "1. Test Broward County data processing" -ForegroundColor White
Write-Host "2. Start automated file agent" -ForegroundColor White
Write-Host "3. Process all Florida counties" -ForegroundColor White
Write-Host "4. Check processing status" -ForegroundColor White
Write-Host "5. Exit" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    1 {
        Write-Host "`nStarting Broward County test..." -ForegroundColor Yellow
        python test_broward.py
    }
    2 {
        Write-Host "`nStarting automated file agent..." -ForegroundColor Yellow
        python file_manager.py
    }
    3 {
        Write-Host "`nProcessing all counties..." -ForegroundColor Yellow
        python -c "
import asyncio
from duckdb_processor import DORDuckDBProcessor
from file_manager import DORDataAgent

async def process_all():
    agent = DORDataAgent()
    await agent.start()
    
    counties = ['Miami-Dade', 'Palm Beach', 'Hillsborough', 'Orange', 'Pinellas']
    for county in counties:
        print(f'Queuing {county}...')
        await agent.manual_download(county, 2025)
    
    print('All counties queued for processing')
    print('Check logs for progress')

asyncio.run(process_all())
"
    }
    4 {
        Write-Host "`nChecking status..." -ForegroundColor Yellow
        python -c "
import json
from pathlib import Path

metadata_file = Path('data/dor/metadata/file_registry.json')
if metadata_file.exists():
    with open(metadata_file) as f:
        registry = json.load(f)
    
    status_counts = {}
    for file, meta in registry.items():
        status = meta['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print('\nFile Status Summary:')
    for status, count in status_counts.items():
        print(f'  {status}: {count}')
    
    print('\nRecent Files:')
    for file, meta in list(registry.items())[:5]:
        print(f'  {file}: {meta[\"status\"]}')
else:
    print('No file registry found')
"
    }
    5 {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
    }
}

# Return to root directory
Set-Location ..\..\..
Write-Host "`nDone!" -ForegroundColor Green