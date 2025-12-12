@echo off
REM ###########################################################################
REM ConcordBroker Project Cleanup Script (Windows)
REM Purpose: Safely remove files identified in security audit
REM Date: 2025-11-07
REM ###########################################################################

setlocal enabledelayedexpansion

REM Colors are limited in CMD, using text labels instead
set "TIMESTAMP=%date:~-4,4%-%date:~-10,2%-%date:~-7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "TIMESTAMP=!TIMESTAMP: =0!"
set "BACKUP_DIR=security_cleanup_backup_!TIMESTAMP!"

echo ========================================
echo ConcordBroker Cleanup Script (Windows)
echo ========================================
echo.

REM ###########################################################################
REM STEP 0: Pre-flight checks
REM ###########################################################################

if not exist "package.json" (
    echo [ERROR] Not in ConcordBroker root directory
    echo Please run this script from the project root
    exit /b 1
)

if not exist "apps\" (
    echo [ERROR] Not in ConcordBroker root directory
    echo Please run this script from the project root
    exit /b 1
)

where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] git is not installed
    exit /b 1
)

if not exist ".git\" (
    echo [ERROR] Not in a git repository
    exit /b 1
)

echo [OK] Pre-flight checks passed
echo.

REM ###########################################################################
REM STEP 1: Create backup directory
REM ###########################################################################
echo ========================================
echo STEP 1: Creating Backup
echo ========================================
echo.

mkdir "%BACKUP_DIR%" 2>nul
echo [OK] Created backup directory: %BACKUP_DIR%
echo.

REM ###########################################################################
REM STEP 2: Backup files with credentials (CRITICAL)
REM ###########################################################################
echo ========================================
echo STEP 2: Backing Up Credential Files
echo ========================================
echo.

set "CRED_FILES=apply_security_fixes.py apply_optimizations.py"

for %%f in (%CRED_FILES%) do (
    if exist "%%f" (
        copy "%%f" "%BACKUP_DIR%\" >nul
        echo [OK] Backed up: %%f
    ) else (
        echo [WARNING] Not found (already deleted?): %%f
    )
)
echo.

REM ###########################################################################
REM STEP 3: Backup obsolete files
REM ###########################################################################
echo ========================================
echo STEP 3: Backing Up Obsolete Files
echo ========================================
echo.

set "OBSOLETE_FILES=apply_all_fixes.py apply_sunbiz_fixes.py APPLY_TIMEOUTS_NOW.sql api.log api_diagnostic_report_2025-09-09T12-43-29-220Z.json api_diagnostic_report_2025-09-09T12-47-37-440Z.json"

for %%f in (%OBSOLETE_FILES%) do (
    if exist "%%f" (
        copy "%%f" "%BACKUP_DIR%\" >nul
        echo [OK] Backed up: %%f
    ) else (
        echo [WARNING] Not found: %%f
    )
)
echo.

REM ###########################################################################
REM STEP 4: Check git history for credential exposure
REM ###########################################################################
echo ========================================
echo STEP 4: Checking Git History
echo ========================================
echo.

set "EXPOSED_IN_GIT=false"

for %%f in (%CRED_FILES%) do (
    git log --all --full-history --oneline -- "%%f" >nul 2>nul
    if not errorlevel 1 (
        echo [CRITICAL] %%f found in git history
        set "EXPOSED_IN_GIT=true"
    ) else (
        echo [OK] %%f not in git history
    )
)

echo.

if "%EXPOSED_IN_GIT%"=="true" (
    echo ========================================
    echo [CRITICAL] CREDENTIALS EXPOSED IN GIT
    echo ========================================
    echo.
    echo You MUST rotate these credentials:
    echo   1. Database password ^(Supabase^)
    echo   2. Service role key ^(Supabase^)
    echo.
    echo See PROJECT_AUDIT_REPORT.md for detailed instructions
    echo.

    REM Create a reminder file
    (
        echo CRITICAL: CREDENTIALS ROTATION CHECKLIST
        echo ========================================
        echo.
        echo The following credentials were found in git history and MUST be rotated:
        echo.
        echo 1. DATABASE PASSWORD
        echo    - Go to: https://supabase.com/dashboard
        echo    - Settings -^> Database -^> Change password
        echo    - Update in:
        echo      [ ] .env.mcp
        echo      [ ] apps/api/.env
        echo      [ ] apps/web/.env
        echo      [ ] Railway environment variables
        echo      [ ] Vercel environment variables
        echo.
        echo 2. SUPABASE SERVICE ROLE KEY
        echo    - Go to: https://supabase.com/dashboard
        echo    - Settings -^> API -^> Regenerate service role key
        echo    - Update in:
        echo      [ ] .env.mcp ^(SUPABASE_SERVICE_ROLE_KEY^)
        echo      [ ] apps/api/.env ^(SUPABASE_SERVICE_ROLE_KEY^)
        echo      [ ] Railway environment variables
        echo      [ ] Vercel environment variables
        echo.
        echo 3. VERIFICATION
        echo    - [ ] Test local dev: npm run dev
        echo    - [ ] Test API: curl http://localhost:3005/health
        echo    - [ ] Test UI: Check properties load
        echo    - [ ] Test Railway deployment
        echo    - [ ] Test Vercel deployment
        echo.
        echo DO NOT SKIP THIS STEP!
        echo Your database and API are currently compromised.
        echo.
        echo Reference: PROJECT_AUDIT_REPORT.md
    ) > "%BACKUP_DIR%\ROTATE_CREDENTIALS_CHECKLIST.txt"

    echo [OK] Created checklist: %BACKUP_DIR%\ROTATE_CREDENTIALS_CHECKLIST.txt
    echo.
)

