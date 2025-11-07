# Runs NAL, SDF, and NAP uploads for a year range, optimized for Supabase (8GB RAM, 2 cores).
#
# Usage examples:
#   pwsh -File scripts/run_years_all.ps1                # 2009..2023, default root
#   pwsh -File scripts/run_years_all.ps1 -StartYear 2009 -EndYear 2023 -County GILCHRIST -BatchSize 800
#   pwsh -File scripts/run_years_all.ps1 -Root "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory"
#
param(
  [int]$StartYear = 2009,
  [int]$EndYear   = 2023,
  [int]$BatchSize = 1000,
  [string]$County,
  [string]$Root = "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory",
  [string]$Datasets = 'NAL,SDF,NAP',
  [switch]$EmitProgress
)

$ErrorActionPreference = 'Stop'

function Write-Header($text) {
  Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Invoke-Step($cmd, $args) {
  Write-Host "`n> $cmd $($args -join ' ')" -ForegroundColor Gray
  & $cmd @args
  if ($LASTEXITCODE -ne 0) {
    throw "Step failed with exit code $LASTEXITCODE: $cmd $($args -join ' ')"
  }
}

function Existing-Folders([string[]]$folders) {
  $existing = @()
  foreach ($f in $folders) {
    if (Test-Path $f) { $existing += $f }
  }
  return $existing
}

# Environment tuning for Python + Postgres client
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONUTF8 = '1'
$env:PGOPTIONS = '-c statement_timeout=0 -c lock_timeout=0 -c maintenance_work_mem=512MB -c work_mem=128MB'

if (-not $env:DATABASE_URL) {
  Write-Host "[NOTE] DATABASE_URL is not set; scripts will use integrator defaults unless SUPABASE_* env vars are provided." -ForegroundColor Yellow
}

Write-Header "Starting uploads ($StartYear..$EndYear, BatchSize=$BatchSize, County=$County, Datasets=$Datasets)"

# Resolve dataset includes from comma list
$dsSet = @{}
foreach ($d in $Datasets.Split(',') | ForEach-Object { $_.Trim().ToUpper() }) {
  if ($d) { $dsSet[$d] = $true }
}
$IncludeNAL = $dsSet.ContainsKey('NAL')
$IncludeSDF = $dsSet.ContainsKey('SDF')
$IncludeNAP = $dsSet.ContainsKey('NAP')

for ($y = $StartYear; $y -le $EndYear; $y++) {
  Write-Header "Year $y"

  if ($IncludeNAL) {
    Write-Header "NAL: P -> S -> F"
    $nalFolders = Existing-Folders @(
      Join-Path $Root ("NALhistory\{0}P" -f $y),
      Join-Path $Root ("NALhistory\{0}S" -f $y),
      Join-Path $Root ("NALhistory\{0}F" -f $y)
    )
    if ($nalFolders.Count -gt 0) {
      $nalArgs = @('--year', $y, '--folders') + $nalFolders + @('--batch-size', $BatchSize)
      if ($EmitProgress) { $nalArgs += @('--progress') }
      if ($County) { $nalArgs += @('--county', $County) }
      Invoke-Step 'python' (@('scripts\upload_old_nal_supabase.py') + $nalArgs)
    } else {
      Write-Host "[SKIP] NAL folders not found for $y under $Root" -ForegroundColor DarkYellow
    }
  }

  if ($IncludeSDF) {
    Write-Header "SDF: P -> F -> S"
    $sdfFolders = Existing-Folders @(
      Join-Path $Root ("SDFhistory\{0}P" -f $y),
      Join-Path $Root ("SDFhistory\{0}F" -f $y),
      Join-Path $Root ("SDFhistory\{0}S" -f $y)
    )
    if ($sdfFolders.Count -gt 0) {
      $sdfArgs = @('--year', $y, '--folders') + $sdfFolders + @('--batch-size', $BatchSize)
      if ($EmitProgress) { $sdfArgs += @('--progress') }
      if ($County) { $sdfArgs += @('--county', $County) }
      Invoke-Step 'python' (@('scripts\upload_old_sdf_supabase.py') + $sdfArgs)
    } else {
      Write-Host "[SKIP] SDF folders not found for $y under $Root" -ForegroundColor DarkYellow
    }
  }

  if ($IncludeNAP) {
    Write-Header "NAP: P -> F"
    $napFolders = Existing-Folders @(
      Join-Path $Root ("NAPhistory\{0}P" -f $y),
      Join-Path $Root ("NAPhistory\{0}F" -f $y)
    )
    if ($napFolders.Count -gt 0) {
      $napArgs = @('--year', $y, '--folders') + $napFolders + @('--batch-size', $BatchSize)
      if ($EmitProgress) { $napArgs += @('--progress') }
      if ($County) { $napArgs += @('--county', $County) }
      Invoke-Step 'python' (@('scripts\upload_old_nap_supabase.py') + $napArgs)
    } else {
      Write-Host "[SKIP] NAP folders not found for $y under $Root" -ForegroundColor DarkYellow
    }
  }
}

Write-Header "All uploads complete"
Write-Host "Quick SQL checks (run in Supabase):" -ForegroundColor Green
Write-Host "- NAL yearly counts: SELECT year, county, COUNT(*) FROM public.florida_parcels WHERE year BETWEEN $StartYear AND $EndYear GROUP BY year, county ORDER BY year, county;"
Write-Host "- SDF dups (expect 0): SELECT COUNT(*) FROM (SELECT parcel_id, county, sale_date, sale_price, or_book, or_page, clerk_no, COUNT(*) c FROM public.property_sales_history GROUP BY 1,2,3,4,5,6,7 HAVING COUNT(*)>1) t;"
Write-Host "- Optional MV: CREATE MATERIALIZED VIEW IF NOT EXISTS public.parcel_current_owner AS SELECT DISTINCT ON (county, parcel_id) parcel_id, county, year, owner_name, owner_addr1, owner_city, owner_state, owner_zip, phy_addr1, phy_city, phy_state, phy_zipcd FROM public.florida_parcels ORDER BY county, parcel_id, year DESC;"
Write-Host "  Then: REFRESH MATERIALIZED VIEW CONCURRENTLY public.parcel_current_owner;"
