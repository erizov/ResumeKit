# Start ResumeKit with separate log windows
# Usage: .\start-logs.ps1
# This version opens separate PowerShell windows for each service

Write-Host "Starting ResumeKit services in separate windows..." -ForegroundColor Green

# Check if backend is already running
$backendRunning = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($backendRunning) {
    Write-Host "[Backend] ⚠️  Already running on port 8000" -ForegroundColor Yellow
} else {
    Write-Host "[Backend] Starting in new window..." -ForegroundColor Cyan
    
    # Start backend in new window with prefix
    $backendScript = @"
`$Host.UI.RawUI.WindowTitle = 'ResumeKit Backend'
Write-Host '[Backend] Starting on http://localhost:8000...' -ForegroundColor Cyan
python -m uvicorn app.main:app --reload 2>&1 | ForEach-Object { Write-Host "[Backend] `$_" }
"@
    
    $backendScript | Out-File -FilePath ".backend-start.ps1" -Encoding UTF8
    Start-Process powershell -ArgumentList "-NoExit", "-File", ".backend-start.ps1" -WindowStyle Normal
    Start-Sleep -Seconds 1
    Write-Host "[Backend] ✅ Started in new window" -ForegroundColor Green
}

# Wait a moment
Start-Sleep -Seconds 2

# Check if frontend is already running
$frontendRunning = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($frontendRunning) {
    Write-Host "[Frontend] ⚠️  Already running on port 5173" -ForegroundColor Yellow
} else {
    Write-Host "[Frontend] Starting in new window..." -ForegroundColor Cyan
    
    # Start frontend in new window with prefix
    $frontendScript = @"
`$Host.UI.RawUI.WindowTitle = 'ResumeKit Frontend'
Set-Location frontend
Write-Host '[Frontend] Starting on http://localhost:5173...' -ForegroundColor Cyan
npm run dev 2>&1 | ForEach-Object { Write-Host "[Frontend] `$_" }
"@
    
    $frontendScript | Out-File -FilePath ".frontend-start.ps1" -Encoding UTF8
    Start-Process powershell -ArgumentList "-NoExit", "-File", ".frontend-start.ps1" -WindowStyle Normal
    Start-Sleep -Seconds 1
    Write-Host "[Frontend] ✅ Started in new window" -ForegroundColor Green
}

Write-Host "`n🎉 ResumeKit is running in separate windows!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`nLogs are displayed in separate PowerShell windows." -ForegroundColor Gray
Write-Host "Close those windows or run .\stop.ps1 to stop services." -ForegroundColor Gray

