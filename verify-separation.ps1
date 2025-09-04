# Project Separation Verification Script
# Ensures ConcordBroker is completely separated from West Boca Executive Suites

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PROJECT SEPARATION VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errorFound = $false

# Check for West Boca references
Write-Host "Checking for West Boca references..." -ForegroundColor Yellow

$westBocaFiles = Get-ChildItem -Path . -Recurse -File -Include *.md,*.ts,*.js,*.py,*.json,*.env,*.yml,*.yaml 2>$null |
    Select-String -Pattern "westboca|west boca|WBES" -CaseSensitive:$false |
    Where-Object { $_.Path -notlike "*verify-separation.ps1" -and $_.Path -notlike "*PROJECT_SEPARATION_REPORT.md" } |
    Select-Object -ExpandProperty Path -Unique

if ($westBocaFiles.Count -gt 0) {
    Write-Host "❌ Found West Boca references in:" -ForegroundColor Red
    foreach ($file in $westBocaFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    $errorFound = $true
} else {
    Write-Host "✅ No West Boca references found" -ForegroundColor Green
}

Write-Host ""

# Check domains
Write-Host "Checking domain configurations..." -ForegroundColor Yellow

$concordDomains = @(
    "concordbroker.com",
    "api.concordbroker.com",
    "noreply@concordbroker.com",
    "support@concordbroker.com"
)

$validDomains = $true
foreach ($domain in $concordDomains) {
    $found = Get-ChildItem -Path . -Recurse -File -Include *.env,*.json,*.md -ErrorAction SilentlyContinue |
        Select-String -Pattern $domain -SimpleMatch |
        Select-Object -First 1
    
    if (-not $found) {
        Write-Host "⚠️  Missing expected domain: $domain" -ForegroundColor Yellow
        $validDomains = $false
    }
}

if ($validDomains) {
    Write-Host "✅ All ConcordBroker domains configured" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some domains may need configuration" -ForegroundColor Yellow
}

Write-Host ""

# Check MCP servers
Write-Host "Checking MCP servers..." -ForegroundColor Yellow

$mcpServers = Get-ChildItem -Path . -Directory -Filter "mcp-server-*" -ErrorAction SilentlyContinue

if ($mcpServers.Count -eq 0) {
    Write-Host "⚠️  No MCP servers found" -ForegroundColor Yellow
} else {
    foreach ($server in $mcpServers) {
        $packageJson = Join-Path $server.FullName "package.json"
        if (Test-Path $packageJson) {
            $content = Get-Content $packageJson | ConvertFrom-Json
            if ($content.name -like "*concordbroker*") {
                Write-Host "✅ MCP Server: $($server.Name) - Properly named for ConcordBroker" -ForegroundColor Green
            } else {
                Write-Host "⚠️  MCP Server: $($server.Name) - May need renaming" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""

# Check credentials
Write-Host "Checking credential separation..." -ForegroundColor Yellow

$envFile = ".env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    
    # Check for Twilio phone
    if ($envContent | Select-String -Pattern "\+15614755454") {
        Write-Host "✅ Twilio phone number is ConcordBroker dedicated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Twilio phone number not found or incorrect" -ForegroundColor Yellow
    }
    
    # Check for password containing West Boca
    if ($envContent | Select-String -Pattern "West.*Boca" -CaseSensitive:$false) {
        Write-Host "❌ Password contains 'West Boca' - needs change" -ForegroundColor Red
        $errorFound = $true
    } else {
        Write-Host "✅ No 'West Boca' in passwords" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           VERIFICATION RESULTS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($errorFound) {
    Write-Host "❌ FAILED: Issues found that need correction" -ForegroundColor Red
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Review PROJECT_SEPARATION_REPORT.md" -ForegroundColor White
    Write-Host "2. Fix identified issues" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    exit 1
} else {
    Write-Host "✅ PASSED: ConcordBroker is properly separated!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The project is ready for independent deployment." -ForegroundColor Green
    Write-Host ""
    Write-Host "Important reminders:" -ForegroundColor Yellow
    Write-Host "• Change Supabase password in dashboard to: Concord@Broker2025!" -ForegroundColor White
    Write-Host "• Keep credentials secure and never commit them" -ForegroundColor White
    Write-Host "• Use project-specific naming for all resources" -ForegroundColor White
    exit 0
}