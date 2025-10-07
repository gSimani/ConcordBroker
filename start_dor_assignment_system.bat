@echo off
echo ============================================================
echo DOR Use Code Assignment System - Quick Start
echo ============================================================
echo.

echo [1/3] Starting FastAPI Service on port 8002...
start "DOR FastAPI Service" cmd /k "cd mcp-server\fastapi-endpoints && python dor_use_code_api.py"
timeout /t 5 /nobreak >nul

echo [2/3] Opening Jupyter Notebook for analysis...
start "DOR Analysis Notebook" cmd /k "jupyter notebook mcp-server\notebooks\dor_use_code_analysis.ipynb"
timeout /t 3 /nobreak >nul

echo [3/3] System Ready!
echo.
echo ============================================================
echo Services Running:
echo   - FastAPI: http://localhost:8002
echo   - API Docs: http://localhost:8002/docs
echo   - Jupyter: http://localhost:8888
echo ============================================================
echo.
echo Quick Commands:
echo   - Check Status: curl http://localhost:8002/assignment-status
echo   - Bulk Assign: curl -X POST http://localhost:8002/assign-bulk
echo   - View Analytics: curl http://localhost:8002/analytics/distribution
echo.
echo Documentation: DOR_USE_CODE_ASSIGNMENT_COMPLETE_SYSTEM.md
echo ============================================================
pause