REM ###########################################################################
REM STEP 5: Delete credential files
REM ###########################################################################
echo ========================================
echo STEP 5: Deleting Credential Files
echo ========================================
echo.

for %%f in (%CRED_FILES%) do (
    if exist "%%f" (
        git ls-files --error-unmatch "%%f" >nul 2>nul
        if not errorlevel 1 (
            git rm "%%f"
            echo [OK] Deleted ^(git rm^): %%f
        ) else (
            del "%%f"
            echo [OK] Deleted ^(del^): %%f
        )
    ) else (
        echo [WARNING] Already deleted: %%f
    )
)
echo.

REM ###########################################################################
REM STEP 6: Delete obsolete files
REM ###########################################################################
echo ========================================
echo STEP 6: Deleting Obsolete Files
echo ========================================
echo.

for %%f in (%OBSOLETE_FILES%) do (
    if exist "%%f" (
        git ls-files --error-unmatch "%%f" >nul 2>nul
        if not errorlevel 1 (
            git rm "%%f"
            echo [OK] Deleted ^(git rm^): %%f
        ) else (
            del "%%f"
            echo [OK] Deleted ^(del^): %%f
        )
    ) else (
        echo [WARNING] Already deleted: %%f
    )
)
echo.

REM ###########################################################################
REM STEP 7: Reorganize keeper files
REM ###########################################################################
echo ========================================
echo STEP 7: Reorganizing Keeper Files
echo ========================================
echo.

REM Create directories
if not exist "scripts\database\" mkdir "scripts\database"
if not exist "docs\database\" mkdir "docs\database"
if not exist "scripts\testing\" mkdir "scripts\testing"

echo [OK] Created directory: scripts\database
echo [OK] Created directory: docs\database
echo [OK] Created directory: scripts\testing
echo.

REM Move files
if exist "apply_database_optimizations.py" (
    git ls-files --error-unmatch "apply_database_optimizations.py" >nul 2>nul
    if not errorlevel 1 (
        git mv "apply_database_optimizations.py" "scripts\database\"
        echo [OK] Moved ^(git mv^): apply_database_optimizations.py -^> scripts\database\
    ) else (
        move "apply_database_optimizations.py" "scripts\database\" >nul
        git add "scripts\database\apply_database_optimizations.py"
        echo [OK] Moved ^(move^): apply_database_optimizations.py -^> scripts\database\
    )
) else (
    if exist "scripts\database\apply_database_optimizations.py" (
        echo [WARNING] Already moved: apply_database_optimizations.py
    ) else (
        echo [WARNING] Not found: apply_database_optimizations.py
    )
)

if exist "APPLY_INDEXES_NOW.md" (
    git ls-files --error-unmatch "APPLY_INDEXES_NOW.md" >nul 2>nul
    if not errorlevel 1 (
        git mv "APPLY_INDEXES_NOW.md" "docs\database\"
        echo [OK] Moved ^(git mv^): APPLY_INDEXES_NOW.md -^> docs\database\
    ) else (
        move "APPLY_INDEXES_NOW.md" "docs\database\" >nul
        git add "docs\database\APPLY_INDEXES_NOW.md"
        echo [OK] Moved ^(move^): APPLY_INDEXES_NOW.md -^> docs\database\
    )
) else (
    if exist "docs\database\APPLY_INDEXES_NOW.md" (
        echo [WARNING] Already moved: APPLY_INDEXES_NOW.md
    ) else (
        echo [WARNING] Not found: APPLY_INDEXES_NOW.md
    )
)

if exist "api_endpoint_test.js" (
    git ls-files --error-unmatch "api_endpoint_test.js" >nul 2>nul
    if not errorlevel 1 (
        git mv "api_endpoint_test.js" "scripts\testing\"
        echo [OK] Moved ^(git mv^): api_endpoint_test.js -^> scripts\testing\
    ) else (
        move "api_endpoint_test.js" "scripts\testing\" >nul
        git add "scripts\testing\api_endpoint_test.js"
        echo [OK] Moved ^(move^): api_endpoint_test.js -^> scripts\testing\
    )
) else (
    if exist "scripts\testing\api_endpoint_test.js" (
        echo [WARNING] Already moved: api_endpoint_test.js
    ) else (
        echo [WARNING] Not found: api_endpoint_test.js
    )
)
echo.

