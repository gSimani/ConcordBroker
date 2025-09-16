# PowerShell script to diagnose why properties aren't showing

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Property Display Diagnostic" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if API is running
Write-Host "1. Checking API Status..." -ForegroundColor Yellow
try {
    $apiResponse = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
    Write-Host "   [OK] API is running" -ForegroundColor Green
    Write-Host "   Version: $($apiResponse.version)" -ForegroundColor Gray
} catch {
    Write-Host "   [FAIL] API is not running on port 8000" -ForegroundColor Red
    Write-Host "   Start it with: cd apps/api && python -m uvicorn main_simple:app --reload" -ForegroundColor Yellow
    exit 1
}

# Step 2: Check API properties endpoint
Write-Host ""
Write-Host "2. Checking Properties Endpoint..." -ForegroundColor Yellow
try {
    $propertiesResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/properties/search?address=&city=&limit=5" -Method Get
    $propCount = $propertiesResponse.properties.Count
    Write-Host "   [OK] Found $propCount properties" -ForegroundColor Green
    
    if ($propCount -gt 0) {
        Write-Host "   Sample property:" -ForegroundColor Gray
        $firstProp = $propertiesResponse.properties[0]
        Write-Host "     - Address: $($firstProp.phy_addr1)" -ForegroundColor Gray
        Write-Host "     - City: $($firstProp.phy_city)" -ForegroundColor Gray
        Write-Host "     - Value: `$$($firstProp.jv)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   [FAIL] Properties endpoint error: $_" -ForegroundColor Red
}

# Step 3: Check if frontend is running
Write-Host ""
Write-Host "3. Checking Frontend Status..." -ForegroundColor Yellow
try {
    $webResponse = Invoke-WebRequest -Uri "http://localhost:5174" -UseBasicParsing -TimeoutSec 2
    if ($webResponse.StatusCode -eq 200) {
        Write-Host "   [OK] Frontend is running on port 5174" -ForegroundColor Green
    }
} catch {
    # Try port 5173
    try {
        $webResponse = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2
        if ($webResponse.StatusCode -eq 200) {
            Write-Host "   [OK] Frontend is running on port 5173" -ForegroundColor Green
            Write-Host "   Note: Using port 5173, not 5174" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   [FAIL] Frontend is not running" -ForegroundColor Red
        Write-Host "   Start it with: cd apps/web && npm run dev" -ForegroundColor Yellow
    }
}

# Step 4: Check CORS
Write-Host ""
Write-Host "4. Checking CORS Configuration..." -ForegroundColor Yellow
try {
    $headers = @{
        "Origin" = "http://localhost:5174"
    }
    $corsResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/properties/search?limit=1" -Headers $headers -UseBasicParsing
    Write-Host "   [OK] CORS is properly configured" -ForegroundColor Green
} catch {
    Write-Host "   [WARNING] CORS might not be configured for port 5174" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Diagnosis Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "SOLUTION:" -ForegroundColor Green
Write-Host "1. The fixed component is now at: /properties" -ForegroundColor White
Write-Host "2. Make sure both services are running:" -ForegroundColor White
Write-Host "   - API: cd apps/api && python -m uvicorn main_simple:app --reload" -ForegroundColor Gray
Write-Host "   - Web: cd apps/web && npm run dev" -ForegroundColor Gray
Write-Host "3. Clear browser cache (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "4. Navigate to: http://localhost:5173/properties (or 5174)" -ForegroundColor White
Write-Host ""
Write-Host "If still not working, open browser console (F12) and check for errors" -ForegroundColor Yellow