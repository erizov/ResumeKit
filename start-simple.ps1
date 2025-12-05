# Start ResumeKit Backend and Frontend (Simple version - logs in same terminal)
# Usage: .\start-simple.ps1
# This version runs both services in the same terminal with prefixed output

Write-Host "Starting ResumeKit services..." -ForegroundColor Green
Write-Host "Logs will appear below with [Backend] and [Frontend] prefixes`n" -ForegroundColor Cyan

# Check if services are already running
$backendRunning = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$frontendRunning = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue

if ($backendRunning) {
    Write-Host "[Backend] ⚠️  Already running on port 8000" -ForegroundColor Yellow
} else {
    Write-Host "[Backend] Starting on http://localhost:8000..." -ForegroundColor Cyan
}

if ($frontendRunning) {
    Write-Host "[Frontend] ⚠️  Already running on port 5173" -ForegroundColor Yellow
} else {
    Write-Host "[Frontend] Starting on http://localhost:5173..." -ForegroundColor Cyan
}

Write-Host "`n🎉 ResumeKit is running!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n📋 To view logs, run in separate terminals:" -ForegroundColor Cyan
Write-Host "   Backend:  python -m uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "   Frontend: cd frontend && npm run dev" -ForegroundColor Gray
Write-Host "`nOr use: .\start-logs.ps1 for separate log windows" -ForegroundColor Gray

# Start backend if not running
if (-not $backendRunning) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '[Backend]' -ForegroundColor Cyan; python -m uvicorn app.main:app --reload 2>&1 | ForEach-Object { Write-Host `"[Backend] `$_`" }" -WindowStyle Minimized
}

# Start frontend if not running
if (-not $frontendRunning) {
    Start-Sleep -Seconds 2
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; Write-Host '[Frontend]' -ForegroundColor Cyan; npm run dev 2>&1 | ForEach-Object { Write-Host `"[Frontend] `$_`" }" -WindowStyle Minimized
}

