@echo off
REM ConcordBroker Startup Script - Windows Batch Version
REM Ensures correct Supabase connection to project: pmispwtdngkcmsrsjwbp

echo ========================================
echo    Starting ConcordBroker Services
echo    Project: pmispwtdngkcmsrsjwbp
echo ========================================
echo.

REM Clear any conflicting system environment variables
echo Clearing conflicting environment variables...
set SUPABASE_URL=
set SUPABASE_SERVICE_ROLE_KEY=
set SUPABASE_ANON_KEY=
set SUPABASE_KEY=
echo Environment cleaned
echo.

REM Start API server
echo Starting API Server on Port 8000...
start "ConcordBroker API" cmd /k "cd /d apps\api && python -m uvicorn main_simple:app --reload --host 0.0.0.0 --port 8000"

REM Wait for API to start
timeout /t 3 /nobreak > nul

REM Start web server
echo Starting Web Server on Port 5173...
start "ConcordBroker Web" cmd /k "cd /d apps\web && npm run dev"

REM Wait for services to fully start
timeout /t 5 /nobreak > nul

echo.
echo ========================================
echo    ConcordBroker Services Started!
echo ========================================
echo.
echo Available URLs:
echo   Web App:    http://localhost:5173
echo   API:        http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo   Supabase:   https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp
echo   Production: https://www.concordbroker.com
echo.
echo Database Info:
echo   Project:    pmispwtdngkcmsrsjwbp
echo   Table:      florida_parcels
echo.
echo Opening web browser...
start http://localhost:5173
echo.
echo To stop all services, close the command windows
pause