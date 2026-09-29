# Uruchamia backend i frontend DataForge Analytics (Windows)
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "DataForge Analytics — dev" -ForegroundColor Cyan
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host ""

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backend'; if (-not (Test-Path .venv)) { py -3.12 -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt }; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontend'; npm run dev"
