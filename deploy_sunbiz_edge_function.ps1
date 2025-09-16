#!/usr/bin/env pwsh
# Deploy Sunbiz Edge Function to Supabase

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "DEPLOYING SUNBIZ EDGE FUNCTION" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if Supabase CLI is installed
if (!(Get-Command supabase -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Supabase CLI..." -ForegroundColor Yellow
    npm install -g supabase
}

# Initialize Supabase if needed
if (!(Test-Path "supabase/.gitignore")) {
    Write-Host "Initializing Supabase project..." -ForegroundColor Yellow
    supabase init
}

# Deploy the function
Write-Host "`nDeploying Edge Function..." -ForegroundColor Green
supabase functions deploy fetch-sunbiz --no-verify-jwt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Edge Function deployed successfully!" -ForegroundColor Green
    
    Write-Host "`n======================================" -ForegroundColor Cyan
    Write-Host "TEST THE FUNCTION" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    
    Write-Host "`n1. List available officer files:" -ForegroundColor Yellow
    Write-Host "curl -X POST https://pmispwtdngkcmsrsjwbp.supabase.co/functions/v1/fetch-sunbiz \"
    Write-Host "  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU0OTEyNjQsImV4cCI6MjA0MTA2NzI2NH0.2uYtqSu7tb-umJmDx5kGFOHHLzMO0LlNvFxB8L_C-tE' \"
    Write-Host "  -H 'Content-Type: application/json' \"
    Write-Host "  -d '{\"action\": \"list\", \"data_type\": \"off\"}'"
    
    Write-Host "`n2. Download specific officer file:" -ForegroundColor Yellow
    Write-Host "curl -X POST https://pmispwtdngkcmsrsjwbp.supabase.co/functions/v1/fetch-sunbiz \"
    Write-Host "  -H 'Authorization: Bearer [ANON_KEY]' \"
    Write-Host "  -H 'Content-Type: application/json' \"
    Write-Host "  -d '{\"action\": \"download\", \"data_type\": \"off\", \"filename\": \"OFFP0001.txt\"}'"
    
    Write-Host "`n3. Stream for pipeline processing:" -ForegroundColor Yellow
    Write-Host "Use the sunbiz_edge_pipeline_loader.py to process directly"
    
} else {
    Write-Host "`n❌ Deployment failed. Check your Supabase configuration." -ForegroundColor Red
    Write-Host "Make sure you're logged in: supabase login" -ForegroundColor Yellow
}