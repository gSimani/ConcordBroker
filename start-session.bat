@echo off
echo ================================================================
echo  ConcordBroker Development Session Startup
echo  Auto-starts MCP Server + All Connected Services
echo ================================================================
echo.

:: Set window title
title ConcordBroker Development Session

:: Check if Node.js is available
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js first.
    pause
    exit /b 1
)

:: Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

echo [1/5] Starting MCP Server (Port 3005)...
echo ----------------------------------------------------------------
start "MCP Server" cmd /k "cd mcp-server && npm start"
timeout /t 3 /nobreak >nul

echo [2/5] Starting React Frontend (Port 5191)...
echo ----------------------------------------------------------------
start "React Frontend" cmd /k "cd apps/web && npm run dev"
timeout /t 2 /nobreak >nul

echo [3/5] Starting Property API (Port 8000)...
echo ----------------------------------------------------------------
start "Property API" cmd /k "cd apps/api && python property_live_api.py"
timeout /t 2 /nobreak >nul

echo [4/5] Initializing MCP Services (ULTIMATE)...
echo ----------------------------------------------------------------
start "MCP Init" cmd /k "node claude-code-ultimate-init.cjs"
timeout /t 3 /nobreak >nul

echo [5/5] Opening Services in Browser...
echo ----------------------------------------------------------------
timeout /t 5 /nobreak >nul

:: Open application in default browser
start "" "http://localhost:5191"
timeout /t 1 /nobreak >nul
start "" "http://localhost:3005/health"
timeout /t 1 /nobreak >nul
start "" "http://localhost:8000/docs"

echo.
echo ================================================================
echo  ConcordBroker Development Session Started Successfully!
echo ================================================================
echo.
echo  Services Running:
echo   - Frontend:     http://localhost:5191
echo   - MCP Server:   http://localhost:3005
echo   - Property API: http://localhost:8000
echo   - API Docs:     http://localhost:8000/docs
echo.
echo  Connected Services:
echo   - Vercel (Frontend Deployment)
echo   - Railway (Backend Deployment)
echo   - Supabase (Database)
echo   - GitHub (Version Control)
echo   - HuggingFace (AI Models)
echo   - OpenAI (GPT-4)
echo   - LangChain (Agent Orchestration)
echo.
echo  Press any key to open service status dashboard...
pause >nul

:: Open MCP service status
start "" "http://localhost:3005/health"

echo.
echo Session started! Close this window when you're done.
echo To stop all services, close the individual terminal windows.
pause