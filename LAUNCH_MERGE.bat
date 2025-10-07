@echo off
color 0A
title ConcordBroker Auto-Merge System

:MENU
cls
echo.
echo ============================================
echo     CONCORDBROKER AUTO-MERGE SYSTEM
echo ============================================
echo.
echo Choose your merge option:
echo.
echo 1. FULL AUTO-MERGE (Recommended)
echo    - Cleans up processes
echo    - Installs dependencies
echo    - Builds everything
echo    - Starts all services
echo    - Runs tests
echo    - Generates report
echo.
echo 2. QUICK START (Services Only)
echo    - Kills old processes
echo    - Starts services immediately
echo.
echo 3. MANUAL MODE (Step by Step)
echo    - Interactive mode with confirmations
echo.
echo 4. EXIT
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto FULL_AUTO
if "%choice%"=="2" goto QUICK_START
if "%choice%"=="3" goto MANUAL_MODE
if "%choice%"=="4" goto EXIT
echo Invalid choice. Please try again.
pause
goto MENU

:FULL_AUTO
cls
echo Starting FULL AUTO-MERGE...
echo.
echo This will run completely automatically.
echo The process will take 2-5 minutes.
echo.
pause
powershell -ExecutionPolicy Bypass -File "AUTO_MERGE_COMPLETE.ps1"
goto END

:QUICK_START
cls
echo Starting QUICK START...
echo.
echo Killing old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3005') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /F /PID %%a 2>nul
timeout /t 2 /nobreak > nul

echo Starting services...
start "Backend API" /min cmd /c "cd apps\api && npm run dev"
timeout /t 3 /nobreak > nul
start "Frontend" /min cmd /c "cd apps\web && npm run dev"
timeout /t 3 /nobreak > nul

echo Opening browser...
timeout /t 5 /nobreak > nul
start http://localhost:5173

echo.
echo Quick start complete!
echo Services should be running at:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo.
pause
goto END

:MANUAL_MODE
cls
echo MANUAL MODE - Step by Step
echo.
echo Step 1: Kill old processes?
set /p confirm="(y/n): "
if /i "%confirm%"=="y" (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a 2>nul
    echo Processes killed.
)

echo.
echo Step 2: Install dependencies?
set /p confirm="(y/n): "
if /i "%confirm%"=="y" (
    echo Installing...
    cd apps\web && npm install && cd ..\..
    cd apps\api && npm install && cd ..\..
    echo Dependencies installed.
)

echo.
echo Step 3: Build frontend?
set /p confirm="(y/n): "
if /i "%confirm%"=="y" (
    cd apps\web && npm run build && cd ..\..
    echo Build complete.
)

echo.
echo Step 4: Start services?
set /p confirm="(y/n): "
if /i "%confirm%"=="y" (
    start "Backend API" /min cmd /c "cd apps\api && npm run dev"
    start "Frontend" /min cmd /c "cd apps\web && npm run dev"
    echo Services started.
)

echo.
echo Step 5: Open browser?
set /p confirm="(y/n): "
if /i "%confirm%"=="y" (
    timeout /t 5 /nobreak > nul
    start http://localhost:5173
)

echo.
echo Manual mode complete!
pause
goto END

:EXIT
echo Goodbye!
timeout /t 1 /nobreak > nul
exit

:END
echo.
echo ============================================
echo Process complete! Check your browser.
echo ============================================
pause