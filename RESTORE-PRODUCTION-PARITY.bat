@echo off
REM ============================================
REM ONE-CLICK PRODUCTION PARITY RESTORATION
REM ============================================
REM Automatically syncs local environment to match production exactly
REM Includes Vercel, Railway, and Supabase configurations

echo.
echo ========================================
echo PRODUCTION PARITY RESTORATION SYSTEM
echo ========================================
echo.
echo This will sync your local environment to match production:
echo - Git: Checkout exact production commit
echo - Vercel: Pull production environment variables
echo - Railway: Sync backend configuration
echo - Supabase: Setup local database (optional)
echo.
echo Press Ctrl+C to cancel, or
pause

REM Check for required tools
echo.
echo Checking prerequisites...

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed
    exit /b 1
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: npm is not installed
    exit /b 1
)

REM Ask user for sync options
echo.
echo Select sync mode:
echo 1. Full Sync (Code + Environment + Database)
echo 2. Code + Environment Only
echo 3. Environment Variables Only
echo 4. Database Only
echo 5. Quick Sync (Code + Env, skip database)
echo.
set /p syncMode="Enter option (1-5): "

REM Set flags based on user choice
set fullSync=false
set skipDatabase=true
set envOnly=false
set dbOnly=false

if "%syncMode%"=="1" (
    set fullSync=true
    set skipDatabase=false
)
if "%syncMode%"=="2" (
    set skipDatabase=true
)
if "%syncMode%"=="3" (
    set envOnly=true
)
if "%syncMode%"=="4" (
    set dbOnly=true
    set skipDatabase=false
)
if "%syncMode%"=="5" (
    set skipDatabase=true
)

REM Execute PowerShell sync script
echo.
echo Starting sync process...
echo.

powershell.exe -ExecutionPolicy Bypass -File "scripts\production-parity-sync.ps1" ^
    %if "%fullSync%"=="true" (-FullSync)% ^
    %if "%envOnly%"=="true" (-EnvironmentOnly)% ^
    %if "%dbOnly%"=="true" (-DatabaseOnly)% ^
    %if "%skipDatabase%"=="true" (-SkipDataImport)%

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Sync process failed
    echo Check the log file for details
    pause
    exit /b 1
)

echo.
echo ========================================
echo SYNC COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Your local environment now matches production.
echo.
echo Services are running at:
echo - Frontend: http://localhost:5173
echo - Backend: http://localhost:8000
echo - Supabase Studio: http://localhost:54323 (if enabled)
echo.
echo Next steps:
echo 1. Clear your browser cache
echo 2. Open http://localhost:5173 in incognito mode
echo 3. Test your application
echo.
echo To monitor for drift, run: node scripts\parity-monitor-agent.js
echo.

REM Ask if user wants to start monitor
set /p startMonitor="Start parity monitor agent? (y/n): "

if /i "%startMonitor%"=="y" (
    echo.
    echo Starting monitor agent in background...
    start /b node scripts\parity-monitor-agent.js
    echo Monitor agent started!
)

echo.
pause