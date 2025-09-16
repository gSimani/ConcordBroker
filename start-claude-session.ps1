#!/usr/bin/env pwsh
# ===================================================
# Claude Code Session Auto-Starter for PowerShell
# Automatically initializes MCP Server and services
# ===================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ConcordBroker Claude Code Initializer " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Navigate to script directory
Set-Location $PSScriptRoot

# Check if .env.mcp exists
if (-not (Test-Path ".env.mcp")) {
    Write-Host "WARNING: .env.mcp file not found" -ForegroundColor Yellow
    Write-Host "Creating from template..." -ForegroundColor Yellow
    
    if (Test-Path ".env.mcp.example") {
        Copy-Item ".env.mcp.example" ".env.mcp"
        Write-Host "Please edit .env.mcp with your API credentials" -ForegroundColor Yellow
        Start-Process notepad ".env.mcp" -Wait
    } else {
        Write-Host "ERROR: No .env.mcp or .env.mcp.example found" -ForegroundColor Red
        Write-Host "Please create .env.mcp with your credentials" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Install dependencies if needed
if (-not (Test-Path "mcp-server\node_modules")) {
    Write-Host "Installing MCP Server dependencies..." -ForegroundColor Yellow
    Set-Location mcp-server
    npm install
    Set-Location ..
}

# Kill any existing MCP server on port 3001
Write-Host "Checking for existing MCP Server..." -ForegroundColor Yellow
$existingProcess = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($existingProcess) {
    Write-Host "Stopping existing server process $existingProcess" -ForegroundColor Yellow
    Stop-Process -Id $existingProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# Start the Claude Code initializer
Write-Host "Starting MCP Server..." -ForegroundColor Green
$mcpProcess = Start-Process -FilePath "node" -ArgumentList "claude-code-init.cjs" -PassThru -NoNewWindow

# Wait for server to be ready
Write-Host "Waiting for server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check server health
Write-Host ""
Write-Host "Checking service connections..." -ForegroundColor Yellow

try {
    $health = Invoke-RestMethod -Uri "http://localhost:3001/health" -Method Get -ErrorAction Stop
    
    Write-Host ""
    Write-Host "===================================" -ForegroundColor Green
    Write-Host " MCP Server Started Successfully! " -ForegroundColor Green
    Write-Host "===================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Services available at: " -NoNewline
    Write-Host "http://localhost:3001" -ForegroundColor Cyan
    Write-Host "API Documentation: " -NoNewline
    Write-Host "http://localhost:3001/docs" -ForegroundColor Cyan
    Write-Host "Health Status: " -NoNewline
    Write-Host "http://localhost:3001/health" -ForegroundColor Cyan
    Write-Host ""
    
    # Display service status
    if ($health.services) {
        Write-Host "Service Status:" -ForegroundColor Yellow
        $health.services.PSObject.Properties | ForEach-Object {
            $serviceName = $_.Name
            $serviceStatus = $_.Value.status
            $statusColor = if ($serviceStatus -eq "healthy" -or $serviceStatus -eq "configured") { "Green" } else { "Yellow" }
            Write-Host "  ✓ $serviceName`: " -NoNewline
            Write-Host $serviceStatus -ForegroundColor $statusColor
        }
    }
    
    Write-Host ""
    Write-Host "All services are connected and ready for Claude Code." -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "WARNING: MCP Server may not be fully initialized" -ForegroundColor Yellow
    Write-Host "Check logs at: mcp-server\claude-init.log" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
}

# Monitor server (optional)
Write-Host ""
Write-Host "MCP Server is running in the background." -ForegroundColor Cyan
Write-Host "To stop the server, close this window or press Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Keep the script running to monitor the server
if ($mcpProcess -and -not $mcpProcess.HasExited) {
    Write-Host "Monitoring MCP Server (PID: $($mcpProcess.Id))..." -ForegroundColor Gray
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
    
    try {
        # Wait for the process to exit or user interrupt
        $mcpProcess.WaitForExit()
    } catch {
        # User pressed Ctrl+C
        Write-Host ""
        Write-Host "Stopping MCP Server..." -ForegroundColor Yellow
        Stop-Process -Id $mcpProcess.Id -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "Press Enter to exit..." -ForegroundColor Gray
    Read-Host
}