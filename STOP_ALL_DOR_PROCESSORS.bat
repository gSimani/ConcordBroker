@echo off
echo ========================================
echo STOPPING ALL DOR PROCESSORS
echo ========================================
echo.
echo Killing all Node.js processes...
taskkill /F /IM node.exe 2>nul
echo.
echo Killing all Python processes...
taskkill /F /IM python.exe 2>nul
echo.
echo ========================================
echo ALL PROCESSORS STOPPED
echo ========================================
echo.
echo You can now:
echo 1. Check the dashboard at http://localhost:8080
echo 2. Run a fresh single-county processor
echo.
pause
