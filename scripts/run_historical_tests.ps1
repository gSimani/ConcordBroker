#!/usr/bin/env pwsh
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
$reportDir = Join-Path $root '.agent\reports'
if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Path $reportDir -Force | Out-Null }
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'

function Run-Step {
  param(
    [string]$name,
    [string[]]$argList,
    [string]$outfile
  )
  Write-Host ("[RUN] {0}" -f $name)
  $outPath = Join-Path $reportDir $outfile
  $errPath = [IO.Path]::ChangeExtension($outPath, '.err.txt')
  try {
    $p = Start-Process -FilePath python -ArgumentList $argList -NoNewWindow -Wait -PassThru -RedirectStandardOutput $outPath -RedirectStandardError $errPath
    Write-Host ("  ExitCode: {0}" -f $p.ExitCode)
    if ((Get-Item $outPath).Length -gt 0) { Write-Host ("  Wrote stdout -> {0}" -f $outPath) }
    if ((Get-Item $errPath).Length -gt 0) { Write-Host ("  Wrote stderr -> {0}" -f $errPath) }
  } catch {
    Write-Host ("  ERROR: {0}" -f $_)
  }
}

# A) Combined NAL+SDF 2025 (limit 500)
Run-Step -name 'Combined NAL+SDF 2025 (limit 500)' -argList @('-u',"$root/scripts/integrate_historical_data_psycopg2.py",'--county','GILCHRIST','--year','2025','--types','NAL,SDF','--batch-size','100','--limit','500') -outfile ("{0}_combo_2025.out.txt" -f $ts)

# B) NAP 2025 (limit 300)
Run-Step -name 'NAP 2025 (limit 300)' -argList @('-u',"$root/scripts/integrate_historical_data_psycopg2.py",'--county','GILCHRIST','--year','2025','--types','NAP','--batch-size','100','--limit','300') -outfile ("{0}_nap_2025.out.txt" -f $ts)

# C) Combined NAL+SDF 2024 (limit 500)
Run-Step -name 'Combined NAL+SDF 2024 (limit 500)' -argList @('-u',"$root/scripts/integrate_historical_data_psycopg2.py",'--county','GILCHRIST','--year','2024','--types','NAL,SDF','--batch-size','100','--limit','500') -outfile ("{0}_combo_2024.out.txt" -f $ts)

Write-Host "Done. Reports in: $reportDir"
