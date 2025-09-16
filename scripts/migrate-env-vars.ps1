# PowerShell script to migrate environment variables to Vercel and Railway
# This script helps you securely move credentials from .env files to cloud platforms

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Environment Variable Migration" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Vercel CLI is installed
$vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue
if (-not $vercelInstalled) {
    Write-Host "❌ Vercel CLI not installed. Install it with: npm i -g vercel" -ForegroundColor Red
    Write-Host "   Then run: vercel login" -ForegroundColor Yellow
    exit 1
}

# Check if Railway CLI is installed
$railwayInstalled = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railwayInstalled) {
    Write-Host "⚠️  Railway CLI not installed. Install from: https://docs.railway.app/develop/cli" -ForegroundColor Yellow
    Write-Host "   Continuing without Railway..." -ForegroundColor Yellow
}

# Function to add environment variable to Vercel
function Add-VercelEnv {
    param(
        [string]$key,
        [string]$value,
        [string]$environment = "production preview development"
    )
    
    try {
        $environments = $environment -split " "
        foreach ($env in $environments) {
            vercel env add $key $env --force 2>$null
            if ($?) {
                Write-Host "✅ Added $key to Vercel ($env)" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "❌ Failed to add $key to Vercel" -ForegroundColor Red
    }
}

# Function to add environment variable to Railway
function Add-RailwayEnv {
    param(
        [string]$key,
        [string]$value
    )
    
    if ($railwayInstalled) {
        try {
            railway variables set "$key=$value" 2>$null
            if ($?) {
                Write-Host "✅ Added $key to Railway" -ForegroundColor Green
            }
        } catch {
            Write-Host "❌ Failed to add $key to Railway" -ForegroundColor Red
        }
    }
}

Write-Host "Reading environment variables from .env file..." -ForegroundColor Yellow
Write-Host ""

# Read .env file if it exists
$envFile = ".env"
if (Test-Path $envFile) {
    $envVars = @{}
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $envVars[$key] = $value
        }
    }
    
    Write-Host "Found $($envVars.Count) environment variables" -ForegroundColor Cyan
    Write-Host ""
    
    # Critical variables that should be migrated
    $criticalVars = @(
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_ANON_KEY",
        "JWT_SECRET",
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "VERCEL_TOKEN",
        "RAILWAY_TOKEN"
    )
    
    Write-Host "Migrating critical environment variables..." -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($var in $criticalVars) {
        if ($envVars.ContainsKey($var)) {
            Write-Host "Processing: $var" -ForegroundColor Cyan
            
            # Mask the value for display
            $maskedValue = if ($envVars[$var].Length -gt 10) {
                $envVars[$var].Substring(0, 5) + "..." + $envVars[$var].Substring($envVars[$var].Length - 5)
            } else {
                "***"
            }
            
            Write-Host "  Value: $maskedValue" -ForegroundColor Gray
            
            $confirm = Read-Host "  Add to Vercel? (y/n)"
            if ($confirm -eq 'y') {
                Add-VercelEnv -key $var -value $envVars[$var]
            }
            
            if ($railwayInstalled) {
                $confirm = Read-Host "  Add to Railway? (y/n)"
                if ($confirm -eq 'y') {
                    Add-RailwayEnv -key $var -value $envVars[$var]
                }
            }
            
            Write-Host ""
        }
    }
    
    Write-Host "================================" -ForegroundColor Green
    Write-Host "Migration Summary" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Environment variables processed" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Verify variables in Vercel dashboard: https://vercel.com/dashboard" -ForegroundColor White
    Write-Host "2. Verify variables in Railway dashboard: https://railway.app" -ForegroundColor White
    Write-Host "3. Delete local .env files with sensitive data" -ForegroundColor White
    Write-Host "4. Rotate all exposed credentials immediately" -ForegroundColor Red
    Write-Host ""
    Write-Host "To remove .env files safely:" -ForegroundColor Yellow
    Write-Host "  Remove-Item .env, .env.local, .env.production -Force" -ForegroundColor Gray
    Write-Host ""
    
} else {
    Write-Host "❌ No .env file found in current directory" -ForegroundColor Red
    Write-Host "   Please run this script from the project root" -ForegroundColor Yellow
}

Write-Host "Script completed!" -ForegroundColor Green