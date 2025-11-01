@echo off
REM Railway Orchestrator Quick Deploy Script (Windows)
REM Run this after `railway login` and `railway link`

echo 🚂 Railway Orchestrator Deployment
echo ====================================
echo.

REM Check if logged in
railway whoami >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Not logged in to Railway
    echo Please run: railway login
    exit /b 1
)

echo ✅ Railway CLI authenticated
echo.

REM Set environment variables
echo 📝 Setting environment variables...
railway variables --set SUPABASE_HOST=aws-1-us-east-1.pooler.supabase.com
railway variables --set SUPABASE_DB=postgres
railway variables --set SUPABASE_USER=postgres.pmispwtdngkcmsrsjwbp
railway variables --set SUPABASE_PASSWORD="West@Boca613!"
railway variables --set SUPABASE_PORT=5432
railway variables --set DB_POOL_MIN=5
railway variables --set DB_POOL_MAX=20
railway variables --set PYTHONUNBUFFERED=1

echo ✅ Environment variables set
echo.

REM Deploy
echo 🚀 Deploying orchestrator...
railway up

echo.
echo ====================================
echo Deployment complete!
echo.
echo Next steps:
echo 1. Check status: railway status
echo 2. View logs: railway logs
echo 3. Monitor: railway logs --follow
echo.

pause
