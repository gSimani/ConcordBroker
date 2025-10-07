# Florida Property Data Downloader
# Downloads all property data files (NAL, NAP, NAV, SDF) for all Florida counties

$baseUrl = "https://floridarevenue.com/property/dataportal/DataPortal_Files/"
$outputBase = "C:\TEMP\DATABASE PROPERTY APP"

# All Florida Counties with their codes
$counties = @{
    "01" = "ALACHUA"
    "02" = "BAKER"
    "03" = "BAY"
    "04" = "BRADFORD"
    "05" = "BREVARD"
    "06" = "BROWARD"
    "07" = "CALHOUN"
    "08" = "CHARLOTTE"
    "09" = "CITRUS"
    "10" = "CLAY"
    "11" = "COLLIER"
    "12" = "COLUMBIA"
    "13" = "MIAMI-DADE"
    "14" = "DESOTO"
    "15" = "DIXIE"
    "16" = "DUVAL"
    "17" = "ESCAMBIA"
    "18" = "FLAGLER"
    "19" = "FRANKLIN"
    "20" = "GADSDEN"
    "21" = "GILCHRIST"
    "22" = "GLADES"
    "23" = "GULF"
    "24" = "HAMILTON"
    "25" = "HARDEE"
    "26" = "HENDRY"
    "27" = "HERNANDO"
    "28" = "HIGHLANDS"
    "29" = "HILLSBOROUGH"
    "30" = "HOLMES"
    "31" = "INDIAN_RIVER"
    "32" = "JACKSON"
    "33" = "JEFFERSON"
    "34" = "LAFAYETTE"
    "35" = "LAKE"
    "36" = "LEE"
    "37" = "LEON"
    "38" = "LEVY"
    "39" = "LIBERTY"
    "40" = "MADISON"
    "41" = "MANATEE"
    "42" = "MARION"
    "43" = "MARTIN"
    "44" = "MONROE"
    "45" = "NASSAU"
    "46" = "OKALOOSA"
    "47" = "OKEECHOBEE"
    "48" = "ORANGE"
    "49" = "OSCEOLA"
    "50" = "PALM_BEACH"
    "51" = "PASCO"
    "52" = "PINELLAS"
    "53" = "POLK"
    "54" = "PUTNAM"
    "55" = "ST_JOHNS"
    "56" = "ST_LUCIE"
    "57" = "SANTA_ROSA"
    "58" = "SARASOTA"
    "59" = "SEMINOLE"
    "60" = "SUMTER"
    "61" = "SUWANNEE"
    "62" = "TAYLOR"
    "63" = "UNION"
    "64" = "VOLUSIA"
    "65" = "WAKULLA"
    "66" = "WALTON"
    "67" = "WASHINGTON"
}

# File types to download
$fileTypes = @("NAL", "NAP", "NAV", "SDF")

# Priority counties (download these first)
$priorityCounties = @("06", "13", "50", "48", "52", "29", "16", "36", "11", "58")

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FLORIDA PROPERTY DATA DOWNLOADER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create base directory if it doesn't exist
if (!(Test-Path $outputBase)) {
    New-Item -ItemType Directory -Path $outputBase -Force | Out-Null
    Write-Host "Created base directory: $outputBase" -ForegroundColor Green
}

# Function to download a file
function Download-PropertyFile {
    param(
        [string]$countyCode,
        [string]$countyName,
        [string]$fileType,
        [string]$year = "2025"
    )

    # Create county directory structure
    $countyPath = Join-Path $outputBase $countyName
    $typePath = Join-Path $countyPath $fileType

    if (!(Test-Path $typePath)) {
        New-Item -ItemType Directory -Path $typePath -Force | Out-Null
    }

    # Construct file name and URL
    $fileName = "${countyCode}_${fileType}_${year}.txt"
    $downloadUrl = "${baseUrl}${year}/${fileName}"
    $outputFile = Join-Path $typePath "${countyName}_${fileType}_${year}.csv"

    # Check if file already exists
    if (Test-Path $outputFile) {
        Write-Host "  [SKIP] $outputFile already exists" -ForegroundColor Yellow
        return $true
    }

    try {
        Write-Host "  Downloading: $fileName..." -NoNewline

        # Download with progress suppressed for cleaner output
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $downloadUrl -OutFile $outputFile -ErrorAction Stop
        $ProgressPreference = 'Continue'

        # Check file size
        $fileSize = (Get-Item $outputFile).Length / 1MB
        Write-Host " OK ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host " FAILED" -ForegroundColor Red
        # Remove empty file if created
        if (Test-Path $outputFile) {
            Remove-Item $outputFile -Force
        }
        return $false
    }
}

# Track statistics
$totalFiles = 0
$successCount = 0
$failCount = 0
$startTime = Get-Date

# Download priority counties first
Write-Host "`nDOWNLOADING PRIORITY COUNTIES (Major metros):" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow

foreach ($code in $priorityCounties) {
    $countyName = $counties[$code]
    Write-Host "`n[$code] $countyName" -ForegroundColor Cyan

    foreach ($type in $fileTypes) {
        $totalFiles++
        if (Download-PropertyFile -countyCode $code -countyName $countyName -fileType $type) {
            $successCount++
        } else {
            $failCount++
        }
    }
}

# Download remaining counties
Write-Host "`n`nDOWNLOADING REMAINING COUNTIES:" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow

foreach ($county in $counties.GetEnumerator() | Sort-Object Name) {
    # Skip if already downloaded in priority
    if ($priorityCounties -contains $county.Name) {
        continue
    }

    Write-Host "`n[$($county.Name)] $($county.Value)" -ForegroundColor Cyan

    foreach ($type in $fileTypes) {
        $totalFiles++
        if (Download-PropertyFile -countyCode $county.Name -countyName $county.Value -fileType $type) {
            $successCount++
        } else {
            $failCount++
        }
    }
}

# Calculate duration
$endTime = Get-Date
$duration = $endTime - $startTime

# Summary report
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "DOWNLOAD SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Files Attempted: $totalFiles" -ForegroundColor White
Write-Host "Successfully Downloaded: $successCount" -ForegroundColor Green
Write-Host "Failed Downloads: $failCount" -ForegroundColor Red
Write-Host "Duration: $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor White
Write-Host "Output Directory: $outputBase" -ForegroundColor White

# List counties with complete data
Write-Host "`nCOUNTIES WITH COMPLETE DATA:" -ForegroundColor Green
foreach ($county in $counties.GetEnumerator() | Sort-Object Value) {
    $countyPath = Join-Path $outputBase $county.Value
    if (Test-Path $countyPath) {
        $fileCount = (Get-ChildItem -Path $countyPath -Recurse -Filter "*.csv" | Measure-Object).Count
        if ($fileCount -eq 4) {
            Write-Host "  ✓ $($county.Value) (All 4 files)" -ForegroundColor Green
        }
    }
}

Write-Host "`nDownload complete!" -ForegroundColor Cyan
Write-Host "Next step: Run import-florida-sales.js to import data into Supabase" -ForegroundColor Yellow