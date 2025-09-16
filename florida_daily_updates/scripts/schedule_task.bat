@echo off
REM Florida Daily Updates - Windows Task Scheduler Setup
REM Run this script as Administrator to create scheduled tasks

echo ========================================
echo Florida Daily Updates - Task Scheduler
echo ========================================
echo.

REM Get current directory
set SCRIPT_DIR=%~dp0
set BASE_DIR=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%BASE_DIR%\scripts\run_daily_update.py

echo Script Directory: %SCRIPT_DIR%
echo Base Directory: %BASE_DIR%
echo Python Script: %PYTHON_SCRIPT%
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator... OK
) else (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as Administrator"
    pause
    exit /b 1
)

echo.
echo Creating Florida Daily Updates scheduled tasks...
echo.

REM Delete existing tasks if they exist
echo Removing existing tasks...
schtasks /delete /tn "Florida-Daily-Updates" /f >nul 2>&1
schtasks /delete /tn "Florida-Monitor-Check" /f >nul 2>&1
schtasks /delete /tn "Florida-Maintenance" /f >nul 2>&1

REM Create daily update task (2 AM daily)
echo Creating daily update task...
schtasks /create ^
    /tn "Florida-Daily-Updates" ^
    /tr "python \"%PYTHON_SCRIPT%\" --mode full" ^
    /sc daily ^
    /st 02:00 ^
    /sd 01/01/2025 ^
    /ru "SYSTEM" ^
    /rl highest ^
    /f

if %errorlevel% == 0 (
    echo   ✓ Daily update task created successfully
) else (
    echo   ✗ Failed to create daily update task
)

REM Create monitoring task (every 6 hours)
echo Creating monitoring task...
schtasks /create ^
    /tn "Florida-Monitor-Check" ^
    /tr "python \"%PYTHON_SCRIPT%\" --mode monitor" ^
    /sc hourly ^
    /mo 6 ^
    /sd 01/01/2025 ^
    /ru "SYSTEM" ^
    /rl highest ^
    /f

if %errorlevel% == 0 (
    echo   ✓ Monitor check task created successfully
) else (
    echo   ✗ Failed to create monitor check task
)

REM Create maintenance task (weekly on Sunday at 3 AM)
echo Creating maintenance task...
schtasks /create ^
    /tn "Florida-Maintenance" ^
    /tr "python \"%PYTHON_SCRIPT%\" --mode maintenance" ^
    /sc weekly ^
    /d SUN ^
    /st 03:00 ^
    /sd 01/01/2025 ^
    /ru "SYSTEM" ^
    /rl highest ^
    /f

if %errorlevel% == 0 (
    echo   ✓ Maintenance task created successfully
) else (
    echo   ✗ Failed to create maintenance task
)

echo.
echo ========================================
echo Task creation completed!
echo ========================================
echo.

REM List created tasks
echo Created tasks:
schtasks /query /tn "Florida-Daily-Updates" /fo list 2>nul | findstr "TaskName\|Next Run Time\|Status"
schtasks /query /tn "Florida-Monitor-Check" /fo list 2>nul | findstr "TaskName\|Next Run Time\|Status"  
schtasks /query /tn "Florida-Maintenance" /fo list 2>nul | findstr "TaskName\|Next Run Time\|Status"

echo.
echo Task Management Commands:
echo   View all tasks:    schtasks /query /fo table
echo   Run daily update:  schtasks /run /tn "Florida-Daily-Updates"
echo   Run monitor:       schtasks /run /tn "Florida-Monitor-Check"
echo   Run maintenance:   schtasks /run /tn "Florida-Maintenance"
echo   Delete all tasks:  schtasks /delete /tn "Florida-*" /f
echo.
echo To view task details, use:
echo   schtasks /query /tn "Florida-Daily-Updates" /v /fo list
echo.
echo Logs will be available in:
echo   %BASE_DIR%\logs\
echo.

pause