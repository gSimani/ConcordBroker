# Check Sunbiz Download Statistics
$basePath = "C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE"

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "SUNBIZ DOWNLOAD STATISTICS" -ForegroundColor Yellow
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

# Get all files
$allFiles = Get-ChildItem -Path $basePath -Recurse -File
$totalFiles = $allFiles.Count
$totalSize = ($allFiles | Measure-Object -Property Length -Sum).Sum
$totalSizeMB = [math]::Round($totalSize/1MB, 2)
$totalSizeGB = [math]::Round($totalSize/1GB, 2)

Write-Host "Overall Statistics:" -ForegroundColor Green
Write-Host "  Total Files Downloaded: $totalFiles"
Write-Host "  Total Size: $totalSizeGB GB ($totalSizeMB MB)"
Write-Host ""

# Get folder statistics
Write-Host "Folder Breakdown:" -ForegroundColor Green
$folders = Get-ChildItem -Path "$basePath\doc" -Directory
foreach ($folder in $folders) {
    $folderFiles = Get-ChildItem -Path $folder.FullName -Recurse -File -ErrorAction SilentlyContinue
    $folderCount = $folderFiles.Count
    $folderSize = ($folderFiles | Measure-Object -Property Length -Sum).Sum
    $folderSizeMB = [math]::Round($folderSize/1MB, 2)
    
    Write-Host "  $($folder.Name): $folderCount files ($folderSizeMB MB)"
}

Write-Host ""

# Get file type statistics
Write-Host "File Types:" -ForegroundColor Green
$fileTypes = $allFiles | Group-Object Extension | Sort-Object Count -Descending
foreach ($type in $fileTypes) {
    Write-Host "  $($type.Name): $($type.Count) files"
}

Write-Host ""

# Get latest downloads
Write-Host "Latest Downloads (Last 10):" -ForegroundColor Green
$latestFiles = $allFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 10
foreach ($file in $latestFiles) {
    Write-Host "  $($file.Name) - $($file.LastWriteTime)"
}

Write-Host ""
Write-Host "="*60 -ForegroundColor Cyan