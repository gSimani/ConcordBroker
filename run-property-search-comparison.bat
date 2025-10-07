@echo off
echo Starting PropertySearch Module Comparison...
echo.
echo This script will:
echo 1. Compare local (localhost:5173) vs production (concordbroker.com)
echo 2. Take screenshots of both /properties pages
echo 3. Check for PropertySearch component functionality
echo 4. Generate comparison report
echo.
pause

echo Installing required dependencies...
npm install playwright

echo.
echo Running comparison script...
node compare-property-search.cjs

echo.
echo Comparison complete! Check the property-search-comparison folder for results.
pause