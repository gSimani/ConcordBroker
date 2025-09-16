# Advanced Filter Verification Script
# Comprehensive testing of all filter components

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Advanced Property Filters Verification" -ForegroundColor Cyan
Write-Host " Neural Network Enhanced Filter Detection & Testing" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if services are running
Write-Host "Checking required services..." -ForegroundColor Yellow

# Check frontend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 3
    Write-Host "✓ Frontend running on port 5173" -ForegroundColor Green
} catch {
    Write-Host "⚠ Starting React frontend..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd" -ArgumentList "/c cd apps/web && npm run dev" -WindowStyle Minimized
    Write-Host "Waiting for frontend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10

    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5
        Write-Host "✓ Frontend now running" -ForegroundColor Green
    } catch {
        Write-Host "✗ Could not start frontend - please start manually" -ForegroundColor Red
        Write-Host "Run: cd apps/web && npm run dev" -ForegroundColor Yellow
        exit 1
    }
}

# Check API
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "✓ API running on port 8000" -ForegroundColor Green
} catch {
    Write-Host "⚠ Starting FastAPI backend..." -ForegroundColor Yellow
    Start-Process -FilePath "cmd" -ArgumentList "/c cd apps/api && python property_live_api.py" -WindowStyle Minimized
    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "Running Advanced Filter Verification..." -ForegroundColor Cyan
Write-Host "This will:" -ForegroundColor White
Write-Host "  • Navigate to the Properties page" -ForegroundColor White
Write-Host "  • Find and click the Advanced Filters button" -ForegroundColor White
Write-Host "  • Detect all filter elements using neural networks" -ForegroundColor White
Write-Host "  • Test each filter's functionality" -ForegroundColor White
Write-Host "  • Verify data flow and interactions" -ForegroundColor White
Write-Host "  • Generate comprehensive report with screenshots" -ForegroundColor White
Write-Host ""

Set-Location "apps/api"

# Create verification directory
if (!(Test-Path "verification")) {
    New-Item -ItemType Directory -Path "verification" | Out-Null
    Write-Host "✓ Created verification directory" -ForegroundColor Green
}

Write-Host "Starting filter detection and verification..." -ForegroundColor Yellow
python advanced_filter_verifier.py

Set-Location "../.."

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Filter Verification Complete!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check for generated reports
$reportFiles = Get-ChildItem "apps/api/advanced_filters_verification_*.json" -ErrorAction SilentlyContinue

if ($reportFiles) {
    $latestReport = $reportFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    Write-Host "Generated Reports:" -ForegroundColor Yellow
    Write-Host "  📊 Verification Report: $($latestReport.Name)" -ForegroundColor White

    # Parse and display key metrics
    try {
        $reportContent = Get-Content $latestReport.FullName | ConvertFrom-Json
        $summary = $reportContent.verification_summary

        Write-Host ""
        Write-Host "Filter Verification Summary:" -ForegroundColor Yellow
        Write-Host "  • Total Filters Found: $($summary.total_filters_found)" -ForegroundColor White
        Write-Host "  • Working Filters: $($summary.working_filters)" -ForegroundColor Green
        Write-Host "  • Broken Filters: $($summary.broken_filters)" -ForegroundColor $(if ($summary.broken_filters -gt 0) { "Red" } else { "Green" })
        Write-Host "  • Success Rate: $([math]::Round($summary.success_rate * 100, 1))%" -ForegroundColor $(if ($summary.success_rate -gt 0.9) { "Green" } elseif ($summary.success_rate -gt 0.7) { "Yellow" } else { "Red" })

        Write-Host ""
        Write-Host "Filter Groups Detected:" -ForegroundColor Yellow
        foreach ($group in $reportContent.filter_groups) {
            $workingCount = ($group.filters | Where-Object { $_.is_working -eq $true }).Count
            $totalCount = $group.filters.Count
            Write-Host "  • $($group.group_name): $workingCount/$totalCount working" -ForegroundColor White
        }

        if ($reportContent.quick_filters) {
            $workingQuickFilters = ($reportContent.quick_filters | Where-Object { $_.is_working -eq $true }).Count
            $totalQuickFilters = $reportContent.quick_filters.Count
            Write-Host "  • Quick Filters: $workingQuickFilters/$totalQuickFilters working" -ForegroundColor White
        }

        if ($reportContent.missing_filters -and $reportContent.missing_filters.Count -gt 0) {
            Write-Host ""
            Write-Host "Missing Filters:" -ForegroundColor Red
            foreach ($missing in $reportContent.missing_filters) {
                Write-Host "  ✗ $missing" -ForegroundColor Red
            }
        }

        if ($reportContent.recommendations) {
            Write-Host ""
            Write-Host "Recommendations:" -ForegroundColor Yellow
            foreach ($rec in $reportContent.recommendations) {
                Write-Host "  • $rec" -ForegroundColor White
            }
        }

    } catch {
        Write-Host "Could not parse report details" -ForegroundColor Yellow
    }

    # Check for screenshot
    $screenshotFiles = Get-ChildItem "apps/api/verification/advanced_filters_*.png" -ErrorAction SilentlyContinue
    if ($screenshotFiles) {
        $latestScreenshot = $screenshotFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        Write-Host ""
        Write-Host "📸 Screenshot saved: $($latestScreenshot.Name)" -ForegroundColor Cyan
    }

} else {
    Write-Host "⚠ No verification report found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Expected Filters (Based on Component Analysis):" -ForegroundColor Yellow
Write-Host ""

Write-Host "🔢 Value Filters:" -ForegroundColor Cyan
Write-Host "  • Min Value (number input)" -ForegroundColor White
Write-Host "  • Max Value (number input)" -ForegroundColor White

Write-Host ""
Write-Host "📐 Size Filters:" -ForegroundColor Cyan
Write-Host "  • Min Square Feet (number input)" -ForegroundColor White
Write-Host "  • Max Square Feet (number input)" -ForegroundColor White
Write-Host "  • Min Land Square Feet (number input)" -ForegroundColor White
Write-Host "  • Max Land Square Feet (number input)" -ForegroundColor White

Write-Host ""
Write-Host "📅 Year Filters:" -ForegroundColor Cyan
Write-Host "  • Min Year Built (number input)" -ForegroundColor White
Write-Host "  • Max Year Built (number input)" -ForegroundColor White

Write-Host ""
Write-Host "📍 Location Filters:" -ForegroundColor Cyan
Write-Host "  • County (select dropdown)" -ForegroundColor White
Write-Host "  • City (text input)" -ForegroundColor White
Write-Host "  • ZIP Code (text input)" -ForegroundColor White

Write-Host ""
Write-Host "🏠 Property Type Filters:" -ForegroundColor Cyan
Write-Host "  • Property Use Code (select dropdown)" -ForegroundColor White
Write-Host "  • Sub-Usage Code (text input)" -ForegroundColor White

Write-Host ""
Write-Host "💰 Assessment Filters:" -ForegroundColor Cyan
Write-Host "  • Min Assessed Value (number input)" -ForegroundColor White
Write-Host "  • Max Assessed Value (number input)" -ForegroundColor White

Write-Host ""
Write-Host "🏊 Feature Filters:" -ForegroundColor Cyan
Write-Host "  • Tax Exempt (select dropdown: Any/Yes/No)" -ForegroundColor White
Write-Host "  • Has Pool (select dropdown: Any/Yes/No)" -ForegroundColor White
Write-Host "  • Waterfront (select dropdown: Any/Yes/No)" -ForegroundColor White
Write-Host "  • Recently Sold (checkbox)" -ForegroundColor White

Write-Host ""
Write-Host "⚡ Quick Filters:" -ForegroundColor Cyan
Write-Host "  • Under `$300K" -ForegroundColor White
Write-Host "  • `$300K - `$600K" -ForegroundColor White
Write-Host "  • `$600K - `$1M" -ForegroundColor White
Write-Host "  • Over `$1M" -ForegroundColor White
Write-Host "  • Single Family" -ForegroundColor White
Write-Host "  • Condos" -ForegroundColor White
Write-Host "  • New Construction" -ForegroundColor White
Write-Host "  • Recently Sold" -ForegroundColor White

Write-Host ""
Write-Host "🔧 Action Buttons:" -ForegroundColor Cyan
Write-Host "  • Search Properties (submit button)" -ForegroundColor White
Write-Host "  • Reset Filters (reset button)" -ForegroundColor White

Write-Host ""
Write-Host "To manually test filters:" -ForegroundColor Yellow
Write-Host "  1. Go to http://localhost:5173/properties" -ForegroundColor White
Write-Host "  2. Look for the Advanced Filters button (with sliders icon)" -ForegroundColor White
Write-Host "  3. Click to open the filter panel" -ForegroundColor White
Write-Host "  4. Test each filter by entering values and checking results" -ForegroundColor White

Write-Host ""
Write-Host "Press any key to open the properties page in browser..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open properties page
Start-Process "http://localhost:5173/properties"

Write-Host ""
Write-Host "Advanced Filter Verification Complete! ✨" -ForegroundColor Green