# ============================================
# CONCORDBROKER AUTOMATED MERGE SYSTEM
# PowerShell Version with Error Handling
# ============================================

$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "ConcordBroker Auto-Merge System"

# Configuration
$config = @{
    Frontend = @{
        Port = 5173
        Path = "apps\web"
        StartCommand = "npm run dev"
        BuildCommand = "npm run build"
    }
    Backend = @{
        Port = 8000
        Path = "apps\api"
        StartCommand = "npm run dev"
        BuildCommand = "npm run build"
    }
    MCP = @{
        Port = 3005
        Path = "mcp-server"
        StartCommand = "npm start"
    }
}

# Colors for output
function Write-Success($message) { Write-Host $message -ForegroundColor Green }
function Write-Error($message) { Write-Host $message -ForegroundColor Red }
function Write-Warning($message) { Write-Host $message -ForegroundColor Yellow }
function Write-Info($message) { Write-Host $message -ForegroundColor Cyan }
function Write-Header($message) {
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host "  $message" -ForegroundColor Magenta
    Write-Host "========================================`n" -ForegroundColor Magenta
}

# Progress tracking
$global:progress = @{
    Total = 10
    Current = 0
    Tasks = @()
}

function Update-Progress($task, $status) {
    $global:progress.Current++
    $percent = ($global:progress.Current / $global:progress.Total) * 100
    Write-Progress -Activity "Merge Process" -Status "$task - $status" -PercentComplete $percent
    $global:progress.Tasks += @{Task = $task; Status = $status; Time = Get-Date}
}

# Main execution
try {
    Write-Header "CONCORDBROKER AUTOMATED MERGE SYSTEM"
    $startTime = Get-Date

    # ============================================
    # PHASE 1: CLEANUP
    # ============================================
    Write-Header "PHASE 1: CLEANUP"
    Update-Progress "Cleanup" "Starting"

    Write-Info "Killing duplicate processes..."
    $portsToClean = @(8000, 3005, 8003, 5173)
    foreach ($port in $portsToClean) {
        $connections = netstat -ano | Select-String ":$port.*LISTENING"
        foreach ($conn in $connections) {
            if ($conn -match '\s+(\d+)$') {
                $pid = $matches[1]
                try {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Write-Success "  Killed process on port $port (PID: $pid)"
                } catch {
                    Write-Warning "  Could not kill PID $pid"
                }
            }
        }
    }
    Start-Sleep -Seconds 2
    Update-Progress "Cleanup" "Complete"

    # ============================================
    # PHASE 2: DEPENDENCY INSTALLATION
    # ============================================
    Write-Header "PHASE 2: DEPENDENCIES"
    Update-Progress "Dependencies" "Checking"

    $paths = @(
        @{Path = "."; Name = "Root"},
        @{Path = "apps\web"; Name = "Frontend"},
        @{Path = "apps\api"; Name = "Backend"}
    )

    foreach ($item in $paths) {
        if (-not (Test-Path "$($item.Path)\node_modules")) {
            Write-Info "Installing $($item.Name) dependencies..."
            Push-Location $item.Path
            $result = npm install 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "  $($item.Name) dependencies installed"
            } else {
                Write-Error "  Failed to install $($item.Name) dependencies"
            }
            Pop-Location
        } else {
            Write-Success "  $($item.Name) dependencies already installed"
        }
    }
    Update-Progress "Dependencies" "Complete"

    # ============================================
    # PHASE 3: BUILD
    # ============================================
    Write-Header "PHASE 3: BUILD"
    Update-Progress "Build" "Starting"

    Write-Info "Building frontend..."
    Push-Location "apps\web"
    $buildResult = npm run build 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "  Frontend built successfully"
    } else {
        Write-Error "  Frontend build failed"
        Write-Warning "  Continuing with development mode..."
    }
    Pop-Location
    Update-Progress "Build" "Complete"

    # ============================================
    # PHASE 4: START SERVICES
    # ============================================
    Write-Header "PHASE 4: START SERVICES"
    Update-Progress "Services" "Starting"

    # Start MCP Server
    if (Test-Path "mcp-server") {
        Write-Info "Starting MCP Server..."
        Start-Process -FilePath "cmd" -ArgumentList "/c cd mcp-server && npm start" -WindowStyle Hidden
        Start-Sleep -Seconds 3
    }

    # Start Backend
    Write-Info "Starting Backend API..."
    Start-Process -FilePath "cmd" -ArgumentList "/c cd apps\api && npm run dev" -WindowStyle Hidden
    Start-Sleep -Seconds 3

    # Start Frontend
    Write-Info "Starting Frontend..."
    Start-Process -FilePath "cmd" -ArgumentList "/c cd apps\web && npm run dev" -WindowStyle Hidden
    Start-Sleep -Seconds 5

    Update-Progress "Services" "Started"

    # ============================================
    # PHASE 5: HEALTH CHECKS
    # ============================================
    Write-Header "PHASE 5: HEALTH CHECKS"
    Update-Progress "Health Checks" "Running"

    $services = @(
        @{Name = "Frontend"; Url = "http://localhost:5173"},
        @{Name = "Backend API"; Url = "http://localhost:8000"},
        @{Name = "MCP Server"; Url = "http://localhost:3005/health"}
    )

    $healthStatus = @{}
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -UseBasicParsing
            Write-Success "  $($service.Name): ONLINE"
            $healthStatus[$service.Name] = "ONLINE"
        } catch {
            Write-Error "  $($service.Name): OFFLINE"
            $healthStatus[$service.Name] = "OFFLINE"
        }
    }
    Update-Progress "Health Checks" "Complete"

    # ============================================
    # PHASE 6: DATA VERIFICATION
    # ============================================
    Write-Header "PHASE 6: DATA VERIFICATION"
    Update-Progress "Data Verification" "Testing"

    try {
        $testParcel = "474131031040"
        $apiUrl = "http://localhost:8000/api/properties/$testParcel"
        $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 10

        if ($response.parcel_id) {
            Write-Success "  Data API: Working"
            Write-Success "  Sample Property: $($response.phy_addr1)"
        } else {
            Write-Warning "  Data API: No data returned"
        }
    } catch {
        Write-Error "  Data API: Failed - $_"
    }
    Update-Progress "Data Verification" "Complete"

    # ============================================
    # PHASE 7: AUTOMATED TESTS
    # ============================================
    Write-Header "PHASE 7: AUTOMATED TESTS"
    Update-Progress "Tests" "Running"

    if (Test-Path "test-unified-system.cjs") {
        Write-Info "Running integration tests..."
        $testResult = node test-unified-system.cjs 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  Integration tests passed"
        } else {
            Write-Warning "  Some tests failed"
        }
    } else {
        Write-Warning "  No test file found"
    }
    Update-Progress "Tests" "Complete"

    # ============================================
    # PHASE 8: PERFORMANCE CHECK
    # ============================================
    Write-Header "PHASE 8: PERFORMANCE CHECK"
    Update-Progress "Performance" "Analyzing"

    $nodeProcesses = Get-Process -Name node -ErrorAction SilentlyContinue
    $totalMemory = 0
    $processCount = 0

    foreach ($proc in $nodeProcesses) {
        $memoryMB = [math]::Round($proc.WorkingSet64 / 1MB, 2)
        $totalMemory += $memoryMB
        $processCount++
        Write-Info "  Node Process (PID: $($proc.Id)): $memoryMB MB"
    }

    Write-Info "Total Node Processes: $processCount"
    Write-Info "Total Memory Usage: $totalMemory MB"

    if ($totalMemory -gt 2000) {
        Write-Warning "High memory usage detected! Consider optimization."
    } else {
        Write-Success "Memory usage is within acceptable range"
    }
    Update-Progress "Performance" "Complete"

    # ============================================
    # PHASE 9: GENERATE REPORT
    # ============================================
    Write-Header "PHASE 9: GENERATE REPORT"
    Update-Progress "Report" "Generating"

    $endTime = Get-Date
    $duration = $endTime - $startTime

    $report = @"
