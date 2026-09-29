# Packages Python backend + venv for Tauri installer (Windows).
# Output is OUTSIDE frontend/ so Next.js build does not scan thousands of venv files.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$pack = Join-Path $root "build\backend-pack"

Write-Host "Packing backend to $pack" -ForegroundColor Cyan
if (Test-Path $pack) { Remove-Item -Recurse -Force $pack }
New-Item -ItemType Directory -Force -Path $pack | Out-Null

Copy-Item -Recurse (Join-Path $root "backend\app") (Join-Path $pack "app")
Copy-Item (Join-Path $root "backend\requirements.txt") $pack

Write-Host "Creating venv (Python 3.12)..."
py -3.12 -m venv (Join-Path $pack ".venv")
& (Join-Path $pack ".venv\Scripts\python.exe") -m pip install -U pip -q
& (Join-Path $pack ".venv\Scripts\pip.exe") install -r (Join-Path $pack "requirements.txt") -q

# Remove stale pack inside frontend if present (legacy path)
$legacy = Join-Path $root "frontend\src-tauri\resources\backend-pack"
if (Test-Path $legacy) {
  Write-Host "Removing legacy pack at $legacy"
  Remove-Item -Recurse -Force $legacy
}

Write-Host "Backend pack ready." -ForegroundColor Green
