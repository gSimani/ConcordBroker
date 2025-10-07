Param(
  [string]$ApiProxy = "https://api.concordbroker.com",
  [string]$OutDir = "apps/web/live-dist",
  [switch]$RunPythonVerify = $true,
  [switch]$RunTsE2E = $false,
  [switch]$Quiet = $false
)

function Write-Info($msg) { if (-not $Quiet) { Write-Host "[restore] $msg" } }

# 1) Download production snapshot if missing
if (-not (Test-Path -Path (Join-Path $OutDir 'index.html'))) {
  Write-Info "Downloading production snapshot to $OutDir ..."
  python scripts/download_vercel_assets.py $OutDir
}

# 2) Discover Railway public URL if token provided and no file exists
if (-not (Test-Path -Path 'RAILWAY_PUBLIC_URL.txt') -and $env:RAILWAY_TOKEN) {
  Write-Info "Discovering Railway public URL with RAILWAY_TOKEN ..."
  node scripts/get-railway-url.cjs 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb > RAILWAY_PUBLIC_URL.txt 2>$null
}

# 3) Set API proxy preference: RAILWAY_PUBLIC_URL.txt overrides param
if (Test-Path -Path 'RAILWAY_PUBLIC_URL.txt') {
  $ApiProxy = Get-Content -Raw 'RAILWAY_PUBLIC_URL.txt'
  Write-Info "Using API proxy from file: $ApiProxy"
} else {
  Write-Info "Using API proxy param: $ApiProxy"
}

# 4) Start local server
Write-Info "Starting local server on 5173 ..."
$env:DIST_DIR = $OutDir
$env:API_PROXY = $ApiProxy
Start-Process -NoNewWindow -FilePath node -ArgumentList "scripts/serve-dist.cjs"
Start-Sleep -Seconds 2

# 5) Optional verifications
if ($RunPythonVerify) {
  Write-Info "Running Python Playwright verification ..."
  $env:API_PROXY = $ApiProxy
  python scripts/verify_local_properties.py
}

if ($RunTsE2E) {
  Write-Info "Running TS Playwright e2e ..."
  Push-Location apps/web
  if (-not (Test-Path -Path 'node_modules')) { npm i }
  $env:DIST_DIR = (Resolve-Path "..\..\$OutDir").Path
  $env:API_PROXY = $ApiProxy
  npx playwright install --with-deps chromium
  npm run e2e:local
  Pop-Location
}

Write-Info "Local restore complete. Open http://localhost:5173/properties"

