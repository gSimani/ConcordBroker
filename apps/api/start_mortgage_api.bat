@echo off
echo ================================================================
echo  MORTGAGE ANALYTICS API - PRODUCTION READY
echo  Fast, Reliable Mortgage Calculations
echo ================================================================
echo.

:: Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

:: Install dependencies
echo [1/4] Installing required packages...
pip install -q fastapi uvicorn pydantic python-multipart

:: Test the API with a quick calculation
echo [2/4] Running API test...
python -c "
from mortgage_analytics_api import MortgageCalculator
result = MortgageCalculator.calculate_mortgage_details(400000, 6.5, 30)
print('[OK] API Test Result:')
print('  Monthly Payment: ${:,.2f}'.format(result['monthly_payment']))
print('  Total Interest: ${:,.2f}'.format(result['total_interest']))
"

if %errorlevel% neq 0 (
    echo WARNING: API test failed. Check dependencies.
    pause
)

:: Start the API server
echo [3/4] Starting Mortgage Analytics API on port 8005...
echo.
echo ================================================================
echo  API ENDPOINTS AVAILABLE:
echo ================================================================
echo  Health Check:     http://localhost:8005/health
echo  API Documentation: http://localhost:8005/docs
echo  Interactive API:   http://localhost:8005/redoc
echo.
echo  MAIN ENDPOINTS:
echo  - POST /mortgage/calculate           - Comprehensive mortgage calculation
echo  - POST /mortgage/payoff-progress     - Loan payoff progress tracking
echo  - POST /mortgage/refinance-analysis  - Refinance analysis & breakeven
echo  - POST /mortgage/affordability       - Home affordability calculator
echo  - GET  /mortgage/quick-payment       - Quick payment calculation
echo  - GET  /mortgage/rate-comparison     - Compare rates side-by-side
echo  - GET  /mortgage/amortization-schedule - Payment schedule generation
echo.
echo  FEATURES:
echo  - Ultra-fast calculations (no database dependency)
echo  - Comprehensive mortgage analytics
echo  - Professional-grade accuracy
echo  - RESTful API with full documentation
echo  - CORS enabled for web integration
echo ================================================================
echo.

:: Launch the API server
echo [4/4] Launching Mortgage Analytics API...
start "Mortgage Analytics API" cmd /k "python mortgage_analytics_api.py"

:: Open browser to API docs
timeout /t 3 /nobreak >nul
start "" "http://localhost:8005/docs"

echo.
echo ================================================================
echo  MORTGAGE ANALYTICS API STARTED SUCCESSFULLY!
echo ================================================================
echo.
echo  Quick Test Commands:
echo.
echo  # Calculate $400,000 loan at 6.5% for 30 years
echo  curl "http://localhost:8005/mortgage/quick-payment?amount=400000&rate=6.5&years=30"
echo.
echo  # Health check
echo  curl "http://localhost:8005/health"
echo.
echo  # View full documentation
echo  curl "http://localhost:8005/docs"
echo.
echo ================================================================
echo.
echo API is running! Press any key to continue...
pause >nul