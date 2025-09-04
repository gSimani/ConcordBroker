# ConcordBroker Stack Connection Test Script
# Tests all services in the production stack

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   CONCORDBROKER STACK CONNECTION TEST" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$allTestsPassed = $true

# Test 1: Supabase Connection
Write-Host "1. Testing Supabase Database..." -ForegroundColor Yellow

$supabaseUrl = "https://pmispwtdngkcmsrsjwbp.supabase.co"
$supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

try {
    $headers = @{
        "apikey" = $supabaseKey
        "Authorization" = "Bearer $supabaseKey"
    }
    
    $response = Invoke-RestMethod -Uri "$supabaseUrl/rest/v1/" -Headers $headers -Method Get -ErrorAction Stop
    Write-Host "   ✅ Supabase connection successful" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Supabase connection failed: $_" -ForegroundColor Red
    $allTestsPassed = $false
}

Write-Host ""

# Test 2: Railway API
Write-Host "2. Testing Railway API..." -ForegroundColor Yellow

$railwayUrl = "https://concordbroker-railway-production.up.railway.app"

try {
    $response = Invoke-WebRequest -Uri "$railwayUrl/health" -Method Get -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Railway API is healthy" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ Railway API returned status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    # Railway might not be deployed yet
    Write-Host "   ⚠️ Railway API not accessible (may not be deployed yet)" -ForegroundColor Yellow
    Write-Host "   Deploy with: railway up" -ForegroundColor White
}

Write-Host ""

# Test 3: Vercel Frontend
Write-Host "3. Testing Vercel Frontend..." -ForegroundColor Yellow

$vercelUrls = @(
    "https://concordbroker.com",
    "https://concordbroker.vercel.app"
)

$vercelAccessible = $false
foreach ($url in $vercelUrls) {
    try {
        $response = Invoke-WebRequest -Uri $url -Method Head -ErrorAction Stop -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✅ Frontend accessible at: $url" -ForegroundColor Green
            $vercelAccessible = $true
            break
        }
    } catch {
        continue
    }
}

if (-not $vercelAccessible) {
    Write-Host "   ⚠️ Frontend not accessible (may not be deployed yet)" -ForegroundColor Yellow
    Write-Host "   Deploy with: vercel --prod" -ForegroundColor White
}

Write-Host ""

# Test 4: Twilio
Write-Host "4. Testing Twilio Configuration..." -ForegroundColor Yellow

$twilioSid = "AC4036e1260ef9372999cda002f533d9f1"
$twilioToken = "035bd39a6462a4ad22aeca3b422fb01e"

try {
    $base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${twilioSid}:${twilioToken}"))
    $headers = @{
        "Authorization" = "Basic $base64Auth"
    }
    
    $response = Invoke-RestMethod -Uri "https://api.twilio.com/2010-04-01/Accounts/$twilioSid.json" -Headers $headers -Method Get -ErrorAction Stop
    
    if ($response.status -eq "active") {
        Write-Host "   ✅ Twilio account active" -ForegroundColor Green
        Write-Host "   Phone: +15614755454" -ForegroundColor White
    } else {
        Write-Host "   ⚠️ Twilio account status: $($response.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Twilio connection failed: $_" -ForegroundColor Red
    $allTestsPassed = $false
}

Write-Host ""

# Test 5: SendGrid
Write-Host "5. Testing SendGrid Email..." -ForegroundColor Yellow

$sendgridKey = "SG.c2b3d2dc39de750595eab3979d79c0c0"

try {
    $headers = @{
        "Authorization" = "Bearer $sendgridKey"
    }
    
    # Test SendGrid API key validity
    $response = Invoke-RestMethod -Uri "https://api.sendgrid.com/v3/scopes" -Headers $headers -Method Get -ErrorAction Stop
    
    if ($response.scopes) {
        Write-Host "   ✅ SendGrid API key valid" -ForegroundColor Green
        Write-Host "   Email: noreply@concordbroker.com" -ForegroundColor White
    }
} catch {
    Write-Host "   ❌ SendGrid connection failed: $_" -ForegroundColor Red
    $allTestsPassed = $false
}

Write-Host ""

# Test 6: MCP Server
Write-Host "6. Testing MCP Server Setup..." -ForegroundColor Yellow

$mcpPath = "C:\Users\gsima\Documents\MyProject\ConcordBroker\mcp-server-twilio"

if (Test-Path "$mcpPath\dist\index.js") {
    Write-Host "   ✅ MCP Server built and ready" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ MCP Server not built" -ForegroundColor Yellow
    Write-Host "   Build with: cd mcp-server-twilio && npm run build" -ForegroundColor White
}

Write-Host ""

# Summary
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "              TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($allTestsPassed) {
    Write-Host "✅ All critical services are connected!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Stack Status:" -ForegroundColor Yellow
    Write-Host "  • Supabase: Connected" -ForegroundColor Green
    Write-Host "  • Twilio: Connected" -ForegroundColor Green
    Write-Host "  • SendGrid: Connected" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Deploy backend: railway up" -ForegroundColor White
    Write-Host "  2. Deploy frontend: cd apps\web && vercel --prod" -ForegroundColor White
    Write-Host "  3. Update Supabase password in dashboard" -ForegroundColor White
} else {
    Write-Host "⚠️ Some services need attention" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please check the failed connections above." -ForegroundColor White
    Write-Host "Review STACK_CONFIGURATION.md for setup instructions." -ForegroundColor White
}

Write-Host ""
Write-Host "Configuration Files:" -ForegroundColor Cyan
Write-Host "  • Environment: .env.production" -ForegroundColor White
Write-Host "  • Stack Info: STACK_CONFIGURATION.md" -ForegroundColor White
Write-Host "  • MCP Config: mcp-server-twilio\.env" -ForegroundColor White