@echo off
REM Git Worktree Manager for ConcordBroker (Windows)
REM Manages multiple development streams with port isolation

setlocal enabledelayedexpansion

set "BASE_DIR=C:\Users\gsima\Documents\MyProject"
set "MAIN_REPO=%BASE_DIR%\ConcordBroker"

if "%1"=="" goto usage
if "%1"=="list" goto list
if "%1"=="create" goto create
if "%1"=="remove" goto remove
if "%1"=="ports" goto ports
if "%1"=="status" goto status
if "%1"=="clean" goto clean
if "%1"=="config" goto config
goto usage

:usage
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Git Worktree Manager for ConcordBroker
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo Usage: worktree-manager.bat [COMMAND] [OPTIONS]
echo.
echo Commands:
echo   list          - List all worktrees and their status
echo   create BRANCH - Create new worktree for branch
echo   remove BRANCH - Remove worktree for branch
echo   ports         - Show port assignments
echo   status        - Show detailed status of all worktrees
echo   clean         - Clean up deleted worktrees
echo   config BRANCH - Show configuration for a worktree
echo.
echo Examples:
echo   worktree-manager.bat list
echo   worktree-manager.bat create feature/ui-consolidation
echo   worktree-manager.bat remove experimental/new-features
echo   worktree-manager.bat ports
echo.
goto :eof

:list
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Active Git Worktrees
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
cd /d "%MAIN_REPO%"
git worktree list
echo.
echo Tip: Use 'worktree-manager.bat status' for detailed information
goto :eof

:ports
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Port Assignments for Worktrees
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo BRANCH                              PORT      DESCRIPTION
echo ────────────────────────────────────────────────────────────────────────────
echo master                              5191      Main development (current)
echo feature/ui-consolidation            5192      UI consolidation and improvements
echo feature/api-enhancements            5193      Backend API development
echo feature/database-optimization       5194      Database and query optimization
echo feature/agent-development           5195      AI agent development
echo hotfix/production                   5196      Production hotfixes
echo experimental/new-features           5197      Experimental features
echo testing/integration                 5198      Integration testing
echo.
echo Note: Each worktree should run on its assigned port to avoid conflicts
goto :eof

:create
if "%2"=="" (
    echo Error: Branch name required
    echo Usage: worktree-manager.bat create BRANCH_NAME
    goto :eof
)

set "BRANCH=%2"
set "WORKTREE_NAME=ConcordBroker-%BRANCH:/=-%"
set "WORKTREE_PATH=%BASE_DIR%\%WORKTREE_NAME%"

if exist "%WORKTREE_PATH%" (
    echo Worktree already exists at: %WORKTREE_PATH%
    goto :eof
)

echo Creating worktree for branch: %BRANCH%
echo Location: %WORKTREE_PATH%
echo.

cd /d "%MAIN_REPO%"

REM Check if branch exists and create worktree
git show-ref --verify --quiet refs/heads/%BRANCH% 2>nul
if %errorlevel% equ 0 (
    REM Branch exists locally
    git worktree add "%WORKTREE_PATH%" "%BRANCH%"
) else (
    git show-ref --verify --quiet refs/remotes/origin/%BRANCH% 2>nul
    if %errorlevel% equ 0 (
        REM Branch exists on remote
        git worktree add "%WORKTREE_PATH%" -b "%BRANCH%" "origin/%BRANCH%"
    ) else (
        REM Create new branch
        echo Branch doesn't exist. Creating new branch...
        git worktree add "%WORKTREE_PATH%" -b "%BRANCH%"
    )
)

echo.
echo ✓ Worktree created successfully!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Branch:      %BRANCH%
echo Path:        %WORKTREE_PATH%
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo Next steps:
echo 1. cd "%WORKTREE_PATH%"
echo 2. Update apps\web\vite.config.ts with assigned port
echo 3. npm install (if needed)
echo 4. npm run dev
goto :eof

:remove
if "%2"=="" (
    echo Error: Branch name required
    echo Usage: worktree-manager.bat remove BRANCH_NAME
    goto :eof
)

set "BRANCH=%2"
set "WORKTREE_NAME=ConcordBroker-%BRANCH:/=-%"
set "WORKTREE_PATH=%BASE_DIR%\%WORKTREE_NAME%"

if not exist "%WORKTREE_PATH%" (
    echo Worktree not found at: %WORKTREE_PATH%
    goto :eof
)

echo Removing worktree: %WORKTREE_PATH%
cd /d "%MAIN_REPO%"
git worktree remove "%WORKTREE_PATH%"
echo ✓ Worktree removed successfully
goto :eof

:status
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Worktree Status Report
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
cd /d "%MAIN_REPO%"
git worktree list
goto :eof

:clean
echo Cleaning up worktrees...
cd /d "%MAIN_REPO%"
git worktree prune
echo ✓ Cleanup complete
goto :eof

:config
if "%2"=="" (
    echo Error: Branch name required
    echo Usage: worktree-manager.bat config BRANCH_NAME
    goto :eof
)

set "BRANCH=%2"
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Configuration for: %BRANCH%
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo See worktree-manager.bat ports for port assignments
echo Path: %BASE_DIR%\ConcordBroker-%BRANCH:/=-%
goto :eof
