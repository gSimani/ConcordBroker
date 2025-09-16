# FLORIDA COMPREHENSIVE MONITORING SYSTEM
# Monitors and downloads ALL Florida property data automatically

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "status", "test", "download")]
    [string]$Action = "start"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  FLORIDA COMPREHENSIVE DATA SYSTEM" -ForegroundColor Cyan
Write-Host "  100% Data Coverage - All 67 Counties" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = "C:\Users\gsima\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

# Verify Python works
& $python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Environment check
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set" -ForegroundColor Yellow
    exit 1
}

switch ($Action) {
    "start" {
        Write-Host "Starting Comprehensive Monitoring System..." -ForegroundColor Green
        Write-Host ""
        Write-Host "This system will:" -ForegroundColor Yellow
        Write-Host "  ✓ Monitor Florida Revenue Portal (NAL, NAP, NAV, SDF, TPP)" -ForegroundColor White
        Write-Host "  ✓ Download data for ALL 67 Florida counties" -ForegroundColor White
        Write-Host "  ✓ Connect to Sunbiz SFTP for business entities" -ForegroundColor White
        Write-Host "  ✓ Download Broward County daily index" -ForegroundColor White
        Write-Host "  ✓ Sync ArcGIS statewide cadastral data" -ForegroundColor White
        Write-Host "  ✓ Automatically detect new folders/updates" -ForegroundColor White
        Write-Host "  ✓ Load all data to Supabase database" -ForegroundColor White
        Write-Host ""
        Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
        Write-Host ""
        
        & $python florida_comprehensive_agent_system.py
    }
    
    "stop" {
        Write-Host "Stopping monitoring processes..." -ForegroundColor Yellow
        Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*florida_comprehensive*"} | Stop-Process -Force
        Write-Host "Monitoring stopped" -ForegroundColor Green
    }
    
    "status" {
        Write-Host "Checking system status..." -ForegroundColor Yellow
        
        # Check if process is running
        $process = Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Select-Object -First 1
        if ($process) {
            Write-Host "✓ Monitoring is ACTIVE" -ForegroundColor Green
        } else {
            Write-Host "✗ Monitoring is STOPPED" -ForegroundColor Red
        }
        
        # Check data directories
        $dataDir = "florida_data_comprehensive"
        if (Test-Path $dataDir) {
            $files = Get-ChildItem -Path $dataDir -Recurse -File | Measure-Object
            Write-Host "✓ Data directory exists with $($files.Count) files" -ForegroundColor Green
            
            # Check each data type
            @("NAL", "NAP", "NAV", "SDF", "TPP", "sunbiz", "broward") | ForEach-Object {
                $typeDir = Join-Path $dataDir $_
                if (Test-Path $typeDir) {
                    $typeFiles = Get-ChildItem -Path $typeDir -Recurse -File | Measure-Object
                    Write-Host "  - $($_): $($typeFiles.Count) files" -ForegroundColor Cyan
                }
            }
        }
        
        # Check processed files
        $processedFile = Join-Path $dataDir "processed_files.json"
        if (Test-Path $processedFile) {
            $processed = Get-Content $processedFile | ConvertFrom-Json
            Write-Host "✓ Processed files: $($processed.Count)" -ForegroundColor Green
        }
    }
    
    "test" {
        Write-Host "Running system test..." -ForegroundColor Yellow
        
        # Test Python script
        $testScript = @"
import sys
sys.path.append('.')
from florida_comprehensive_agent_system import FloridaComprehensiveAgent
import asyncio

async def test():
    agent = FloridaComprehensiveAgent()
    status = agent.get_status()
    print(f"System configured with {status['data_sources']} data sources")
    print(f"Covering {status['counties_covered']} Florida counties")
    print("Test successful!")
    return True

asyncio.run(test())
"@
        
        $testScript | & $python
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ System test PASSED" -ForegroundColor Green
        } else {
            Write-Host "✗ System test FAILED" -ForegroundColor Red
        }
    }
    
    "download" {
        Write-Host "Starting one-time download of ALL data..." -ForegroundColor Yellow
        Write-Host "This will download data for ALL 67 Florida counties" -ForegroundColor Yellow
        Write-Host "Estimated time: 2-4 hours" -ForegroundColor Yellow
        Write-Host ""
        
        $confirmation = Read-Host "Continue? (Y/N)"
        if ($confirmation -eq 'Y') {
            # Run download script
            $downloadScript = @"
import sys
sys.path.append('.')
from florida_comprehensive_agent_system import FloridaComprehensiveAgent
import asyncio

async def download_all():
    agent = FloridaComprehensiveAgent()
    
    # Run all monitors once
    await agent.monitor_florida_revenue()
    await agent.monitor_sunbiz_sftp()
    await agent.monitor_broward_daily()
    await agent.monitor_arcgis_cadastral()
    
    print("Download complete!")
    status = agent.get_status()
    print(f"Processed {status['processed_files']} files")

asyncio.run(download_all())
"@
            
            $downloadScript | & $python
        } else {
            Write-Host "Download cancelled" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Operation complete" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan