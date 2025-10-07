@echo off
REM Railway Deployment Helper Script
REM This script guides you through deploying Meilisearch and Search API to Railway Pro

echo ================================================================================
echo RAILWAY DEPLOYMENT HELPER
echo ================================================================================
echo.

REM Check if Railway CLI is installed
railway --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Railway CLI not found!
    echo Please install it first: npm install -g @railway/cli
    exit /b 1
)

echo Railway CLI: OK
echo.

REM Check if logged in
railway whoami >nul 2>&1
if errorlevel 1 (
    echo You need to login to Railway first.
    echo Opening browser for authentication...
    echo.
    railway login
    echo.
    echo After logging in, press any key to continue...
    pause >nul
)

echo Railway Auth: OK
echo.

echo ================================================================================
echo STEP 1: DEPLOY MEILISEARCH SERVICE
echo ================================================================================
echo.
echo This will:
echo - Create a new Railway project called "concordbroker-search"
echo - Deploy Meilisearch container
echo - Set environment variables
echo - Generate public domain
echo.
echo Press any key to start Meilisearch deployment...
pause >nul

REM Initialize project
echo Creating Railway project...
railway init concordbroker-search

REM Deploy Meilisearch
echo.
echo Deploying Meilisearch...
railway up --dockerfile Dockerfile.meilisearch

REM Set environment variables
echo.
echo Setting environment variables...
railway variables set MEILI_MASTER_KEY=concordbroker-meili-railway-prod-key-2025
railway variables set MEILI_ENV=production
railway variables set MEILI_NO_ANALYTICS=true

REM Generate domain
echo.
echo Generating public domain...
railway domain

echo.
echo ================================================================================
echo MEILISEARCH DEPLOYED!
echo ================================================================================
echo.
echo IMPORTANT: Copy the URL shown above and save it.
echo You'll need it for the next step.
echo.
echo Example: https://concordbroker-meilisearch-production.up.railway.app
echo.
set /p MEILI_URL="Enter your Meilisearch URL: "
echo.

echo ================================================================================
echo STEP 2: DEPLOY SEARCH API SERVICE
echo ================================================================================
echo.
echo This will:
echo - Create a second service called "search-api"
echo - Deploy FastAPI container
echo - Connect to Meilisearch and Supabase
echo - Generate public domain
echo.
echo Press any key to start Search API deployment...
pause >nul

REM Create search-api service
echo Creating search-api service...
railway service create search-api

REM Deploy Search API
echo.
echo Deploying Search API...
railway up --dockerfile Dockerfile.search-api --service search-api

REM Set environment variables
echo.
echo Setting environment variables...
railway variables set MEILISEARCH_URL=%MEILI_URL% --service search-api
railway variables set MEILISEARCH_KEY=concordbroker-meili-railway-prod-key-2025 --service search-api
railway variables set SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co --service search-api
railway variables set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0 --service search-api

REM Generate domain
echo.
echo Generating public domain for Search API...
railway domain --service search-api

echo.
echo ================================================================================
echo SEARCH API DEPLOYED!
echo ================================================================================
echo.
echo IMPORTANT: Copy the Search API URL shown above.
echo.
echo Example: https://concordbroker-search-api-production.up.railway.app
echo.
set /p SEARCH_API_URL="Enter your Search API URL: "
echo.

echo ================================================================================
echo DEPLOYMENT COMPLETE!
echo ================================================================================
echo.
echo Your services are now running on Railway:
echo.
echo Meilisearch URL: %MEILI_URL%
echo Search API URL:  %SEARCH_API_URL%
echo.
echo ================================================================================
echo NEXT STEPS:
echo ================================================================================
echo.
echo 1. Verify services are healthy:
echo    curl %MEILI_URL%/health
echo    curl %SEARCH_API_URL%/health
echo.
echo 2. Update railway_indexer.py with Meilisearch URL
echo.
echo 3. Index properties:
echo    cd ..\apps\api
echo    python railway_indexer.py 100000
echo.
echo 4. Update frontend PropertySearch.tsx with Search API URL
echo.
echo 5. Run Playwright tests to verify
echo.
echo See READY_TO_DEPLOY_SUMMARY.md for detailed instructions.
echo.
echo ================================================================================
echo.
pause
