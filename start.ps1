# Start ResumeKit Backend and Frontend with Logging
# Usage: .\start.ps1
# This version opens separate PowerShell windows with prefixed logs

Write-Host "[Start] Starting ResumeKit services with logging..." -ForegroundColor Green

# Check if backend is already running
$backendRunning = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($backendRunning) {
    Write-Host "[Start] [Backend] ⚠️  Already running on port 8000" -ForegroundColor Yellow
} else {
    Write-Host "[Start] [Backend] Starting on http://localhost:8000..." -ForegroundColor Cyan
    
    # Create backend start script with logging
    $backendScript = @"
`$Host.UI.RawUI.WindowTitle = 'ResumeKit Backend - Port 8000'
`$ErrorActionPreference = 'Continue'
Write-Host '[Backend] Starting ResumeKit Backend...' -ForegroundColor Cyan
Write-Host '[Backend] API will be available at http://localhost:8000' -ForegroundColor Green
Write-Host '[Backend] API Docs: http://localhost:8000/docs' -ForegroundColor Green
Write-Host '[Backend] Press Ctrl+C to stop' -ForegroundColor Gray
Write-Host ''
python -m uvicorn app.main:app --reload 2>&1 | ForEach-Object {
    `$timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[Backend] [`$timestamp] `$_"
}
"@
    
    $backendScript | Out-File -FilePath ".backend-start.ps1" -Encoding UTF8
    $backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-File", ".backend-start.ps1" -PassThru
    $backendProcess.Id | Out-File -FilePath ".backend.pid" -Encoding ASCII
    Write-Host "[Start] [Backend] ✅ Started in new window (PID: $($backendProcess.Id))" -ForegroundColor Green
}

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Check if frontend is already running
$frontendRunning = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($frontendRunning) {
    Write-Host "[Start] [Frontend] ⚠️  Already running on port 5173" -ForegroundColor Yellow
} else {
    Write-Host "[Start] [Frontend] Starting on http://localhost:5173..." -ForegroundColor Cyan
    
    # Create frontend start script with logging
    $frontendPath = (Resolve-Path "frontend").Path
    $frontendScript = @"
`$Host.UI.RawUI.WindowTitle = 'ResumeKit Frontend - Port 5173'
`$ErrorActionPreference = 'Continue'
Set-Location '$frontendPath'
Write-Host '[Frontend] Starting ResumeKit Frontend...' -ForegroundColor Cyan
Write-Host '[Frontend] Working directory: ' -NoNewline; Write-Host `$PWD -ForegroundColor Gray
Write-Host '[Frontend] Frontend will be available at http://localhost:5173' -ForegroundColor Green
Write-Host '[Frontend] Press Ctrl+C to stop' -ForegroundColor Gray
Write-Host ''
npm run dev 2>&1 | ForEach-Object {
    `$timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[Frontend] [`$timestamp] `$_"
}
"@
    
    $frontendScript | Out-File -FilePath ".frontend-start.ps1" -Encoding UTF8
    $frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-File", ".frontend-start.ps1" -PassThru
    $frontendProcess.Id | Out-File -FilePath ".frontend.pid" -Encoding ASCII
    Write-Host "[Start] [Frontend] ✅ Started in new window (PID: $($frontendProcess.Id))" -ForegroundColor Green
}

Write-Host "`n[Start] 🎉 ResumeKit is running!" -ForegroundColor Green
Write-Host "[Start]    Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "[Start]    Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "[Start]    API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n[Start] 📋 Logs are displayed in separate PowerShell windows" -ForegroundColor Cyan
Write-Host "[Start]    Each window shows prefixed logs: [Backend] or [Frontend]" -ForegroundColor Gray
Write-Host "[Start]    Each log line includes timestamp: [HH:mm:ss]" -ForegroundColor Gray
Write-Host "[Start]    Close those windows or run .\stop.ps1 to stop services" -ForegroundColor Gray
