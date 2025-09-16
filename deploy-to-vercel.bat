@echo off
REM Vercel Deployment Script for ConcordBroker (Batch Version)
REM Deploys the web application to Vercel production

echo ========================================
echo    Deploying ConcordBroker to Vercel
echo    Project: concord-broker
echo    Domain: https://www.concordbroker.com
echo ========================================
echo.

REM Check if Vercel CLI is installed
vercel --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Vercel CLI not found. Installing...
    echo Installing Vercel CLI globally...
    call npm install -g vercel
    if %errorlevel% neq 0 (
        echo Failed to install Vercel CLI
        pause
        exit /b 1
    )
)

echo Vercel CLI is installed
echo.

REM Set Vercel token for authentication
set VERCEL_TOKEN=t9AK4qQ51TyAc0K0ZLk7tN0H

REM Configure project
echo Configuring Vercel project...
echo Team: westbocaexecs-projects
echo Project ID: prj_l6jgk7483iwPCcaYarq7sMgt2m7L
echo.

REM Build the web application
echo Building web application...
cd apps\web
call npm install
if %errorlevel% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

call npm run build
if %errorlevel% neq 0 (
    echo Failed to build application
    pause
    exit /b 1
)

cd ..\..

REM Deploy to Vercel
echo.
echo Deploying to Vercel...
echo This will deploy to production at https://www.concordbroker.com
echo.

REM Deploy with production flag
vercel --prod --token t9AK4qQ51TyAc0K0ZLk7tN0H --scope westbocaexecs-projects --yes

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    Deployment Complete!
    echo ========================================
    echo.
    echo Your application has been deployed to:
    echo   Production: https://www.concordbroker.com
    echo   Dashboard: https://vercel.com/westbocaexecs-projects/concord-broker
    echo.
    echo API Backend ^(Railway^): https://concordbroker.up.railway.app
) else (
    echo.
    echo Deployment failed. Please check the error messages above.
)

echo.
pause