REM ###########################################################################
REM STEP 8: Update .gitignore
REM ###########################################################################
echo ========================================
echo STEP 8: Updating .gitignore
echo ========================================
echo.

if exist ".gitignore" (
    findstr /C:"Security: Never commit files with potential credentials" ".gitignore" >nul 2>nul
    if errorlevel 1 (
        (
            echo.
            echo # Security: Never commit files with potential credentials
            echo *_fixes.py
            echo *_security*.py
            echo *.log
            echo *diagnostic_report*.json
            echo.
            echo # Backup directories
            echo security_cleanup_backup_*/
            echo security_backup_*/
        ) >> ".gitignore"
        git add ".gitignore"
        echo [OK] Updated .gitignore with security patterns
    ) else (
        echo [WARNING] .gitignore already has security patterns
    )
) else (
    (
        echo # Security: Never commit files with potential credentials
        echo *_fixes.py
        echo *_security*.py
        echo *.log
        echo *diagnostic_report*.json
        echo.
        echo # Backup directories
        echo security_cleanup_backup_*/
        echo security_backup_*/
    ) > ".gitignore"
    git add ".gitignore"
    echo [OK] Created .gitignore with security patterns
)
echo.

REM ###########################################################################
REM STEP 9: Show status and summary
REM ###########################################################################
echo ========================================
echo STEP 9: Summary
echo ========================================
echo.

echo Git Status:
git status --short
echo.

REM Create summary
(
    echo ConcordBroker Cleanup Summary
    echo ========================================
    echo Date: %TIMESTAMP%
    echo Backup Location: %BACKUP_DIR%
    echo.
    echo FILES DELETED ^(WITH CREDENTIALS^):
    for %%f in ^(%CRED_FILES%^) do echo   - %%f
    echo.
    echo FILES DELETED ^(OBSOLETE^):
    for %%f in ^(%OBSOLETE_FILES%^) do echo   - %%f
    echo.
    echo FILES REORGANIZED:
    echo   - apply_database_optimizations.py -^> scripts/database/
    echo   - APPLY_INDEXES_NOW.md -^> docs/database/
    echo   - api_endpoint_test.js -^> scripts/testing/
    echo.
    echo GIT HISTORY CHECK:
    if "%EXPOSED_IN_GIT%"=="true" (
        echo   [CRITICAL] CREDENTIALS FOUND IN GIT HISTORY
    ) else (
        echo   [OK] Credentials not in git history
    )
    echo.
    echo NEXT STEPS:
    if "%EXPOSED_IN_GIT%"=="true" (
        echo   1. [CRITICAL] ROTATE CREDENTIALS IMMEDIATELY ^(see checklist^)
    ) else (
        echo   1. [OK] No credential rotation needed
    )
    echo   2. Review changes: git status
    echo   3. Commit changes: git commit -m "security: cleanup audit files"
    echo   4. Push to remote: git push origin master
    echo.
    echo VERIFICATION:
    echo   - All backups are in: %BACKUP_DIR%
    echo   - Review PROJECT_AUDIT_REPORT.md for details
    if "%EXPOSED_IN_GIT%"=="true" (
        echo   - MUST rotate credentials before considering this complete
    )
) > "%BACKUP_DIR%\CLEANUP_SUMMARY.txt"

type "%BACKUP_DIR%\CLEANUP_SUMMARY.txt"
echo.

REM ###########################################################################
REM STEP 10: Next steps
REM ###########################################################################
echo ========================================
echo Next Steps
echo ========================================
echo.

if "%EXPOSED_IN_GIT%"=="true" (
    echo [CRITICAL] ROTATE CREDENTIALS FIRST
    echo.
    echo See: %BACKUP_DIR%\ROTATE_CREDENTIALS_CHECKLIST.txt
    echo.
    echo After rotating credentials:
) else (
    echo [OK] No credential rotation needed
    echo.
    echo You can now:
)

echo   1. Review changes:
echo      git status
echo.
echo   2. Commit changes:
echo      git commit -m "security: Remove files with hardcoded credentials and reorganize"
echo.
echo   3. Push to remote:
echo      git push origin master
echo.
echo   4. Verify everything works:
echo      npm run dev
echo.

echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo All files backed up to: %BACKUP_DIR%
echo Full report: PROJECT_AUDIT_REPORT.md
echo.

if "%EXPOSED_IN_GIT%"=="true" (
    echo [WARNING] DO NOT FORGET TO ROTATE CREDENTIALS!
    echo.
)

endlocal
exit /b 0
