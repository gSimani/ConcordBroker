@echo off
echo ================================================================
echo  ConcordBroker OPTIMIZED Performance Session
echo  With PySpark, Redis, FastAPI, and Performance Monitoring
echo ================================================================
echo.

:: Check prerequisites
echo [1/8] Checking Prerequisites...
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
where redis-cli >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Redis not found. Installing Redis...
    echo Please download Redis from: https://github.com/microsoftarchive/redis/releases
    echo Or use WSL: wsl --install
    echo Then: sudo apt update && sudo apt install redis-server
)

echo Prerequisites OK!

echo.
echo [2/8] Starting Redis Cache Server...
echo ----------------------------------------------------------------
:: Try WSL Redis first
wsl -e redis-server --daemonize yes >nul 2>nul
if %errorlevel% equ 0 (
    echo Redis started in WSL
) else (
    :: Try native Windows Redis
    start "Redis Server" cmd /k "redis-server"
    timeout /t 2 /nobreak >nul
)

echo.
echo [3/8] Starting MCP Server with Monitoring (Port 3001)...
echo ----------------------------------------------------------------
start "MCP Server" cmd /k "cd mcp-server && npm start"
timeout /t 3 /nobreak >nul

echo.
echo [4/8] Starting Optimized Fast API (Port 8001)...
echo ----------------------------------------------------------------
start "Fast Property API" cmd /k "cd apps/api && python fast_property_api.py"
timeout /t 3 /nobreak >nul

echo.
echo [5/8] Starting Original API for Compatibility (Port 8000)...
echo ----------------------------------------------------------------
start "Property API" cmd /k "cd apps/api && python property_live_api.py"
timeout /t 2 /nobreak >nul

echo.
echo [6/8] Starting React Frontend (Port 5173)...
echo ----------------------------------------------------------------
start "React Frontend" cmd /k "cd apps/web && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo [7/8] Initializing Performance Monitor...
echo ----------------------------------------------------------------
:: Pre-compute aggregations in background
start "Data Engine" cmd /k "cd apps/api && python -c \"from optimized_data_engine import get_data_engine; engine = get_data_engine(); engine.precompute_aggregations(); print('Aggregations cached')\""
timeout /t 2 /nobreak >nul

echo.
echo [8/8] Opening Dashboard and Services...
echo ----------------------------------------------------------------
timeout /t 5 /nobreak >nul

:: Open services in browser
start "" "http://localhost:5173"
timeout /t 1 /nobreak >nul
start "" "http://localhost:8001/docs"
timeout /t 1 /nobreak >nul

echo.
echo ================================================================
echo  🚀 OPTIMIZED ConcordBroker Session Started Successfully!
echo ================================================================
echo.
echo  Frontend:          http://localhost:5173
echo  Fast API:          http://localhost:8001 (Optimized)
echo  Original API:      http://localhost:8000 (Fallback)
echo  Fast API Docs:     http://localhost:8001/docs
echo  MCP Server:        http://localhost:3001
echo  Redis Cache:       localhost:6379
echo.
echo  Performance Features Enabled:
echo   ✓ Redis multi-layer caching
echo   ✓ Connection pooling (20 connections)
echo   ✓ NumPy vectorized calculations
echo   ✓ In-memory hot data cache
echo   ✓ Background cache warming
echo   ✓ Async/await optimizations
echo.
echo  To run performance analysis:
echo   1. Open new terminal
echo   2. Run: jupyter notebook performance_analysis.ipynb
echo.
echo  To monitor real-time performance:
echo   1. Open new terminal
echo   2. Run: python playwright_performance_monitor.py
echo.
echo Press any key to keep services running...
pause >nul

echo.
echo Shutting down services...
taskkill /F /IM redis-server.exe >nul 2>nul
wsl -e redis-cli shutdown >nul 2>nul
echo Services stopped.