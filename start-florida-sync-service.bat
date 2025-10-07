@echo off
REM Florida Data Sync Service - Windows Service Launcher
echo ========================================
echo FLORIDA DATA SYNC SERVICE
echo ========================================
echo Starting daily synchronization service...
echo.

REM Install required packages if not present
echo Checking dependencies...
call npm install node-schedule adm-zip csv-parser

echo.
echo ========================================
echo SERVICE COMMANDS:
echo ========================================
echo 1. Run sync once:     node florida-data-sync-service.cjs
echo 2. Start scheduler:   node florida-data-sync-service.cjs --schedule
echo.

REM Ask user what they want to do
set /p choice="Choose (1) Run once, (2) Start scheduler, or (Enter) to exit: "

if "%choice%"=="1" (
    echo.
    echo Running one-time synchronization...
    node florida-data-sync-service.cjs
) else if "%choice%"=="2" (
    echo.
    echo Starting scheduled service (daily at 3 AM EST)...
    echo Press Ctrl+C to stop the service
    node florida-data-sync-service.cjs --schedule
) else (
    echo Exiting...
    pause
    exit
)

pause