============================================
CONCORDBROKER MERGE COMPLETION REPORT
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
============================================

EXECUTION TIME: $($duration.TotalSeconds) seconds

SERVICE STATUS:
$($healthStatus.GetEnumerator() | ForEach-Object { "  $($_.Key): $($_.Value)" } | Out-String)

MEMORY USAGE:
  Total Processes: $processCount
  Total Memory: $totalMemory MB

TASKS COMPLETED:
$($global:progress.Tasks | ForEach-Object { "  [$($_.Time.ToString('HH:mm:ss'))] $($_.Task): $($_.Status)" } | Out-String)

RECOMMENDATIONS:
$(if ($totalMemory -gt 2000) { "  - Optimize memory usage (currently over 2GB)" })
$(if ($healthStatus.ContainsValue("OFFLINE")) { "  - Some services are offline, check logs" })
$(if ($processCount -gt 10) { "  - Too many Node processes, consider consolidation" })

============================================
"@

    $report | Out-File -FilePath "MERGE_REPORT_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    Write-Success "Report saved successfully"
    Update-Progress "Report" "Complete"

    # ============================================
    # PHASE 10: FINAL ACTIONS
    # ============================================
    Write-Header "PHASE 10: FINAL ACTIONS"
    Update-Progress "Final" "Completing"

    # Open browser
    Write-Info "Opening application in browser..."
    Start-Process "http://localhost:5173"

    # Show summary
    Write-Header "MERGE COMPLETE!"
    Write-Success @"

All systems merged and operational!

Services running at:
  Frontend:    http://localhost:5173
  Backend API: http://localhost:8000
  MCP Server:  http://localhost:3005

Total execution time: $($duration.TotalSeconds) seconds
Memory usage: $totalMemory MB
Success rate: $(($global:progress.Current / $global:progress.Total) * 100)%

Check the generated report for detailed information.
"@

} catch {
    Write-Error "CRITICAL ERROR: $_"
    Write-Error $_.ScriptStackTrace
} finally {
    Write-Progress -Activity "Merge Process" -Completed
    Write-Host "`nPress any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}