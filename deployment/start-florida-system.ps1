# Florida Data System Startup Script
# PowerShell script to start the comprehensive Florida data monitoring system

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("single", "daemon", "dashboard", "health")]
    [string]$Mode = "single",
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "florida_config.json",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("DEBUG", "INFO", "WARNING", "ERROR")]
    [string]$LogLevel = "INFO",
    
    [Parameter(Mandatory=$false)]
    [switch]$InstallDependencies,
    
    [Parameter(Mandatory=$false)]
    [switch]$SetupDatabase,
    
    [Parameter(Mandatory=$false)]
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=" * 60 -ForegroundColor Green
Write-Host "Florida Property Data Comprehensive System" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Function to check if Python is installed
function Test-Python {
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Python not found. Please install Python 3.9 or higher." -ForegroundColor Red
        return $false
    }
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    
    $requirementsFile = Join-Path $ProjectRoot "requirements-florida-comprehensive.txt"
    
    if (-not (Test-Path $requirementsFile)) {
        Write-Host "✗ Requirements file not found: $requirementsFile" -ForegroundColor Red
        exit 1
    }
    
    try {
        python -m pip install --upgrade pip
        python -m pip install -r $requirementsFile
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Failed to install dependencies: $_" -ForegroundColor Red
        exit 1
    }
}

# Function to check environment variables
function Test-Environment {
    Write-Host "Checking environment configuration..." -ForegroundColor Yellow
    
    $requiredVars = @(
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY"
    )
    
    $missing = @()
    foreach ($var in $requiredVars) {
        if (-not (Get-Item "Env:$var" -ErrorAction SilentlyContinue)) {
            $missing += $var
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "✗ Missing required environment variables:" -ForegroundColor Red
        foreach ($var in $missing) {
            Write-Host "  - $var" -ForegroundColor Red
        }
        Write-Host "Please check your .env file or set these variables." -ForegroundColor Red
        return $false
    }
    
    Write-Host "✓ Environment variables configured" -ForegroundColor Green
    return $true
}

# Function to setup database
function Setup-Database {
    Write-Host "Setting up database schema..." -ForegroundColor Yellow
    
    $workersPath = Join-Path $ProjectRoot "apps\workers"
    
    try {
        Push-Location $workersPath
        python -c @"
import asyncio
import sys
sys.path.insert(0, '.')
from florida_comprehensive_monitor import FloridaComprehensiveMonitor

async def setup():
    try:
        async with FloridaComprehensiveMonitor() as monitor:
            print('✓ Database schemas initialized successfully')
        return True
    except Exception as e:
        print(f'✗ Database setup failed: {e}')
        return False

result = asyncio.run(setup())
sys.exit(0 if result else 1)
"@
        Pop-Location
        Write-Host "✓ Database setup completed" -ForegroundColor Green
    }
    catch {
        Pop-Location
        Write-Host "✗ Database setup failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Function to run system tests
function Run-Tests {
    Write-Host "Running system tests..." -ForegroundColor Yellow
    
    $workersPath = Join-Path $ProjectRoot "apps\workers"
    
    $testModules = @(
        "florida_url_resolver.py",
        "florida_data_processor.py",
        "florida_error_handler.py"
    )
    
    try {
        Push-Location $workersPath
        
        foreach ($module in $testModules) {
            Write-Host "Testing $module..." -ForegroundColor Cyan
            python $module
        }
        
        Pop-Location
        Write-Host "✓ All tests passed" -ForegroundColor Green
    }
    catch {
        Pop-Location
        Write-Host "✗ Tests failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Function to start the system
function Start-System {
    param($Mode, $ConfigPath, $LogLevel)
    
    $workersPath = Join-Path $ProjectRoot "apps\workers"
    $orchestratorScript = Join-Path $workersPath "florida_master_orchestrator.py"
    
    if (-not (Test-Path $orchestratorScript)) {
        Write-Host "✗ Orchestrator script not found: $orchestratorScript" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Starting Florida Data System in $Mode mode..." -ForegroundColor Yellow
    Write-Host "Log Level: $LogLevel" -ForegroundColor Gray
    
    if (Test-Path $ConfigPath) {
        Write-Host "Using config: $ConfigPath" -ForegroundColor Gray
    }
    
    try {
        Push-Location $workersPath
        
        $args = @("florida_master_orchestrator.py", "--mode", $Mode, "--log-level", $LogLevel)
        
        if (Test-Path $ConfigPath) {
            $args += @("--config", $ConfigPath)
        }
        
        Write-Host "Command: python $($args -join ' ')" -ForegroundColor Gray
        Write-Host ""
        
        python @args
    }
    catch {
        Write-Host "✗ System startup failed: $_" -ForegroundColor Red
        exit 1
    }
    finally {
        Pop-Location
    }
}

# Main execution flow
try {
    # Change to project root
    Set-Location $ProjectRoot
    
    # Basic checks
    if (-not (Test-Python)) {
        exit 1
    }
    
    # Install dependencies if requested
    if ($InstallDependencies) {
        Install-Dependencies
    }
    
    # Check environment
    if (-not (Test-Environment)) {
        exit 1
    }
    
    # Setup database if requested
    if ($SetupDatabase) {
        Setup-Database
    }
    
    # Run tests if requested
    if ($RunTests) {
        Run-Tests
    }
    
    # Display system information
    Write-Host ""
    Write-Host "System Information:" -ForegroundColor Cyan
    Write-Host "  Project Root: $ProjectRoot" -ForegroundColor Gray
    Write-Host "  Python Version: $(python --version)" -ForegroundColor Gray
    Write-Host "  Mode: $Mode" -ForegroundColor Gray
    Write-Host "  Log Level: $LogLevel" -ForegroundColor Gray
    Write-Host ""
    
    # Start the system
    Start-System -Mode $Mode -ConfigPath $ConfigPath -LogLevel $LogLevel
}
catch {
    Write-Host "✗ Startup failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Florida Data System startup completed." -ForegroundColor Green