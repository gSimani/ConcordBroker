@echo off
echo ================================================================
echo  ConcordBroker OPTIMIZED Performance Services
echo  SQLAlchemy + Redis + Playwright + OpenCV Integration
echo ================================================================
echo.

:: Check requirements
echo [1/7] Checking dependencies...
echo ----------------------------------------------------------------

:: Check Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js first.
    pause
    exit /b 1
)

:: Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

:: Check Redis
redis-cli ping >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Redis not running. Starting Redis...
    start "Redis Server" redis-server
    timeout /t 3 /nobreak >nul
)

echo Dependencies OK!
echo.

:: Install Python requirements if needed
echo [2/7] Installing Python packages...
echo ----------------------------------------------------------------
pip install -q sqlalchemy redis aioredis aiocache psycopg2-binary opencv-python-headless playwright pytesseract pillow scikit-learn 2>nul
echo Python packages ready!
echo.

:: Start Redis if not running
echo [3/7] Ensuring Redis Cache is running...
echo ----------------------------------------------------------------
redis-cli ping >nul 2>nul
if %errorlevel% neq 0 (
    start "Redis Cache" cmd /k "redis-server --port 6379"
    timeout /t 3 /nobreak >nul
)
echo Redis Cache: Running on port 6379
echo.

:: Start MCP Server with monitoring
echo [4/7] Starting MCP Server with Enhanced Monitoring...
echo ----------------------------------------------------------------
start "MCP Server" cmd /k "cd mcp-server && npm start"
timeout /t 3 /nobreak >nul

:: Initialize MCP with ultimate configuration
start "MCP Ultimate Init" cmd /k "node claude-code-ultimate-init.cjs"
timeout /t 2 /nobreak >nul
echo MCP Server: http://localhost:3001
echo.

:: Start Optimized Property Service (SQLAlchemy)
echo [5/7] Starting Optimized Property Service (SQLAlchemy)...
echo ----------------------------------------------------------------
start "Optimized API" cmd /k "cd apps/api && python optimized_property_service.py"
timeout /t 3 /nobreak >nul
echo Optimized API: http://localhost:8001
echo.

:: Start Performance Monitor (Playwright)
echo [6/7] Starting Performance Monitor (Playwright)...
echo ----------------------------------------------------------------
start "Performance Monitor" cmd /k "cd apps/api && python -c ""import asyncio; from playwright_performance_monitor import PlaywrightPerformanceMonitor; monitor = PlaywrightPerformanceMonitor(); print('Performance monitor ready. Access reports at /performance_reports/')"" && pause"
timeout /t 2 /nobreak >nul
echo Performance Monitor: Active
echo.

:: Start React Frontend
echo [7/7] Starting React Frontend...
echo ----------------------------------------------------------------
start "React Frontend" cmd /k "cd apps/web && npm run dev"
timeout /t 3 /nobreak >nul
echo Frontend: http://localhost:5173
echo.

echo ================================================================
echo  OPTIMIZED SERVICES STARTED SUCCESSFULLY!
echo ================================================================
echo.
echo  Performance Stack:
echo   - SQLAlchemy DB:     Connection pooling + Query caching
echo   - Redis Cache:       In-memory caching (port 6379)
echo   - Optimized API:     http://localhost:8001
echo   - MCP Server:        http://localhost:3001
echo   - Frontend:          http://localhost:5173
echo.
echo  Monitoring:
echo   - Playwright Tests:  Automated UI/API testing
echo   - OpenCV Analysis:   Property image processing
echo   - Performance:       Real-time metrics tracking
echo.
echo  API Endpoints:
echo   - /api/properties/search/optimized   (Cached search)
echo   - /api/properties/{id}/detailed      (Eager loading)
echo   - /api/properties/bulk-search        (Batch operations)
echo   - /api/analytics/market-trends       (Aggregations)
echo   - /                                  (Health + Metrics)
echo.
echo  Cache Info:
echo   - Memory cache: 5 min TTL
echo   - Redis cache:  Configurable TTL
echo   - Hit rate:     Monitored in /health
echo.
echo ----------------------------------------------------------------
echo  Opening Performance Dashboard...
timeout /t 3 /nobreak >nul

:: Open services in browser
start "" "http://localhost:8001"
timeout /t 1 /nobreak >nul
start "" "http://localhost:5173"
timeout /t 1 /nobreak >nul
start "" "http://localhost:3001/health"

echo.
echo  Press any key to run performance benchmark...
pause >nul

:: Run performance test
echo.
echo Running performance benchmark...
echo ================================================================
python -c "import asyncio; from apps.api.playwright_performance_monitor import main; asyncio.run(main())"

echo.
echo ================================================================
echo  Session running. Close this window to stop all services.
echo ================================================================
pause