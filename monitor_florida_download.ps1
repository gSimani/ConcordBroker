# Florida Revenue Download Monitor
# PowerShell script to monitor download progress

$basePath = "C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"

Write-Host "Florida Revenue Download Monitor" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Count files by data type
$nalCount = (Get-ChildItem -Path $basePath -Recurse -Filter "NAL*.csv" -ErrorAction SilentlyContinue | Measure-Object).Count
$nalCount += (Get-ChildItem -Path $basePath -Recurse -Filter "NAL*.xls*" -ErrorAction SilentlyContinue | Measure-Object).Count

$napCount = (Get-ChildItem -Path $basePath -Recurse -Filter "NAP*.csv" -ErrorAction SilentlyContinue | Measure-Object).Count
$napCount += (Get-ChildItem -Path $basePath -Recurse -Filter "NAP*.xls*" -ErrorAction SilentlyContinue | Measure-Object).Count

$sdfCount = (Get-ChildItem -Path $basePath -Recurse -Filter "SDF*.csv" -ErrorAction SilentlyContinue | Measure-Object).Count
$sdfCount += (Get-ChildItem -Path $basePath -Recurse -Filter "SDF*.xls*" -ErrorAction SilentlyContinue | Measure-Object).Count

$totalCounties = 67
$totalExpected = $totalCounties * 3

Write-Host "Download Progress:" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow
Write-Host "NAL Files: $nalCount / $totalCounties" -ForegroundColor Green
Write-Host "NAP Files: $napCount / $totalCounties" -ForegroundColor Green  
Write-Host "SDF Files: $sdfCount / $totalCounties" -ForegroundColor Green
Write-Host ""
Write-Host "Total: $($nalCount + $napCount + $sdfCount) / $totalExpected files" -ForegroundColor White
Write-Host ""

# Show progress bar
$progress = [math]::Round((($nalCount + $napCount + $sdfCount) / $totalExpected) * 100, 2)
$progressBar = "[" + ("=" * [math]::Floor($progress / 5)) + (" " * (20 - [math]::Floor($progress / 5))) + "]"
Write-Host "Progress: $progressBar $progress%" -ForegroundColor Cyan
Write-Host ""

# Check which counties are complete
Write-Host "County Status:" -ForegroundColor Yellow
Write-Host "==============" -ForegroundColor Yellow

$counties = Get-ChildItem -Path $basePath -Directory | Select-Object -First 10

foreach ($county in $counties) {
    $countyPath = Join-Path $basePath $county.Name
    
    $hasNAL = Test-Path (Join-Path $countyPath "NAL\*.csv"), (Join-Path $countyPath "NAL\*.xls*")
    $hasNAP = Test-Path (Join-Path $countyPath "NAP\*.csv"), (Join-Path $countyPath "NAP\*.xls*")
    $hasSDF = Test-Path (Join-Path $countyPath "SDF\*.csv"), (Join-Path $countyPath "SDF\*.xls*")
    
    $status = ""
    if ($hasNAL) { $status += "NAL " }
    if ($hasNAP) { $status += "NAP " }
    if ($hasSDF) { $status += "SDF " }
    
    if ($status -eq "") { $status = "None" }
    
    Write-Host "$($county.Name): $status" -ForegroundColor Gray
}

Write-Host "... (showing first 10 counties)" -ForegroundColor DarkGray
Write-Host ""

# Check for log file
$logFile = Get-ChildItem -Path "C:\Users\gsima\Documents\MyProject\ConcordBroker" -Filter "florida_revenue_agent.log" -ErrorAction SilentlyContinue
if ($logFile) {
    Write-Host "Latest log entries:" -ForegroundColor Yellow
    Write-Host "==================" -ForegroundColor Yellow
    Get-Content $logFile.FullName -Tail 5
}

Write-Host ""
Write-Host "Press any key to refresh..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")