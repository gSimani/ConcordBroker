# Vercel Deployment Script for ConcordBroker
# Deploys the web application to Vercel production

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Deploying ConcordBroker to Vercel" -ForegroundColor Cyan
Write-Host "   Project: concord-broker" -ForegroundColor Cyan
Write-Host "   Domain: https://www.concordbroker.com" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Vercel CLI is installed
$vercelVersion = vercel --version 2>$null
if (-not $vercelVersion) {
    Write-Host "Vercel CLI not found. Installing..." -ForegroundColor Yellow
    Write-Host "Installing Vercel CLI globally..." -ForegroundColor Green
    npm install -g vercel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install Vercel CLI" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Vercel CLI Version: $vercelVersion" -ForegroundColor Green
Write-Host ""

# Set Vercel token for authentication
$env:VERCEL_TOKEN = "t9AK4qQ51TyAc0K0ZLk7tN0H"

# Configure project
Write-Host "Configuring Vercel project..." -ForegroundColor Yellow
Write-Host "Team: westbocaexecs-projects" -ForegroundColor Gray
Write-Host "Project ID: prj_l6jgk7483iwPCcaYarq7sMgt2m7L" -ForegroundColor Gray
Write-Host ""

# Build the web application
Write-Host "Building web application..." -ForegroundColor Cyan
Set-Location -Path "apps/web"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    exit 1
}

npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build application" -ForegroundColor Red
    exit 1
}

Set-Location -Path "../.."

# Deploy to Vercel
Write-Host ""
Write-Host "Deploying to Vercel..." -ForegroundColor Cyan
Write-Host "This will deploy to production at https://www.concordbroker.com" -ForegroundColor Yellow
Write-Host ""

# Deploy with production flag
vercel --prod --token t9AK4qQ51TyAc0K0ZLk7tN0H --scope westbocaexecs-projects --yes

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   Deployment Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your application has been deployed to:" -ForegroundColor Cyan
    Write-Host "  Production: https://www.concordbroker.com" -ForegroundColor Yellow
    Write-Host "  Dashboard: https://vercel.com/westbocaexecs-projects/concord-broker" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "API Backend (Railway): https://concordbroker.up.railway.app" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "Deployment failed. Please check the error messages above." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"