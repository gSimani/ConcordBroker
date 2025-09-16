# Tax Deed Real-Time Monitoring System Startup Script
# Starts the comprehensive monitoring system for tax deed auctions

param(
    [switch]$TestOnly,
    [switch]$Deploy,
    [switch]$Verbose
)

Write-Host "=" -ForegroundColor Cyan
Write-Host "🏛️  TAX DEED REAL-TIME MONITORING SYSTEM" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Purpose: Monitor tax deed auctions for real-time changes" -ForegroundColor Green
Write-Host "🚨 Critical: Tracks cancellations, postponements, bid changes" -ForegroundColor Red  
Write-Host "📊 Features: Real-time alerts, performance monitoring, daily reports" -ForegroundColor Blue
Write-Host ""

# Check if Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ Python not found. Please install Python 3.8+ and try again." -ForegroundColor Red
    exit 1
}

# Check Python version
$pythonVersion = & python --version 2>&1
Write-Host "🐍 Using: $pythonVersion" -ForegroundColor Green

# Check if virtual environment exists
$venvPath = "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
$activateScript = if ($IsWindows -or $env:OS -eq "Windows_NT") { 
    "$venvPath\Scripts\Activate.ps1" 
} else { 
    "$venvPath/bin/activate" 
}

if (Test-Path $activateScript) {
    Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
    
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        & $activateScript
    } else {
        . $activateScript
    }
} else {
    Write-Host "⚠️  Virtual environment activation script not found, continuing without..." -ForegroundColor Yellow
}

# Install required packages
Write-Host "📚 Installing required packages..." -ForegroundColor Yellow
$packages = @(
    "asyncio",
    "aiohttp", 
    "beautifulsoup4",
    "supabase",
    "schedule",
    "rich",
    "pydantic",
    "tenacity",
    "psutil",
    "pytz"
)

foreach ($package in $packages) {
    Write-Host "   Installing $package..." -ForegroundColor Gray
    pip install $package --quiet
}

# Check environment variables
Write-Host ""
Write-Host "🔧 Checking environment configuration..." -ForegroundColor Yellow

$requiredEnvVars = @(
    "VITE_SUPABASE_URL",
    "VITE_SUPABASE_ANON_KEY"
)

$missingVars = @()
foreach ($var in $requiredEnvVars) {
    if (-not [Environment]::GetEnvironmentVariable($var)) {
        $missingVars += $var
    } else {
        Write-Host "   ✅ $var is set" -ForegroundColor Green
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing required environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "💡 Please set these in your .env file or system environment" -ForegroundColor Yellow
    exit 1
}

# Deploy database schema if requested
if ($Deploy) {
    Write-Host ""
    Write-Host "🗄️  Deploying database schema..." -ForegroundColor Yellow
    
    # Check if schema file exists
    if (-not (Test-Path "tax_deed_changes_schema.sql")) {
        Write-Host "❌ Schema file not found: tax_deed_changes_schema.sql" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "   Schema deployment will be handled by the Python script..." -ForegroundColor Gray
}

# Test mode
if ($TestOnly) {
    Write-Host ""
    Write-Host "🧪 Running in TEST MODE only..." -ForegroundColor Yellow
    Write-Host "   This will test the monitoring system without starting full monitoring" -ForegroundColor Gray
    Write-Host ""
    
    python start_tax_deed_monitoring.py --test
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Test completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Test failed!" -ForegroundColor Red
        exit 1
    }
    
    exit 0
}

# Start the monitoring system
Write-Host ""
Write-Host "🚀 Starting Tax Deed Real-Time Monitoring System..." -ForegroundColor Green
Write-Host ""
Write-Host "📋 System will monitor:" -ForegroundColor Blue
Write-Host "   • Broward County auctions every 30 seconds" -ForegroundColor Gray
Write-Host "   • Deep content scans every 5 minutes" -ForegroundColor Gray  
Write-Host "   • Full data scans daily at 2 AM" -ForegroundColor Gray
Write-Host "   • Send alerts for critical changes" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

# Set verbose logging if requested
if ($Verbose) {
    $env:PYTHONPATH = $pwd.Path
    $env:LOGGING_LEVEL = "DEBUG"
} else {
    $env:LOGGING_LEVEL = "INFO"
}

# Run the monitoring system
try {
    python start_tax_deed_monitoring.py
} catch {
    Write-Host ""
    Write-Host "❌ Monitoring system encountered an error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "👋 Tax Deed Monitoring System has stopped." -ForegroundColor Yellow
Write-Host "✅ Thank you for using the monitoring system!" -ForegroundColor Green