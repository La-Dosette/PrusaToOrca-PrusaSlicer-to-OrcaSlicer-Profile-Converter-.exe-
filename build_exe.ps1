$ErrorActionPreference = "Stop"

$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

& $python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name "PrusaToOrca" `
  --icon "logo.ico" `
  --collect-all "tkinterdnd2" `
  --add-data "assets;assets" `
  --add-data "logo.png;." `
  --add-data "logo.ico;." `
  "app.py"

Write-Host "Built dist\PrusaToOrca.exe"

$releaseDir = Join-Path $PSScriptRoot "release"
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
Copy-Item -Force (Join-Path $PSScriptRoot "dist\PrusaToOrca.exe") (Join-Path $releaseDir "PrusaToOrca-v0.2.0.exe")
if (Test-Path (Join-Path $PSScriptRoot "CHANGELOG.md")) {
  Copy-Item -Force (Join-Path $PSScriptRoot "CHANGELOG.md") (Join-Path $releaseDir "CHANGELOG.md")
}

Write-Host "Prepared release\PrusaToOrca-v0.2.0.exe"
