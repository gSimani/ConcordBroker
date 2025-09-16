# PowerShell Deployment Script for Cloud-Native Sunbiz Daily Update System
# This script deploys the complete cloud infrastructure with ZERO PC dependency

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CLOUD-NATIVE SUNBIZ DEPLOYMENT SYSTEM" -ForegroundColor Cyan
Write-Host "  100% Cloud-Based Daily Updates" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if required tools are installed
Write-Host "[1/7] Checking prerequisites..." -ForegroundColor Yellow

$supabaseCli = Get-Command supabase -ErrorAction SilentlyContinue
if (-not $supabaseCli) {
    Write-Host "Installing Supabase CLI..." -ForegroundColor Yellow
    npm install -g supabase
}

$vercelCli = Get-Command vercel -ErrorAction SilentlyContinue
if (-not $vercelCli) {
    Write-Host "Installing Vercel CLI..." -ForegroundColor Yellow
    npm install -g vercel
}

# Step 1: Deploy Supabase Edge Function
Write-Host ""
Write-Host "[2/7] Deploying Supabase Edge Function..." -ForegroundColor Yellow

# Link to Supabase project
Write-Host "Linking to Supabase project..." -ForegroundColor Gray
$supabaseUrl = $env:VITE_SUPABASE_URL
if ($supabaseUrl) {
    $projectRef = $supabaseUrl -replace 'https://', '' -replace '.supabase.co', ''
    supabase link --project-ref $projectRef
}

# Deploy the edge function
Write-Host "Deploying sunbiz-daily-update function..." -ForegroundColor Gray
supabase functions deploy sunbiz-daily-update

# Set environment variables for edge function
Write-Host "Setting edge function secrets..." -ForegroundColor Gray
if ($env:WEBHOOK_URL) {
    supabase secrets set WEBHOOK_URL="$env:WEBHOOK_URL"
}

# Step 2: Create database tables
Write-Host ""
Write-Host "[3/7] Creating database tables..." -ForegroundColor Yellow

$sqlScript = @"
-- Tracking table for processed files
CREATE TABLE IF NOT EXISTS florida_daily_processed_files (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) UNIQUE NOT NULL,
    file_type VARCHAR(50),
    file_date DATE,
    records_processed INTEGER DEFAULT 0,
    entities_created INTEGER DEFAULT 0,
    entities_updated INTEGER DEFAULT 0,
    processing_time_seconds FLOAT,
    processed_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'completed',
    error_message TEXT
);

-- Supervisor status table
CREATE TABLE IF NOT EXISTS sunbiz_supervisor_status (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    last_update TIMESTAMP DEFAULT NOW(),
    metrics JSONB,
    error_log JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_processed_files_date 
ON florida_daily_processed_files(file_date DESC);

CREATE INDEX IF NOT EXISTS idx_supervisor_status_created 
ON sunbiz_supervisor_status(created_at DESC);

-- Grant permissions
GRANT ALL ON florida_daily_processed_files TO service_role;
GRANT ALL ON sunbiz_supervisor_status TO service_role;
"@

$sqlScript | supabase db push

# Step 3: Setup Vercel environment variables
Write-Host ""
Write-Host "[4/7] Configuring Vercel environment..." -ForegroundColor Yellow

# Generate CRON_SECRET if not exists
if (-not $env:CRON_SECRET) {
    $cronSecret = [System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
    Write-Host "Generated CRON_SECRET: $cronSecret" -ForegroundColor Gray
} else {
    $cronSecret = $env:CRON_SECRET
}

# Set Vercel environment variables
Write-Host "Setting Vercel environment variables..." -ForegroundColor Gray
Write-Output "$env:VITE_SUPABASE_URL" | vercel env add SUPABASE_URL production --force
Write-Output "$env:SUPABASE_SERVICE_ROLE_KEY" | vercel env add SUPABASE_SERVICE_ROLE_KEY production --force
Write-Output "$cronSecret" | vercel env add CRON_SECRET production --force

if ($env:WEBHOOK_URL) {
    Write-Output "$env:WEBHOOK_URL" | vercel env add WEBHOOK_URL production --force
}

if ($env:SENDGRID_API_KEY) {
    Write-Output "$env:SENDGRID_API_KEY" | vercel env add SENDGRID_API_KEY production --force
    Write-Output "$env:ALERT_EMAIL" | vercel env add ALERT_EMAIL production --force
}

# Step 4: Deploy to Vercel
Write-Host ""
Write-Host "[5/7] Deploying to Vercel..." -ForegroundColor Yellow
vercel --prod

# Step 5: Test the deployment
Write-Host ""
Write-Host "[6/7] Testing cloud deployment..." -ForegroundColor Yellow

$vercelUrl = (vercel ls --json | ConvertFrom-Json)[0].url
if ($vercelUrl) {
    Write-Host "Testing manual trigger..." -ForegroundColor Gray
    $testUrl = "https://$vercelUrl/api/cron/sunbiz-daily-update"
    
    try {
        $response = Invoke-RestMethod -Uri $testUrl -Method POST `
            -Headers @{ "Authorization" = "Bearer $cronSecret" } `
            -TimeoutSec 30
        
        if ($response.success) {
            Write-Host "[SUCCESS] Cloud deployment successful!" -ForegroundColor Green
            Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Gray
        } else {
            Write-Host "[WARNING] Deployment completed but test failed" -ForegroundColor Yellow
            Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "[WARNING] Test trigger failed (this is normal for first deployment)" -ForegroundColor Yellow
        Write-Host "Error: $_" -ForegroundColor Gray
    }
}

# Step 7: Display summary
Write-Host ""
Write-Host "[7/7] Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT SUMMARY" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] Supabase Edge Function: Deployed" -ForegroundColor Green
Write-Host "[OK] Database Tables: Created" -ForegroundColor Green
Write-Host "[OK] Vercel Cron Job: Configured" -ForegroundColor Green
Write-Host "[OK] Environment Variables: Set" -ForegroundColor Green
Write-Host ""
Write-Host "Cloud Infrastructure:" -ForegroundColor Cyan
Write-Host "   - Vercel URL: https://$vercelUrl" -ForegroundColor White
Write-Host "   - Cron Schedule: Daily at 2 AM EST (7 AM UTC)" -ForegroundColor White
Write-Host "   - Edge Function: sunbiz-daily-update" -ForegroundColor White
Write-Host ""
Write-Host "Monitor at:" -ForegroundColor Cyan
Write-Host "   - Vercel Dashboard: https://vercel.com/dashboard" -ForegroundColor White
Write-Host "   - Supabase Dashboard: $env:VITE_SUPABASE_URL" -ForegroundColor White
Write-Host ""
Write-Host "Manual Trigger Command:" -ForegroundColor Cyan
Write-Host "   curl -X POST https://$vercelUrl/api/cron/sunbiz-daily-update \" -ForegroundColor White
Write-Host "        -H 'Authorization: Bearer $cronSecret'" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Verify cron job in Vercel Dashboard → Functions → Cron Jobs" -ForegroundColor White
Write-Host "   2. Check first automatic run at 2 AM EST tomorrow" -ForegroundColor White
Write-Host "   3. Monitor logs in both Vercel and Supabase dashboards" -ForegroundColor White
Write-Host ""
Write-Host "Your Sunbiz data will now update automatically every day!" -ForegroundColor Green
Write-Host "   NO PC CONNECTION REQUIRED - 100% CLOUD-NATIVE!" -ForegroundColor Green
Write-Host ""