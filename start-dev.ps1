# PowerShell script to start development servers
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONCORDBROKER DEVELOPMENT SERVER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env file with your Supabase credentials!" -ForegroundColor Yellow
    Write-Host "Press any key to continue after updating .env..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Write-Host "Starting development servers..." -ForegroundColor Green
Write-Host ""

# Start FastAPI backend
Write-Host "📦 Starting API Server (FastAPI)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/api; Write-Host 'API Server starting on http://localhost:8000' -ForegroundColor Green; Write-Host 'API Docs: http://localhost:8000/docs' -ForegroundColor Green; python -m uvicorn main_dev:app --reload --port 8000"

# Wait a moment for API to start
Start-Sleep -Seconds 3

# Start React frontend
Write-Host "🌐 Starting Web Server (React)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/web; Write-Host 'Web Server starting on http://localhost:5173' -ForegroundColor Green; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SERVERS STARTING" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 API Server: http://localhost:8000" -ForegroundColor White
Write-Host "📍 API Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "📍 Web App:    http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop servers" -ForegroundColor Gray
Write-Host ""

# Open browser after a delay
Start-Sleep -Seconds 5
Write-Host "Opening browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"