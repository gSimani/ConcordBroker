# Florida Revenue Data Download Runner Script
# PowerShell script to execute all Florida Revenue downloaders
# Last Updated: September 12, 2024

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       FLORIDA REVENUE DATA DOWNLOAD SYSTEM" -ForegroundColor Cyan  
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Set the base directory
$BaseDir = "C:\Users\gsima\Documents\MyProject\ConcordBroker"
Set-Location $BaseDir

# Function to run a Python script and check result
function Run-PythonScript {
    param(
        [string]$ScriptName,
        [string]$Description
    )
    
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host " $Description" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host "Running: $ScriptName"
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host ""
    
    if (Test-Path $ScriptName) {
        python $ScriptName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SUCCESS] $Description completed" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "[FAILED] $Description failed with exit code $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    }
    else {
        Write-Host "[ERROR] Script not found: $ScriptName" -ForegroundColor Red
        return $false
    }
}

# Track overall success
$AllSuccess = $true
$StartTime = Get-Date

# Step 1: Verify Prerequisites
Write-Host ""
Write-Host "STEP 1: VERIFYING PREREQUISITES" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check Python version
$PythonVersion = python --version 2>&1
Write-Host "Python Version: $PythonVersion"

# Check required packages
Write-Host "Checking required packages..."
$RequiredPackages = @("playwright", "aiohttp", "aiofiles")

foreach ($Package in $RequiredPackages) {
    $PackageCheck = python -c "import $Package; print('$Package: OK')" 2>&1
    if ($PackageCheck -like "*OK*") {
        Write-Host "  [OK] $Package installed" -ForegroundColor Green
    }
    else {
        Write-Host "  [MISSING] $Package not installed" -ForegroundColor Red
        Write-Host "  Run: pip install $Package" -ForegroundColor Yellow
        $AllSuccess = $false
    }
}

# Check Playwright browser
Write-Host "Checking Playwright browser..."
$PlaywrightCheck = python -c "from playwright.sync_api import sync_playwright; print('OK')" 2>&1
if ($PlaywrightCheck -eq "OK") {
    Write-Host "  [OK] Playwright browser ready" -ForegroundColor Green
}
else {
    Write-Host "  [MISSING] Playwright browser not installed" -ForegroundColor Red
    Write-Host "  Run: python -m playwright install chromium" -ForegroundColor Yellow
    $AllSuccess = $false
}

if (-not $AllSuccess) {
    Write-Host ""
    Write-Host "Prerequisites not met. Please install missing components." -ForegroundColor Red
    Write-Host "Installation commands:" -ForegroundColor Yellow
    Write-Host "  pip install playwright aiohttp aiofiles"
    Write-Host "  python -m playwright install chromium"
    exit 1
}

# Step 2: Run comprehensive downloader for NAL, NAP, SDF
Write-Host ""
Write-Host "STEP 2: DOWNLOADING NAL, NAP, SDF FILES (2025P)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$Result = Run-PythonScript `
    -ScriptName "florida_comprehensive_downloader.py" `
    -Description "NAL, NAP, SDF Download (2025P)"

if (-not $Result) {
    Write-Host "Warning: Some NAL/NAP/SDF files may have failed" -ForegroundColor Yellow
}

# Step 3: Run NAV downloader
Write-Host ""
Write-Host "STEP 3: DOWNLOADING NAV FILES (2024)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

$Result = Run-PythonScript `
    -ScriptName "florida_nav_fixed_downloader.py" `
    -Description "NAV N and NAV D Download (2024)"

if (-not $Result) {
    Write-Host "Warning: Some NAV files may have failed" -ForegroundColor Yellow
}

# Step 4: Verify downloads
Write-Host ""
Write-Host "STEP 4: VERIFYING DOWNLOADS" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

$Result = Run-PythonScript `
    -ScriptName "check_nav_downloads.py" `
    -Description "Download Verification"

# Step 5: Generate summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                    DOWNLOAD SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$EndTime = Get-Date
$Duration = $EndTime - $StartTime

Write-Host ""
Write-Host "Start Time: $($StartTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "End Time: $($EndTime.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "Duration: $($Duration.Hours) hours, $($Duration.Minutes) minutes, $($Duration.Seconds) seconds"

# Count files
$DataPath = "C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"

if (Test-Path $DataPath) {
    Write-Host ""
    Write-Host "File Counts by Type:" -ForegroundColor Green
    
    $NALCount = (Get-ChildItem -Path $DataPath -Recurse -Directory -Filter "NAL" | Get-ChildItem -File).Count
    $NAPCount = (Get-ChildItem -Path $DataPath -Recurse -Directory -Filter "NAP" | Get-ChildItem -File).Count
    $SDFCount = (Get-ChildItem -Path $DataPath -Recurse -Directory -Filter "SDF" | Get-ChildItem -File).Count
    $NAVNCount = (Get-ChildItem -Path $DataPath -Recurse -Directory -Filter "NAV_N" | Get-ChildItem -File).Count
    $NAVDCount = (Get-ChildItem -Path $DataPath -Recurse -Directory -Filter "NAV_D" | Get-ChildItem -File).Count
    
    Write-Host "  NAL files: $NALCount"
    Write-Host "  NAP files: $NAPCount"
    Write-Host "  SDF files: $SDFCount"
    Write-Host "  NAV_N files: $NAVNCount"
    Write-Host "  NAV_D files: $NAVDCount"
    
    $TotalFiles = $NALCount + $NAPCount + $SDFCount + $NAVNCount + $NAVDCount
    Write-Host ""
    Write-Host "Total Files Downloaded: $TotalFiles" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                DOWNLOAD PROCESS COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Data Location: $DataPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "To re-run failed downloads, simply execute this script again."
Write-Host "Already downloaded files will be skipped automatically."
Write-Host ""

# Pause at the end
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")