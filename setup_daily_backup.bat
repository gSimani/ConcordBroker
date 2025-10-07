@echo off
echo ================================================================
echo  SUPABASE DAILY BACKUP SETUP
echo  Configures Windows Task Scheduler for automated daily backups
echo ================================================================
echo.

:: Get current directory
set "SCRIPT_DIR=%~dp0"
set "BACKUP_SCRIPT=%SCRIPT_DIR%daily_supabase_backup.py"

echo Setting up daily backup task...
echo Script location: %BACKUP_SCRIPT%
echo.

:: Check if Python is available
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

:: Check if backup script exists
if not exist "%BACKUP_SCRIPT%" (
    echo ERROR: Backup script not found at %BACKUP_SCRIPT%
    pause
    exit /b 1
)

:: Create the scheduled task
echo Creating Windows scheduled task...

schtasks /create /tn "Supabase Daily Backup" /tr "python \"%BACKUP_SCRIPT%\"" /sc daily /st 02:00 /f /rl highest

if %errorlevel%==0 (
    echo.
    echo [SUCCESS] Daily backup task created successfully!
    echo.
    echo Task Details:
    echo   Name: Supabase Daily Backup
    echo   Schedule: Daily at 2:00 AM
    echo   Script: %BACKUP_SCRIPT%
    echo   Run Level: Highest privileges
    echo.
    echo To manage this task:
    echo   View: schtasks /query /tn "Supabase Daily Backup"
    echo   Run now: schtasks /run /tn "Supabase Daily Backup"
    echo   Delete: schtasks /delete /tn "Supabase Daily Backup" /f
    echo.
) else (
    echo.
    echo [ERROR] Failed to create scheduled task.
    echo You may need to run this script as Administrator.
    echo.
)

:: Test the backup script
echo Testing backup script...
echo Running: python "%BACKUP_SCRIPT%"
echo.
echo Press any key to run a test backup, or Ctrl+C to skip...
pause >nul

python "%BACKUP_SCRIPT%"

echo.
echo ================================================================
echo  SETUP COMPLETE
echo ================================================================
echo.
echo The daily backup system is now configured to run at 2:00 AM daily.
echo Check the backup.log file for detailed logs.
echo Backups will be stored in: C:\TEMP\SUPABASE_BACKUPS\
echo.
pause