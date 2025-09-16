# SUNBIZ SUPERVISOR INSTALLATION SCRIPT - Windows PowerShell
# =========================================================
# Installs and configures the Sunbiz Supervisor Agent as a Windows Service

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "SUNBIZ SUPERVISOR AGENT INSTALLATION" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Exit 1
}

# Configuration
$ServiceName = "SunbizSupervisor"
$ServiceDisplayName = "Sunbiz Database Supervisor Agent"
$ServiceDescription = "Manages daily updates of Florida Sunbiz database"
$InstallPath = "C:\ProgramData\SunbizSupervisor"
$PythonPath = "python"
$LogPath = "$InstallPath\logs"

Write-Host "[1/8] Creating installation directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null
New-Item -ItemType Directory -Force -Path $LogPath | Out-Null

Write-Host "[2/8] Copying agent files..." -ForegroundColor Yellow
$SourcePath = "$PSScriptRoot\apps\agents"
Copy-Item "$SourcePath\sunbiz_supervisor_agent.py" -Destination $InstallPath -Force
Copy-Item "$SourcePath\sunbiz_supervisor_service.py" -Destination $InstallPath -Force
Copy-Item "$SourcePath\sunbiz_supervisor_dashboard.py" -Destination $InstallPath -Force
Copy-Item "$SourcePath\florida_daily_updater.py" -Destination $InstallPath -Force
Copy-Item "$SourcePath\florida_cloud_updater.py" -Destination $InstallPath -Force

Write-Host "[3/8] Creating configuration file..." -ForegroundColor Yellow
$ConfigContent = @{
    database_url = $env:DATABASE_URL
    update_schedule = "02:00"
    health_check_interval = 300
    max_retries = 3
    enable_auto_recovery = $true
    alert_email = ""
    webhook_url = ""
} | ConvertTo-Json

$ConfigContent | Out-File -FilePath "$InstallPath\sunbiz_supervisor_config.json" -Encoding UTF8

Write-Host "[4/8] Installing Python dependencies..." -ForegroundColor Yellow
& $PythonPath -m pip install psycopg2-binary paramiko schedule fastapi uvicorn pywin32

Write-Host "[5/8] Creating Windows service..." -ForegroundColor Yellow
$ServicePath = "$PythonPath `"$InstallPath\sunbiz_supervisor_service.py`""

# Remove existing service if it exists
$ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($ExistingService) {
    Write-Host "   Removing existing service..." -ForegroundColor Gray
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    & sc.exe delete $ServiceName
    Start-Sleep -Seconds 2
}

# Install the service
Write-Host "   Installing new service..." -ForegroundColor Gray
& python "$InstallPath\sunbiz_supervisor_service.py" install

Write-Host "[6/8] Configuring service settings..." -ForegroundColor Yellow
# Set service to automatic start
Set-Service -Name $ServiceName -StartupType Automatic -ErrorAction SilentlyContinue

# Set recovery options
& sc.exe failure $ServiceName reset=86400 actions=restart/60000/restart/60000/restart/60000

Write-Host "[7/8] Creating scheduled tasks..." -ForegroundColor Yellow

# Create scheduled task for dashboard
$DashboardAction = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$InstallPath\sunbiz_supervisor_dashboard.py`""
$DashboardTrigger = New-ScheduledTaskTrigger -AtStartup
$DashboardPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "SunbizDashboard" `
    -Action $DashboardAction `
    -Trigger $DashboardTrigger `
    -Principal $DashboardPrincipal `
    -Description "Sunbiz Supervisor Dashboard API" `
    -Force | Out-Null

Write-Host "[8/8] Starting services..." -ForegroundColor Yellow
Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
Start-ScheduledTask -TaskName "SunbizDashboard" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
$Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($Service) {
    Write-Host "   Name: $($Service.Name)" -ForegroundColor White
    Write-Host "   Status: $($Service.Status)" -ForegroundColor $(if($Service.Status -eq 'Running'){'Green'}else{'Yellow'})
}

Write-Host ""
Write-Host "Dashboard Access:" -ForegroundColor Cyan
Write-Host "   URL: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "Log Files:" -ForegroundColor Cyan
Write-Host "   Location: $LogPath" -ForegroundColor White
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Cyan
Write-Host "   Start Service:   Start-Service -Name $ServiceName" -ForegroundColor Gray
Write-Host "   Stop Service:    Stop-Service -Name $ServiceName" -ForegroundColor Gray
Write-Host "   Service Status:  Get-Service -Name $ServiceName" -ForegroundColor Gray
Write-Host "   View Logs:       Get-Content `"$LogPath\sunbiz_supervisor.log`" -Tail 50" -ForegroundColor Gray
Write-Host ""

# Ask if user wants to open dashboard
$OpenDashboard = Read-Host "Would you like to open the dashboard now? (Y/N)"
if ($OpenDashboard -eq 'Y' -or $OpenDashboard -eq 'y') {
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:8080"
}