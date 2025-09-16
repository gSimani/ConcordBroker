@echo off
REM ===================================================
REM Claude Code Session Auto-Starter for Windows
REM Automatically initializes MCP Server and services
REM ===================================================

echo.
echo ========================================
echo  ConcordBroker Claude Code Initializer
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Navigate to project directory
cd /d "%~dp0"

REM Check if .env.mcp exists
if not exist ".env.mcp" (
    echo WARNING: .env.mcp file not found
    echo Creating from template...
    if exist ".env.mcp.example" (
        copy ".env.mcp.example" ".env.mcp"
        echo Please edit .env.mcp with your API credentials
        notepad ".env.mcp"
    ) else (
        echo ERROR: No .env.mcp or .env.mcp.example found
        echo Please create .env.mcp with your credentials
        pause
        exit /b 1
    )
)

REM Install dependencies if needed
if not exist "mcp-server\node_modules" (
    echo Installing MCP Server dependencies...
    cd mcp-server
    call npm install
    cd ..
)

REM Kill any existing MCP server on port 3001
echo Checking for existing MCP Server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do (
    echo Stopping existing server process %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Start the Claude Code initializer
echo Starting MCP Server...
start /B node claude-code-init.cjs

REM Wait for server to be ready
echo Waiting for server to initialize...
timeout /t 5 /nobreak >nul

REM Check server health
echo.
echo Checking service connections...
curl -s http://localhost:3001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ===================================
    echo  MCP Server Started Successfully!
    echo ===================================
    echo.
    echo Services available at: http://localhost:3001
    echo API Documentation: http://localhost:3001/docs
    echo Health Status: http://localhost:3001/health
    echo.
    echo All services are connected and ready for Claude Code.
) else (
    echo.
    echo WARNING: MCP Server may not be fully initialized
    echo Check logs at: mcp-server\claude-init.log
)

REM Keep window open for monitoring
echo.
echo Press any key to continue...
pause >nul