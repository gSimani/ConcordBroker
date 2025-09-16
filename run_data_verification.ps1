# PowerShell script to run comprehensive data verification
# Ensures all data flows correctly from database to UI

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " ConcordBroker Data Verification System" -ForegroundColor Cyan
Write-Host " ML-based Field Mapping + Visual Verification" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green

# Install dependencies if needed
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$deps = @(
    "scikit-learn",
    "pandas",
    "opencv-python",
    "pytesseract",
    "playwright",
    "supabase"
)

foreach ($dep in $deps) {
    $installed = pip show $dep 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing $dep..." -ForegroundColor Yellow
        pip install $dep --quiet
    } else {
        Write-Host "✓ $dep installed" -ForegroundColor Green
    }
}

# Install Playwright browsers if needed
Write-Host ""
Write-Host "Checking Playwright browsers..." -ForegroundColor Yellow
python -m playwright install chromium

# Create verification directory
if (!(Test-Path "verification")) {
    New-Item -ItemType Directory -Path "verification" | Out-Null
    Write-Host "✓ Created verification directory" -ForegroundColor Green
}

# Start services if not running
Write-Host ""
Write-Host "Checking services..." -ForegroundColor Yellow

# Check if localhost:5173 is responding
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2
    Write-Host "✓ Frontend is running" -ForegroundColor Green
} catch {
    Write-Host "Starting frontend..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd" -ArgumentList "/c cd apps/web && npm run dev" -WindowStyle Minimized
    Start-Sleep -Seconds 5
}

# Check if API is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
    Write-Host "✓ API is running" -ForegroundColor Green
} catch {
    Write-Host "Starting API..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd" -ArgumentList "/c cd apps/api && python property_live_api.py" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Running Data Verification Tests" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Run the verification
Set-Location "apps/api"

Write-Host "1. Running ML-based field mapping..." -ForegroundColor Yellow
python intelligent_data_mapper.py

Write-Host ""
Write-Host "2. Running visual verification..." -ForegroundColor Yellow
python visual_data_verifier.py

Write-Host ""
Write-Host "3. Running comprehensive verification..." -ForegroundColor Yellow
python comprehensive_data_verification.py

Set-Location "../.."

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Verification Complete!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Reports generated:" -ForegroundColor Yellow
Write-Host "  • data_mapping_report.md - Field mapping analysis" -ForegroundColor White
Write-Host "  • visual_verification_report.md - Visual verification results" -ForegroundColor White
Write-Host "  • comprehensive_verification_report.md - Complete analysis" -ForegroundColor White
Write-Host "  • verified_mapping_config.json - Verified field mappings" -ForegroundColor White
Write-Host ""
Write-Host "Screenshots saved in: verification/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")