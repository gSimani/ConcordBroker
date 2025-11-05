#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$outDir = Join-Path $PSScriptRoot '..' | Join-Path -ChildPath 'docs'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$outFile = Join-Path $outDir 'CHANGES_PER_COMMIT.md'

$count = 15
$hashes = git -C (Join-Path $PSScriptRoot '..') log --pretty=format:"%h|%an|%ad|%s" --date=short -n $count

"# Per-Commit Change Summary (last $count commits)" | Set-Content -Path $outFile -Encoding UTF8
"Generated: $(Get-Date -Format s)" | Add-Content -Path $outFile -Encoding UTF8
"" | Add-Content -Path $outFile -Encoding UTF8

foreach($line in $hashes){
  $parts = $line -split '\|',4
  $h = $parts[0]
  $an = $parts[1]
  $ad = $parts[2]
  $subj = $parts[3]
  "## $h — $subj ($ad)" | Add-Content -Path $outFile -Encoding UTF8
  "Author: $an" | Add-Content -Path $outFile -Encoding UTF8
  "" | Add-Content -Path $outFile -Encoding UTF8
  $show = git -C (Join-Path $PSScriptRoot '..') show --name-status --pretty=format: $h
  "````
$show
````" | Add-Content -Path $outFile -Encoding UTF8
  "" | Add-Content -Path $outFile -Encoding UTF8
}

Write-Host "Wrote: $outFile"
