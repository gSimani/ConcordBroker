# PowerShell Script to Rotate All Credentials
# This script helps automate the credential rotation process

Write-Host "==========================================" -ForegroundColor Red
Write-Host "     CREDENTIAL ROTATION ASSISTANT" -ForegroundColor Red
Write-Host "==========================================" -ForegroundColor Red
Write-Host ""
Write-Host "⚠️  CRITICAL SECURITY ALERT" -ForegroundColor Yellow
Write-Host "Your credentials have been exposed and must be rotated immediately!" -ForegroundColor Yellow
Write-Host ""

# Function to generate secure random strings
function New-SecurePassword {
    param(
        [int]$Length = 32
    )
    $chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'
    $password = -join ((1..$Length) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
    return $password
}

function New-SecureToken {
    param(
        [int]$Length = 64
    )
    $bytes = New-Object byte[] $Length
    [Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

# Create a new .env.new file with rotated credentials
$envFile = ".env.new"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

Write-Host "Creating new environment file with secure credentials..." -ForegroundColor Cyan
Write-Host ""

# Generate new secure credentials
$newCredentials = @"
# ConcordBroker Environment Variables - ROTATED $timestamp
# ⚠️  These are NEW credentials - old ones should be revoked

# Database (Supabase) - UPDATE THESE WITH YOUR NEW VALUES FROM SUPABASE DASHBOARD
DATABASE_URL=postgres://username:$(New-SecurePassword)@host:port/database?sslmode=require
POSTGRES_PASSWORD=$(New-SecurePassword)

# JWT Authentication - NEW SECURE SECRETS
JWT_SECRET=$(New-SecureToken)
SUPABASE_JWT_SECRET=$(New-SecureToken)

# IMPORTANT: Replace these with actual values from service dashboards
SUPABASE_URL=https://your-new-project.supabase.co
SUPABASE_ANON_KEY=GET_FROM_SUPABASE_DASHBOARD
SUPABASE_SERVICE_ROLE_KEY=GET_FROM_SUPABASE_DASHBOARD

# API Keys - GET NEW ONES FROM EACH SERVICE
OPENAI_API_KEY=sk-...GET_NEW_KEY_FROM_OPENAI
ANTHROPIC_API_KEY=sk-ant-...GET_NEW_KEY_FROM_ANTHROPIC
GOOGLE_AI_API_KEY=AIza...GET_NEW_KEY_FROM_GOOGLE
GITHUB_TOKEN=ghp_...GET_NEW_TOKEN_FROM_GITHUB

# Other Services
CLOUDFLARE_API_KEY=GET_NEW_KEY_FROM_CLOUDFLARE
VERCEL_TOKEN=GET_NEW_TOKEN_FROM_VERCEL
RAILWAY_TOKEN=GET_NEW_TOKEN_FROM_RAILWAY
SENTRY_DSN=GET_NEW_DSN_FROM_SENTRY

# Application Settings (safe to keep)
NODE_ENV=production
ENVIRONMENT=production
APP_NAME=ConcordBroker
API_PORT=8000
API_HOST=0.0.0.0
"@

# Write new credentials to file
$newCredentials | Out-File -FilePath $envFile -Encoding UTF8

Write-Host "✅ Generated new secure passwords and tokens" -ForegroundColor Green
Write-Host "📄 New credentials saved to: $envFile" -ForegroundColor Green
Write-Host ""

# Backup old .env files before deletion
$backupDir = "env_backup_$timestamp"
Write-Host "Backing up old .env files to $backupDir..." -ForegroundColor Yellow

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Get-ChildItem -Path . -Filter ".env*" -File | ForEach-Object {
    if ($_.Name -ne ".env.new" -and $_.Name -ne ".env.example") {
        Copy-Item $_.FullName -Destination "$backupDir\$($_.Name)" -Force
        Write-Host "  Backed up: $($_.Name)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "     MANUAL STEPS REQUIRED" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  SUPABASE (Do this FIRST):" -ForegroundColor Yellow
Write-Host "   • Open: https://supabase.com/dashboard" -ForegroundColor White
Write-Host "   • Go to Settings → Database → Reset Database Password" -ForegroundColor White
Write-Host "   • Go to Settings → API → Roll service_role key" -ForegroundColor White
Write-Host "   • Copy new values to $envFile" -ForegroundColor White
Write-Host ""

Write-Host "2️⃣  GITHUB TOKEN:" -ForegroundColor Yellow
Write-Host "   • Open: https://github.com/settings/tokens" -ForegroundColor White
Write-Host "   • DELETE the old token immediately" -ForegroundColor Red
Write-Host "   • Generate new token with minimal permissions" -ForegroundColor White
Write-Host "   • Copy new token to $envFile" -ForegroundColor White
Write-Host ""

Write-Host "3️⃣  API KEYS:" -ForegroundColor Yellow
Write-Host "   • OpenAI: https://platform.openai.com/api-keys" -ForegroundColor White
Write-Host "   • Anthropic: https://console.anthropic.com/" -ForegroundColor White
Write-Host "   • Google: https://console.cloud.google.com/" -ForegroundColor White
Write-Host "   • DELETE old keys and create new ones" -ForegroundColor Red
Write-Host "   • Copy new keys to $envFile" -ForegroundColor White
Write-Host ""

# Prompt to continue
Write-Host "Have you updated the credentials in $envFile with real values from the service dashboards?" -ForegroundColor Yellow
$confirm = Read-Host "Type 'yes' when complete"

if ($confirm -ne 'yes') {
    Write-Host "❌ Rotation cancelled. Please update $envFile manually and re-run." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Updating Vercel environment variables..." -ForegroundColor Cyan

# Check if Vercel CLI is installed
$vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue
if ($vercelInstalled) {
    Write-Host "Adding environment variables to Vercel..." -ForegroundColor Yellow
    
    # Read the new env file and push to Vercel
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            if ($value -and $value -notlike "*GET_*" -and $value -notlike "*your-*") {
                Write-Host "  Setting $key..." -ForegroundColor Gray
                
                # Add to all environments
                echo $value | vercel env add $key production --force 2>$null
                echo $value | vercel env add $key preview --force 2>$null
                echo $value | vercel env add $key development --force 2>$null
            }
        }
    }
    
    Write-Host "✅ Vercel environment variables updated" -ForegroundColor Green
} else {
    Write-Host "⚠️  Vercel CLI not found. Install with: npm i -g vercel" -ForegroundColor Yellow
    Write-Host "   Then manually add variables from $envFile" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Cleaning up old files..." -ForegroundColor Cyan

# Remove old .env files
$filesToDelete = @(
    ".env",
    ".env.local", 
    ".env.production",
    ".env.supabase",
    ".env.railway",
    ".env.huggingface"
)

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  ✅ Deleted: $file" -ForegroundColor Green
    }
}

# Clean from git
Write-Host ""
Write-Host "Removing from git tracking..." -ForegroundColor Cyan
git rm --cached .env* 2>$null

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "     ROTATION COMPLETE" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ New credentials generated in: $envFile" -ForegroundColor Green
Write-Host "✅ Old files backed up to: $backupDir" -ForegroundColor Green
Write-Host "✅ Removed sensitive files from git" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  IMPORTANT NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Rename $envFile to .env when ready to use" -ForegroundColor White
Write-Host "2. Deploy to trigger use of new credentials:" -ForegroundColor White
Write-Host "   vercel --prod" -ForegroundColor Gray
Write-Host "3. Test all services are working" -ForegroundColor White
Write-Host "4. Delete the backup folder: $backupDir" -ForegroundColor White
Write-Host ""
Write-Host "Security Tip: Enable 2FA on all service accounts!" -ForegroundColor Cyan