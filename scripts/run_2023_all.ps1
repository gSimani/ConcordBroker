# Runs 2023 NAL, SDF, and NAP uploads in sequence, optimized for Supabase (8GB RAM, 2 cores).
# Usage examples:
#   pwsh -File scripts/run_2023_all.ps1
#   pwsh -File scripts/run_2023_all.ps1 -County GILCHRIST -BatchSize 800
#   pwsh -File scripts/run_2023_all.ps1 -Year 2023

param(
  [int]$Year = 2023,
  [int]$BatchSize = 1000,
  [string]$County,
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

# Environment tuning for Python + Postgres client
$env:PYTHONPATH = (Get-Location).Path
$env:PYTHONUTF8 = '1'
# Favor generous memory/timeouts for batch upserts on 2 cores
$env:PGOPTIONS = '-c statement_timeout=0 -c lock_timeout=0 -c maintenance_work_mem=512MB -c work_mem=128MB'

if (-not $env:DATABASE_URL) {
  Write-Host "[NOTE] DATABASE_URL is not set; scripts will use integrator defaults unless SUPABASE_* env vars are provided." -ForegroundColor Yellow
}

# Folder sets (precedence-aware order)
$NAL = @(
  "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory\NALhistory\${Year}P",
  "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory\NALhistory\${Year}S",
  "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory\NALhistory\${Year}F"
)
$SDF = @(
  "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory\SDFhistory\${Year}P",
  "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory\SDFhistory\${Year}F",
  "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory\SDFhistory\${Year}S"
)
$NAP = @(
  "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory\NAPhistory\${Year}P",
  "C:\Users\gsima\Documents\MyProject\HOTELS\AAAdatabasehistory\NAPhistory\${Year}F"
)

Write-Header "Starting 2023 uploads (Year=$Year, BatchSize=$BatchSize, County=$County, Datasets=$Datasets)"

# Resolve dataset includes from comma list
$dsSet = @{}
foreach ($d in $Datasets.Split(',') | ForEach-Object { $_.Trim().ToUpper() }) {
  if ($d) { $dsSet[$d] = $true }
}
$IncludeNAL = $dsSet.ContainsKey('NAL')
$IncludeSDF = $dsSet.ContainsKey('SDF')
$IncludeNAP = $dsSet.ContainsKey('NAP')

# NAL (P -> S -> F) so Final wins
if ($IncludeNAL) {
  Write-Header "NAL: P -> S -> F"
  $nalArgs = @('--year', $Year, '--folders') + $NAL + @('--batch-size', $BatchSize)
  if ($EmitProgress) { $nalArgs += @('--progress') }
  if ($County) { $nalArgs += @('--county', $County) }
  Invoke-Step 'python' (@('scripts\upload_old_nal_supabase.py') + $nalArgs)
} else { Write-Host "[SKIP] NAL disabled" -ForegroundColor DarkYellow }

# SDF (P -> F -> S), strong dedupe key by default
if ($IncludeSDF) {
  Write-Header "SDF: P -> F -> S"
  $sdfArgs = @('--year', $Year, '--folders') + $SDF + @('--batch-size', $BatchSize)
  if ($EmitProgress) { $sdfArgs += @('--progress') }
  if ($County) { $sdfArgs += @('--county', $County) }
  Invoke-Step 'python' (@('scripts\upload_old_sdf_supabase.py') + $sdfArgs)
} else { Write-Host "[SKIP] SDF disabled" -ForegroundColor DarkYellow }

# NAP (P -> F)
if ($IncludeNAP) {
  Write-Header "NAP: P -> F"
  $napArgs = @('--year', $Year, '--folders') + $NAP + @('--batch-size', $BatchSize)
  if ($EmitProgress) { $napArgs += @('--progress') }
  if ($County) { $napArgs += @('--county', $County) }
  Invoke-Step 'python' (@('scripts\upload_old_nap_supabase.py') + $napArgs)
} else { Write-Host "[SKIP] NAP disabled" -ForegroundColor DarkYellow }

Write-Header "All uploads complete"
Write-Host "Quick SQL checks (run in Supabase):" -ForegroundColor Green
Write-Host "- NAL counts (2023): SELECT county, COUNT(*) FROM public.florida_parcels WHERE year=$Year GROUP BY county ORDER BY county;"
Write-Host "- SDF dups (expect 0): SELECT COUNT(*) FROM (SELECT parcel_id, county, sale_date, sale_price, or_book, or_page, clerk_no, COUNT(*) c FROM public.property_sales_history GROUP BY 1,2,3,4,5,6,7 HAVING COUNT(*)>1) t;"
Write-Host "- Optional MV: CREATE MATERIALIZED VIEW IF NOT EXISTS public.parcel_current_owner AS SELECT DISTINCT ON (county, parcel_id) parcel_id, county, year, owner_name, owner_addr1, owner_city, owner_state, owner_zip, phy_addr1, phy_city, phy_state, phy_zipcd FROM public.florida_parcels ORDER BY county, parcel_id, year DESC;"
Write-Host "  Then: REFRESH MATERIALIZED VIEW CONCURRENTLY public.parcel_current_owner;"
