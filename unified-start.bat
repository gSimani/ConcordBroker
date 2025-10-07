@echo off
echo ========================================
echo    ConcordBroker Unified Startup
echo    Starting all services...
echo ========================================
echo.

:: Kill any existing Node processes on our ports
echo [1/6] Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3005') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8003') do taskkill /F /PID %%a 2>nul

timeout /t 2 /nobreak > nul

:: Start MCP Server
echo [2/6] Starting MCP Server on port 3005...
start "MCP Server" /min cmd /c "cd mcp-server && npm start"
timeout /t 3 /nobreak > nul

:: Start Backend API
echo [3/6] Starting Backend API on port 8000...
start "Backend API" /min cmd /c "cd apps/api && npm run dev"
timeout /t 3 /nobreak > nul

:: Start Frontend
echo [4/6] Starting Frontend on port 5173...
start "Frontend" /min cmd /c "cd apps/web && npm run dev"
timeout /t 3 /nobreak > nul

:: Start LangChain API (if exists)
echo [5/6] Checking for LangChain API...
if exist "langchain-api" (
    start "LangChain API" /min cmd /c "cd langchain-api && npm start"
    timeout /t 3 /nobreak > nul
)

echo.
echo ========================================
echo    All services started!
echo ========================================
echo.
echo Services running on:
echo   - Frontend:      http://localhost:5173
echo   - Backend API:   http://localhost:8000
echo   - MCP Server:    http://localhost:3005
echo   - LangChain:     http://localhost:8003
echo.
echo Health checks:
echo   - API Health:    http://localhost:8000/health
echo   - MCP Health:    http://localhost:3005/health
echo.
echo Press any key to open the application...
pause > nul

:: Open the application in browser
start http://localhost:5173

echo.
echo To stop all services, close this window or press Ctrl+C
pause