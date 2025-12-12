@echo off
REM Automatic Port Configuration for Worktrees
REM Updates vite.config.ts in a worktree to use the correct port

setlocal enabledelayedexpansion

REM Get current branch
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i

echo Current branch: %CURRENT_BRANCH%

REM Set port based on branch (must match worktree-manager.bat)
set ASSIGNED_PORT=5191

if "%CURRENT_BRANCH%"=="master" set ASSIGNED_PORT=5191
if "%CURRENT_BRANCH%"=="feature/ui-consolidation" set ASSIGNED_PORT=5192
if "%CURRENT_BRANCH%"=="feature/api-enhancements" set ASSIGNED_PORT=5193
if "%CURRENT_BRANCH%"=="feature/database-optimization" set ASSIGNED_PORT=5194
if "%CURRENT_BRANCH%"=="feature/agent-development" set ASSIGNED_PORT=5195
if "%CURRENT_BRANCH%"=="hotfix/production" set ASSIGNED_PORT=5196
if "%CURRENT_BRANCH%"=="experimental/new-features" set ASSIGNED_PORT=5197
if "%CURRENT_BRANCH%"=="testing/integration" set ASSIGNED_PORT=5198

echo Assigned port: %ASSIGNED_PORT%
echo.

REM Path to vite config
set VITE_CONFIG=apps\web\vite.config.ts

if not exist "%VITE_CONFIG%" (
    echo Error: %VITE_CONFIG% not found
    echo Are you in the correct directory?
    exit /b 1
)

REM Backup original config
copy "%VITE_CONFIG%" "%VITE_CONFIG%.backup" >nul

REM Update port in vite.config.ts using PowerShell
powershell -Command "(Get-Content '%VITE_CONFIG%') -replace 'port: \d+,', 'port: %ASSIGNED_PORT%,' | Set-Content '%VITE_CONFIG%'"

echo ✓ Updated vite.config.ts
echo Port changed to: %ASSIGNED_PORT%
echo.
echo Verification:
findstr "port:" "%VITE_CONFIG%"
echo.
echo Backup saved: %VITE_CONFIG%.backup
echo.
echo Next steps:
echo   cd apps\web
echo   npm run dev
echo.
echo Your server will start on: http://localhost:%ASSIGNED_PORT%
