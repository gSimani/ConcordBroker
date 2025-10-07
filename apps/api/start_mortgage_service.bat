@echo off
echo ================================================================
echo  MORTGAGE ANALYTICS SERVICE LAUNCHER
echo  FRED PMMS Integration + Loan Calculations
echo ================================================================
echo.

:: Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

:: Check for required environment variables
if not defined FRED_API_KEY (
    echo WARNING: FRED_API_KEY not set. Rate fetching will use fallback data.
    echo Get your free API key at: https://fred.stlouisfed.org/docs/api/api_key.html
)

if not defined SUPABASE_URL (
    echo WARNING: SUPABASE_URL not set. Database features will be disabled.
)

:: Install dependencies
echo [1/4] Installing required packages...
pip install -q -r requirements-mortgage.txt 2>nul || (
    echo Installing core dependencies individually...
    pip install -q supabase pandas numpy requests pydantic python-dateutil
    pip install -q apscheduler fredapi pyarrow fastapi uvicorn openpyxl
)

:: Run tests
echo [2/4] Running validation tests...
python tests/test_mortgage_analytics.py
if %errorlevel% neq 0 (
    echo WARNING: Some tests failed. Review output above.
    pause
)

:: Start service
echo [3/4] Starting Mortgage Analytics Service on port 8005...
echo.
echo ================================================================
echo  SERVICE ENDPOINTS:
echo ================================================================
echo  Health Check:     http://localhost:8005/health
echo  API Docs:         http://localhost:8005/docs
echo
echo  Main Endpoints:
echo  - GET  /mortgage/{property_id}/payoff
echo  - GET  /mortgage/{property_id}/current-payment
echo  - POST /rates/refresh
echo.
echo  Features:
echo  - Automatic FRED PMMS rate updates (nightly at 2 AM ET)
echo  - Historical loan payoff progress tracking
echo  - Current market rate debt service calculations
echo  - Extra principal payment support
echo  - DSCR calculations with NOI input
echo ================================================================
echo.

:: Launch the service
echo [4/4] Launching service...
start "Mortgage Analytics API" cmd /k "python mortgage_analytics_service.py"

:: Open browser
timeout /t 3 /nobreak >nul
start "" "http://localhost:8005/docs"

echo.
echo Service started successfully!
echo Press any key to exit this launcher...
pause >nul