# Test script to verify localhost is working

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Testing ConcordBroker on Localhost" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor White
Write-Host ""

# Test API
Write-Host "Testing API Server..." -ForegroundColor Yellow
try {
    $apiResponse = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing
    if ($apiResponse.StatusCode -eq 200) {
        Write-Host "✅ API Server is running on http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ API Server is NOT running on http://localhost:8000" -ForegroundColor Red
    Write-Host "   Start it with: cd apps/api && python -m uvicorn main_dev:app --reload --port 8000" -ForegroundColor Yellow
}

# Test API Health
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✅ API Health check passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ API Health check failed" -ForegroundColor Red
}

Write-Host ""

# Test Web Server
Write-Host "Testing Web Server..." -ForegroundColor Yellow
try {
    $webResponse = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing
    if ($webResponse.StatusCode -eq 200) {
        Write-Host "✅ Web Server is running on http://localhost:5173" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Web Server is NOT running on http://localhost:5173" -ForegroundColor Red
    Write-Host "   Start it with: cd apps/web && npm run dev" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Available URLs:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Web Application:      http://localhost:5173" -ForegroundColor White
Write-Host "🏠 Dashboard:           http://localhost:5173/dashboard" -ForegroundColor White
Write-Host "🔍 Property Search:     http://localhost:5173/properties" -ForegroundColor White
Write-Host "📊 Analytics:           http://localhost:5173/analytics" -ForegroundColor White
Write-Host "📚 API Documentation:   http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Green