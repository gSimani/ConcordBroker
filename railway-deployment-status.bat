@echo off
echo ================================================================
echo  Railway Deployment Status Report
echo ================================================================
echo.
echo  Project ID: 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
echo  Environment: production
echo.

echo ----------------------------------------------------------------
echo  LOCAL VERIFICATION
echo ----------------------------------------------------------------

echo [1] Checking required files...
echo.

if exist "main.py" (
    echo   [OK] main.py exists
) else (
    echo   [FAIL] main.py NOT FOUND - Railway won't find entry point!
)

if exist "requirements.txt" (
    echo   [OK] requirements.txt exists at root
) else (
    echo   [FAIL] requirements.txt NOT FOUND at root - Railway won't find dependencies!
)

if exist "railway.json" (
    echo   [OK] railway.json exists
) else (
    echo   [FAIL] railway.json NOT FOUND
)

if exist "nixpacks.toml" (
    echo   [OK] nixpacks.toml exists
) else (
    echo   [FAIL] nixpacks.toml NOT FOUND
)

if exist "Procfile" (
    echo   [OK] Procfile exists
) else (
    echo   [WARN] Procfile NOT FOUND (optional)
)

echo.
echo ----------------------------------------------------------------
echo  RAILWAY DEPLOYMENT READINESS
echo ----------------------------------------------------------------
echo.
echo [2] Testing local execution...
echo.

python -c "import sys; sys.path.insert(0, 'apps/api'); from ultimate_autocomplete_api import app; print('  [OK] Can import ultimate_autocomplete_api')" 2>nul
if %errorlevel% neq 0 (
    python -c "import sys; sys.path.insert(0, 'apps/api'); from property_live_api import app; print('  [OK] Can import property_live_api')" 2>nul
    if %errorlevel% neq 0 (
        echo   [WARN] Cannot import APIs, will use fallback
    )
)

echo.
echo ----------------------------------------------------------------
echo  DEPLOYMENT CHECKLIST
echo ----------------------------------------------------------------
echo.
echo [ ] 1. All files committed to Git?
echo        Run: git status
echo.
echo [ ] 2. Pushed to GitHub main branch?
echo        Run: git push origin main
echo.
echo [ ] 3. Railway environment variables set?
echo        Required in Railway dashboard:
echo        - SUPABASE_URL
echo        - SUPABASE_ANON_KEY
echo        - SUPABASE_SERVICE_ROLE_KEY
echo        - PORT=8000
echo        - PYTHON_VERSION=3.10
echo.
echo [ ] 4. Railway connected to GitHub?
echo        Check: https://railway.app/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
echo.
echo ----------------------------------------------------------------
echo  DEPLOYMENT COMMAND
echo ----------------------------------------------------------------
echo.
echo To deploy now, run these commands:
echo.
echo   git add .
echo   git commit -m "fix: Railway deployment configuration"
echo   git push origin main
echo.
echo Then go to Railway dashboard and click "Redeploy"
echo.
echo ----------------------------------------------------------------
echo  RAILWAY DASHBOARD
echo ----------------------------------------------------------------
echo.
echo Open Railway dashboard:
echo   https://railway.app/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
echo.
echo Check these tabs:
echo   - Deployments: See build logs
echo   - Variables: Verify environment variables
echo   - Settings: Check GitHub connection
echo   - Logs: View runtime logs
echo.
pause