@echo off
REM Railway Deployment Script for ConcordBroker (Batch Version)
REM Deploys the application to Railway production environment

echo ========================================
echo    Deploying ConcordBroker to Railway
echo    Project ID: 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
echo ========================================
echo.

REM Check if Railway CLI is installed
railway version >nul 2>&1
if %errorlevel% neq 0 (
    echo Railway CLI not found. Installing...
    echo Please install Railway CLI from: https://docs.railway.app/develop/cli
    echo Run: npm install -g @railway/cli
    pause
    exit /b 1
)

echo Railway CLI is installed
echo.

REM Login to Railway
echo Logging into Railway...
railway login

REM Link to project
echo Linking to Railway project...
railway link 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb

REM Set environment
echo Setting environment to production...
railway environment concordbrokerproduction

echo.
echo Starting deployment...
echo This will deploy both API and Web services
echo.

REM Deploy the application
railway up

echo.
echo ========================================
echo    Deployment Complete!
echo ========================================
echo.
echo Your application is being deployed to:
echo   Public URL: https://concordbroker.up.railway.app
echo   Internal: concordbroker.railway.internal
echo.
echo Check deployment status at:
echo   https://railway.app/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
echo.
pause