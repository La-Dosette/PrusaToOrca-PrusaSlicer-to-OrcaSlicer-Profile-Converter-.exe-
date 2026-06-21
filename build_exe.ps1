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
