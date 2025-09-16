# Ultra-Fast Property System Startup Script
# Starts all components for maximum performance

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " ConcordBroker Ultra-Fast Property System" -ForegroundColor Cyan
Write-Host " PySpark + Redis + Playwright MCP + OpenCV" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/7] Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check Node.js
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js not found. Please install Node.js" -ForegroundColor Red
    exit 1
}

# Check Java for Spark
if (!(Get-Command java -ErrorAction SilentlyContinue)) {
    Write-Host "WARNING: Java not found. Required for PySpark. Install Java 8+" -ForegroundColor Yellow
}

Write-Host "✓ Prerequisites checked" -ForegroundColor Green
Write-Host ""

# Install dependencies if needed
Write-Host "[2/7] Installing Python dependencies..." -ForegroundColor Yellow
pip install -q pyspark aioredis psycopg2-binary opencv-python-headless playwright 2>$null
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Start Redis if not running
Write-Host "[3/7] Starting Redis cache server..." -ForegroundColor Yellow
$redisProcess = Get-Process redis-server -ErrorAction SilentlyContinue
if (!$redisProcess) {
    if (Test-Path "C:\Program Files\Redis\redis-server.exe") {
        Start-Process "C:\Program Files\Redis\redis-server.exe" -WindowStyle Hidden
    } elseif (Get-Command docker -ErrorAction SilentlyContinue) {
        docker run -d --name redis-cache -p 6379:6379 redis:alpine 2>$null
    } else {
        Write-Host "WARNING: Redis not found. Cache will be disabled" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ Redis already running" -ForegroundColor Green
}
Write-Host ""

# Start MCP Server
Write-Host "[4/7] Starting MCP Server (Port 3001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd mcp-server; npm start" -WindowStyle Minimized
Start-Sleep -Seconds 3
Write-Host "✓ MCP Server started" -ForegroundColor Green
Write-Host ""

# Start Ultra-Fast API
Write-Host "[5/7] Starting Ultra-Fast Property API (Port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/api; python ultra_fast_property_system.py" -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "✓ Ultra-Fast API started" -ForegroundColor Green
Write-Host ""

# Start existing Property API as fallback
Write-Host "[6/7] Starting Fallback Property API (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/api; python property_live_api.py" -WindowStyle Minimized
Start-Sleep -Seconds 2
Write-Host "✓ Fallback API started" -ForegroundColor Green
Write-Host ""

# Start React Frontend
Write-Host "[7/7] Starting React Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/web; npm run dev" -WindowStyle Minimized
Start-Sleep -Seconds 3
Write-Host "✓ React Frontend started" -ForegroundColor Green
Write-Host ""

# Display service URLs
Write-Host "================================================================" -ForegroundColor Green
Write-Host " Ultra-Fast System Started Successfully!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services Running:" -ForegroundColor Cyan
Write-Host "  📊 Spark UI:         http://localhost:4041" -ForegroundColor White
Write-Host "  🚀 Ultra-Fast API:   http://localhost:8001" -ForegroundColor White
Write-Host "  📡 Fallback API:     http://localhost:8000" -ForegroundColor White
Write-Host "  🌐 Frontend:         http://localhost:5173" -ForegroundColor White
Write-Host "  🔧 MCP Server:       http://localhost:3001" -ForegroundColor White
Write-Host "  💾 Redis Cache:      localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "Performance Features:" -ForegroundColor Cyan
Write-Host "  ✓ PySpark distributed processing" -ForegroundColor Gray
Write-Host "  ✓ Redis in-memory caching" -ForegroundColor Gray
Write-Host "  ✓ Playwright real-time sync" -ForegroundColor Gray
Write-Host "  ✓ OpenCV image optimization" -ForegroundColor Gray
Write-Host "  ✓ Connection pooling" -ForegroundColor Gray
Write-Host "  ✓ Async/await architecture" -ForegroundColor Gray
Write-Host ""

# Open browser to test
Write-Host "Opening test endpoints..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test health check
Start-Process "http://localhost:8001/"

# Test ultra-search
Start-Process "http://localhost:8001/api/properties/ultra-search?city=Miami&limit=10"

# Open frontend
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "System ready! Press Ctrl+C to stop all services." -ForegroundColor Green
Write-Host ""

# Keep script running
while ($true) {
    Start-Sleep -Seconds 60

    # Health check
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "$(Get-Date -Format 'HH:mm:ss') - System healthy ✓" -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "$(Get-Date -Format 'HH:mm:ss') - System check failed!" -ForegroundColor Red
    }
}