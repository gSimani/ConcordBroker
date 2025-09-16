@echo off
echo ================================================================
echo  ConcordBroker Data Verification System Setup
echo ================================================================
echo.

:: Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

echo [1/5] Installing Python dependencies...
echo ----------------------------------------------------------------
pip install -r requirements-data-verification.txt

echo.
echo [2/5] Installing Playwright browsers...
echo ----------------------------------------------------------------
playwright install chromium

echo.
echo [3/5] Checking environment configuration...
echo ----------------------------------------------------------------
if not exist .env.mcp (
    echo WARNING: .env.mcp file not found
    echo Please ensure you have the following environment variables:
    echo   - SUPABASE_URL
    echo   - SUPABASE_SERVICE_ROLE_KEY
    echo   - MCP_API_KEY
    echo.
    echo Create .env.mcp file with these variables before running verification.
    pause
)

echo.
echo [4/5] Creating verification directories...
echo ----------------------------------------------------------------
if not exist verification_results mkdir verification_results
if not exist data_mapping_visualizations mkdir data_mapping_visualizations
if not exist visual_verification_screenshots mkdir visual_verification_screenshots

echo.
echo [5/5] Running quick verification test...
echo ----------------------------------------------------------------
echo Running data mapping analysis only (quick mode)...
python run_data_verification.py --quick

echo.
echo ================================================================
echo  Setup Complete!
echo ================================================================
echo.
echo Available commands:
echo   python run_data_verification.py              # Full verification
echo   python run_data_verification.py --quick      # Data mapping only
echo   python run_data_verification.py --skip-visual  # Skip visual tests
echo.
echo Results will be saved to 'verification_results' directory
echo.
pause