@echo off
echo ================================================================
echo  ConcordBroker Railway Deployment Fix
echo ================================================================
echo.
echo This script will help fix Railway deployment issues
echo.

:: Load environment variables
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in ('findstr "RAILWAY_" .env') do (
        set "%%a=%%b"
    )
    echo Loaded Railway configuration from .env
) else (
    echo WARNING: .env file not found
    echo Please ensure you have Railway credentials in .env
    pause
    exit /b 1
)

:: Check if Railway CLI is installed
where railway >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo Railway CLI not found. Installing...
    powershell -Command "iwr https://railway.app/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo Failed to install Railway CLI
        echo Please install manually from: https://railway.app/cli
        pause
        exit /b 1
    )
)

echo.
echo ================================================================
echo  Step 1: Checking Required Files
echo ================================================================

:: Check for required files
if not exist "railway.json" (
    echo ERROR: railway.json not found
    echo Creating railway.json...

    echo {>railway.json
    echo   "$schema": "https://railway.app/railway.schema.json",>>railway.json
    echo   "build": {>>railway.json
    echo     "builder": "NIXPACKS">>railway.json
    echo   },>>railway.json
    echo   "deploy": {>>railway.json
    echo     "numReplicas": 1,>>railway.json
    echo     "startCommand": "cd apps/api && python -m uvicorn ultimate_autocomplete_api:app --host 0.0.0.0 --port $PORT",>>railway.json
    echo     "restartPolicyType": "ON_FAILURE",>>railway.json
    echo     "restartPolicyMaxRetries": 10,>>railway.json
    echo     "healthcheckPath": "/health",>>railway.json
    echo     "healthcheckTimeout": 30>>railway.json
    echo   }>>railway.json
    echo }>>railway.json

    echo Created railway.json
)

if not exist "nixpacks.toml" (
    echo ERROR: nixpacks.toml not found
    echo Please run: git pull origin main
    pause
    exit /b 1
)

if not exist "apps\api\requirements.txt" (
    echo ERROR: apps\api\requirements.txt not found
    pause
    exit /b 1
)

echo All required files present!

echo.
echo ================================================================
echo  Step 2: Authenticating with Railway
echo ================================================================

if defined RAILWAY_API_TOKEN (
    echo Logging into Railway...
    railway login --token %RAILWAY_API_TOKEN%
    if %errorlevel% neq 0 (
        echo Failed to authenticate with Railway
        echo Please check your RAILWAY_API_TOKEN in .env
        pause
        exit /b 1
    )
    echo Successfully authenticated!
) else (
    echo ERROR: RAILWAY_API_TOKEN not found in environment
    echo Please add it to your .env file
    pause
    exit /b 1
)

echo.
echo ================================================================
echo  Step 3: Manual Configuration Required
echo ================================================================
echo.
echo Please complete these steps in your Railway dashboard:
echo.
echo 1. Go to: https://railway.app/project/%RAILWAY_PROJECT_ID%
echo.
echo 2. Click on your service (or create one if it doesn't exist)
echo.
echo 3. Go to the "Variables" tab and add these environment variables:
echo    - SUPABASE_URL = (your supabase url)
echo    - SUPABASE_ANON_KEY = (your supabase anon key)
echo    - SUPABASE_SERVICE_ROLE_KEY = (your supabase service role key)
echo    - PORT = 8000
echo    - PYTHON_VERSION = 3.10
echo.
echo 4. Go to the "Settings" tab and verify:
echo    - Build Command: (leave empty - Nixpacks will handle it)
echo    - Start Command: (leave empty - will use railway.json)
echo    - Health Check Path: /health
echo    - Region: us-east4 (or your preferred)
echo.
echo 5. Go to the "Deployments" tab
echo.
echo 6. Click "Deploy from GitHub" if not connected
echo    - Repository: gSimani/ConcordBroker
echo    - Branch: main
echo.
echo Press any key when you've completed these steps...
pause >nul

echo.
echo ================================================================
echo  Step 4: Deploying to Railway
echo ================================================================
echo.
echo Triggering deployment...

railway up --project %RAILWAY_PROJECT_ID%

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo  Deployment Initiated!
    echo ================================================================
    echo.
    echo Check the deployment status at:
    echo https://railway.app/project/%RAILWAY_PROJECT_ID%
    echo.
    echo The build should:
    echo 1. Detect Python app via Nixpacks
    echo 2. Install requirements.txt
    echo 3. Start the FastAPI server
    echo 4. Pass health checks
    echo.
    echo If it fails, check:
    echo - Build logs for missing dependencies
    echo - Environment variables are set correctly
    echo - GitHub repository is connected
    echo.
) else (
    echo.
    echo ================================================================
    echo  Deployment Failed
    echo ================================================================
    echo.
    echo Please check:
    echo 1. Railway dashboard for error messages
    echo 2. Your API token has correct permissions
    echo 3. Project ID is correct
    echo.
)

echo Press any key to exit...
pause >nul