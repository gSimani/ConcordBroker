@echo off
echo ================================================================================
echo RAILWAY DEPLOYMENT - AUTOMATED
echo ================================================================================
echo.
echo This script will deploy Meilisearch and Search API to Railway Pro.
echo.
echo STEP 1: LOGIN TO RAILWAY
echo ================================================================================
echo.
echo Opening browser for Railway authentication...
echo After logging in, return to this window and press any key.
echo.

railway login

if errorlevel 1 (
    echo.
    echo ERROR: Railway login failed or was cancelled.
    echo Please try again.
    pause
    exit /b 1
)

echo.
echo ✅ Railway login successful!
echo.
pause

echo.
echo STEP 2: DEPLOY MEILISEARCH SERVICE
echo ================================================================================
echo.

cd railway-deploy

echo Creating Railway project: concordbroker-search
railway init concordbroker-search

echo.
echo Deploying Meilisearch container...
railway up --dockerfile Dockerfile.meilisearch

echo.
echo Setting Meilisearch environment variables...
railway variables set MEILI_MASTER_KEY=concordbroker-meili-railway-prod-key-2025
railway variables set MEILI_ENV=production
railway variables set MEILI_NO_ANALYTICS=true

echo.
echo Generating public domain for Meilisearch...
railway domain

echo.
echo ✅ Meilisearch deployed!
echo.
echo IMPORTANT: Copy the Meilisearch URL shown above.
echo Example: https://concordbroker-meilisearch-production.up.railway.app
echo.
set /p MEILI_URL="Enter your Meilisearch URL: "

echo.
echo Testing Meilisearch health...
curl %MEILI_URL%/health

echo.
pause

echo.
echo STEP 3: DEPLOY SEARCH API SERVICE
echo ================================================================================
echo.

echo Creating Search API service...
railway service create search-api

echo.
echo Deploying Search API container...
railway up --dockerfile Dockerfile.search-api --service search-api

echo.
echo Setting Search API environment variables...
railway variables set MEILISEARCH_URL=%MEILI_URL% --service search-api
railway variables set MEILISEARCH_KEY=concordbroker-meili-railway-prod-key-2025 --service search-api
railway variables set SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co --service search-api
railway variables set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0 --service search-api

echo.
echo Generating public domain for Search API...
railway domain --service search-api

echo.
echo ✅ Search API deployed!
echo.
echo IMPORTANT: Copy the Search API URL shown above.
echo Example: https://concordbroker-search-api-production.up.railway.app
echo.
set /p SEARCH_API_URL="Enter your Search API URL: "

echo.
echo Testing Search API health...
curl %SEARCH_API_URL%/health

echo.
pause

echo.
echo ================================================================================
echo DEPLOYMENT COMPLETE!
echo ================================================================================
echo.
echo Your services are now running on Railway Pro:
echo.
echo Meilisearch URL: %MEILI_URL%
echo Search API URL:  %SEARCH_API_URL%
echo.
echo ================================================================================
echo NEXT STEPS
echo ================================================================================
echo.
echo 1. Update railway_indexer.py with Meilisearch URL:
echo    - Edit apps/api/railway_indexer.py
echo    - Line 12: MEILI_URL = '%MEILI_URL%'
echo.
echo 2. Index properties to Railway:
echo    cd ..\apps\api
echo    python railway_indexer.py 100000
echo.
echo 3. Update frontend PropertySearch.tsx with Search API URL
echo.
echo 4. Run Playwright tests to verify
echo.
echo See DEPLOYMENT_READY_SUMMARY.md for detailed next steps.
echo.
echo ================================================================================
echo.
pause
