@echo off
setlocal enabledelayedexpansion

:: ============================================
:: CONCORDBROKER AUTOMATED MERGE SYSTEM
:: This script runs ALL merge operations automatically
:: ============================================

echo.
echo ============================================
echo    CONCORDBROKER AUTOMATED MERGE SYSTEM
echo    Starting Complete Merge Process...
echo ============================================
echo.

:: Set up log file
set LOGFILE=merge_log_%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set LOGFILE=!LOGFILE: =0!
echo Starting merge at %date% %time% > %LOGFILE%

:: Function to log and display
call :LOG "=== PHASE 1: CLEANUP ==="

:: 1. Kill duplicate processes
call :LOG "Killing duplicate Node processes..."
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /F /PID %%a 2>nul
    if !errorlevel! equ 0 call :LOG "  Killed process on port 8000 (PID: %%a)"
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3005') do (
    taskkill /F /PID %%a 2>nul
    if !errorlevel! equ 0 call :LOG "  Killed process on port 3005 (PID: %%a)"
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8003') do (
    taskkill /F /PID %%a 2>nul
    if !errorlevel! equ 0 call :LOG "  Killed process on port 8003 (PID: %%a)"
)

timeout /t 3 /nobreak > nul

:: 2. Clean node_modules if needed
call :LOG "=== PHASE 2: DEPENDENCY CHECK ==="
if not exist node_modules (
    call :LOG "Installing root dependencies..."
    call npm install >> %LOGFILE% 2>&1
)

if not exist apps\web\node_modules (
    call :LOG "Installing frontend dependencies..."
    cd apps\web
    call npm install >> ..\..\%LOGFILE% 2>&1
    cd ..\..
)

if not exist apps\api\node_modules (
    call :LOG "Installing API dependencies..."
    cd apps\api
    call npm install >> ..\..\%LOGFILE% 2>&1
    cd ..\..
)

:: 3. Build all components
call :LOG "=== PHASE 3: BUILD PROCESS ==="

call :LOG "Building frontend..."
cd apps\web
call npm run build >> ..\..\%LOGFILE% 2>&1
if !errorlevel! neq 0 (
    call :LOG "  ERROR: Frontend build failed!"
) else (
    call :LOG "  SUCCESS: Frontend built"
)
cd ..\..

:: 4. Start services
call :LOG "=== PHASE 4: SERVICE STARTUP ==="

:: Start MCP Server if it exists
if exist mcp-server (
    call :LOG "Starting MCP Server..."
    start "MCP Server" /min cmd /c "cd mcp-server && npm start"
    timeout /t 3 /nobreak > nul
)

:: Start Backend API
call :LOG "Starting Backend API..."
start "Backend API" /min cmd /c "cd apps\api && npm run dev"
timeout /t 5 /nobreak > nul

:: Start Frontend
call :LOG "Starting Frontend..."
start "Frontend" /min cmd /c "cd apps\web && npm run dev"
timeout /t 5 /nobreak > nul

:: 5. Run automated tests
call :LOG "=== PHASE 5: AUTOMATED TESTING ==="

:: Check if services are running
call :LOG "Checking service health..."

:: Test Frontend
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 5; Write-Host '  Frontend: OK' } catch { Write-Host '  Frontend: FAILED' }"

:: Test API
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000' -UseBasicParsing -TimeoutSec 5; Write-Host '  Backend API: OK' } catch { Write-Host '  Backend API: FAILED' }"

:: Run integration tests if they exist
if exist test-unified-system.cjs (
    call :LOG "Running integration tests..."
    node test-unified-system.cjs >> %LOGFILE% 2>&1
)

:: 6. Data verification
call :LOG "=== PHASE 6: DATA VERIFICATION ==="

:: Create a test script to verify data
echo const axios = require('axios'); > verify-data.js
echo async function verify() { >> verify-data.js
echo   try { >> verify-data.js
echo     const res = await axios.get('http://localhost:8000/api/properties/474131031040'); >> verify-data.js
echo     console.log('Data verification: ' + (res.data ? 'PASSED' : 'FAILED')); >> verify-data.js
echo   } catch(e) { >> verify-data.js
echo     console.log('Data verification: FAILED - ' + e.message); >> verify-data.js
echo   } >> verify-data.js
echo } >> verify-data.js
echo verify(); >> verify-data.js

node verify-data.js >> %LOGFILE% 2>&1
del verify-data.js

:: 7. Generate summary report
call :LOG "=== PHASE 7: GENERATING REPORT ==="

:: Create summary report
echo. > MERGE_REPORT.txt
echo ============================================ >> MERGE_REPORT.txt
echo    CONCORDBROKER MERGE COMPLETION REPORT >> MERGE_REPORT.txt
echo    Generated: %date% %time% >> MERGE_REPORT.txt
echo ============================================ >> MERGE_REPORT.txt
echo. >> MERGE_REPORT.txt

:: Check running services
echo SERVICES STATUS: >> MERGE_REPORT.txt
echo ---------------- >> MERGE_REPORT.txt
netstat -ano | findstr LISTENING | findstr "5173 8000 3005 8003" >> MERGE_REPORT.txt
echo. >> MERGE_REPORT.txt

:: Memory usage
echo MEMORY USAGE: >> MERGE_REPORT.txt
echo ------------- >> MERGE_REPORT.txt
wmic process where "name='node.exe'" get ProcessId,WorkingSetSize /format:list | findstr "=" >> MERGE_REPORT.txt
echo. >> MERGE_REPORT.txt

:: Git status
echo GIT STATUS: >> MERGE_REPORT.txt
echo ----------- >> MERGE_REPORT.txt
git status --short >> MERGE_REPORT.txt 2>&1
echo. >> MERGE_REPORT.txt

:: Final status
call :LOG "=== MERGE PROCESS COMPLETE ==="
call :LOG "Report saved to: MERGE_REPORT.txt"
call :LOG "Log saved to: %LOGFILE%"

:: Open browser to test
call :LOG "Opening application in browser..."
start http://localhost:5173

echo.
echo ============================================
echo    MERGE COMPLETE!
echo ============================================
echo.
echo Services running at:
echo   Frontend: http://localhost:5173
echo   API:      http://localhost:8000
echo.
echo Check MERGE_REPORT.txt for details
echo.
pause
goto :EOF

:: Logging function
:LOG
echo %~1
echo %date% %time%: %~1 >> %LOGFILE%
goto :EOF