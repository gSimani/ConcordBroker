# Railway Deployment Script for ConcordBroker
# Deploys the application to Railway production environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Deploying ConcordBroker to Railway" -ForegroundColor Cyan
Write-Host "   Project ID: 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Railway CLI is installed
$railwayVersion = railway version 2>$null
if (-not $railwayVersion) {
    Write-Host "Railway CLI not found. Installing..." -ForegroundColor Yellow
    Write-Host "Please install Railway CLI from: https://docs.railway.app/develop/cli" -ForegroundColor Yellow
    Write-Host "Run: npm install -g @railway/cli" -ForegroundColor Green
    exit 1
}

Write-Host "Railway CLI Version: $railwayVersion" -ForegroundColor Green
Write-Host ""

# Login to Railway
Write-Host "Logging into Railway..." -ForegroundColor Yellow
railway login

# Link to project
Write-Host "Linking to Railway project..." -ForegroundColor Yellow
railway link 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb

# Set environment
Write-Host "Setting environment to production..." -ForegroundColor Yellow
railway environment concordbrokerproduction

# Deploy
Write-Host ""
Write-Host "Starting deployment..." -ForegroundColor Cyan
Write-Host "This will deploy both API and Web services" -ForegroundColor Yellow
Write-Host ""

# Deploy the application
railway up

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your application is being deployed to:" -ForegroundColor Cyan
Write-Host "  Public URL: https://concordbroker.up.railway.app" -ForegroundColor Yellow
Write-Host "  Internal: concordbroker.railway.internal" -ForegroundColor Yellow
Write-Host ""
Write-Host "Check deployment status at:" -ForegroundColor Cyan
Write-Host "  https://railway.app/project/05f5fbf4-f31c-4bdb-9022-3e987dd80fdb" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"