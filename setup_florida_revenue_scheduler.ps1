# Florida Revenue Daily Sync - Windows Task Scheduler Setup
# This script sets up automated daily synchronization at 2 AM

$taskName = "FloridaRevenueDailySync"
$scriptPath = "$PSScriptRoot\florida_revenue_daily_sync_system.py"
$pythonPath = "python"
$workingDirectory = $PSScriptRoot

# Create the scheduled task action
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath -WorkingDirectory $workingDirectory

# Create the trigger (daily at 2 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# Create the principal (run whether user is logged in or not)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartInterval (New-TimeSpan -Minutes 30) -RestartCount 3

# Register the task
try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
    Write-Host "Successfully created scheduled task: $taskName" -ForegroundColor Green
    Write-Host "The task will run daily at 2:00 AM" -ForegroundColor Yellow
    
    # Show task details
    Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State, LastRunTime, NextRunTime
} catch {
    Write-Host "Error creating scheduled task: $_" -ForegroundColor Red
}

# Optional: Run the task immediately for testing
$runNow = Read-Host "Do you want to run the sync task now for testing? (Y/N)"
if ($runNow -eq 'Y') {
    Start-ScheduledTask -TaskName $taskName
    Write-Host "Task started. Check logs at: $PSScriptRoot\florida_revenue_sync.log" -ForegroundColor Cyan
}