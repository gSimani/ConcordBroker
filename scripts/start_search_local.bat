@echo off
REM Quick Start Script for Local Search Development

echo ================================================
echo ConcordBroker Search Infrastructure - Local Dev
echo ================================================
echo.

REM Check if Meilisearch is installed
where meilisearch >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Meilisearch not found!
    echo.
    echo Install via:
    echo   - Windows: winget install meilisearch
    echo   - Or download from: https://github.com/meilisearch/meilisearch/releases
    echo.
    pause
    exit /b 1
)

REM Start Meilisearch in background
echo Starting Meilisearch...
start "Meilisearch" meilisearch --master-key="devMasterKey" --db-path="./meili_data"
timeout /t 3 >nul

REM Check if Meilisearch is running
curl -s http://localhost:7700/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Meilisearch failed to start!
    pause
    exit /b 1
)
echo ✓ Meilisearch running on http://localhost:7700

REM Set environment variables
set MEILISEARCH_URL=http://localhost:7700
set MEILISEARCH_KEY=devMasterKey

REM Start Search API
echo.
echo Starting Search API...
cd apps\api
start "Search API" python search_api.py
timeout /t 3 >nul
cd ..\..

REM Check if Search API is running
curl -s http://localhost:8001/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Search API may not have started yet
) else (
    echo ✓ Search API running on http://localhost:8001
)

echo.
echo ================================================
echo Services Started Successfully!
echo ================================================
echo.
echo Meilisearch: http://localhost:7700
echo Search API:  http://localhost:8001
echo.
echo Next steps:
echo   1. Index properties: python apps/api/meilisearch_indexer.py
echo   2. Test search: curl http://localhost:8001/api/search/instant?q=miami
echo   3. View dashboard: http://localhost:7700
echo.
echo Press any key to view logs (Ctrl+C to exit)...
pause >nul

REM Show logs
echo.
echo === Meilisearch Logs ===
type meili_data\logs\meilisearch.log 2>nul || echo No logs yet
echo.
echo === Search API Logs ===
echo Check the Search API window for logs
echo.
pause
