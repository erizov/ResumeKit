$Host.UI.RawUI.WindowTitle = 'ResumeKit - Backend & Frontend Logs'
$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host '[OK] ResumeKit is running!' -ForegroundColor Green
Write-Host '   Backend:  http://localhost:8000' -ForegroundColor White
Write-Host '   Frontend: http://localhost:5173' -ForegroundColor White
Write-Host '   API Docs: http://localhost:8000/docs' -ForegroundColor White
Write-Host ''
Write-Host '[INFO] All logs appear below:' -ForegroundColor Cyan
Write-Host '   [Backend]  - Backend logs' -ForegroundColor Gray
Write-Host '   [Frontend] - Frontend logs' -ForegroundColor Gray
Write-Host '   Press Ctrl+C to stop all services' -ForegroundColor Gray
Write-Host ''
Write-Host ('=' * 60) -ForegroundColor DarkGray
Write-Host ''

# Start backend as background job
Set-Location 'E:\Python\FastAPI\ResumeKit'
$backendJob = Start-Job -ScriptBlock {
    Set-Location 'E:\Python\FastAPI\ResumeKit'
    $env:PYTHONUNBUFFERED = '1'
    python -u -m uvicorn app.main:app --reload 2>&1
}

# Monitor backend job and display output
$monitorBackend = {
    param($JobId)
    while ($true) {
        $output = Receive-Job -Id $JobId -ErrorAction SilentlyContinue
        if ($output) {
            foreach ($line in $output) {
                if ($line) {
                    $timestamp = Get-Date -Format 'HH:mm:ss'
                    Write-Host "[Backend] [$timestamp] $line"
                }
            }
        }
        Start-Sleep -Milliseconds 300
    }
}

# Start backend monitor in background thread
if (Get-Command Start-ThreadJob -ErrorAction SilentlyContinue) {
    $monitorJob = Start-ThreadJob -ScriptBlock $monitorBackend -ArgumentList $backendJob.Id
} else {
    $monitorJob = Start-Job -ScriptBlock $monitorBackend -ArgumentList $backendJob.Id
}

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Start frontend in foreground (will block until Ctrl+C)
try {
    Set-Location 'E:\Python\FastAPI\ResumeKit\frontend'
    npm run dev 2>&1 | ForEach-Object {
        $timestamp = Get-Date -Format 'HH:mm:ss'
        Write-Host "[Frontend] [$timestamp] $_"
    }
} finally {
    # Cleanup
    Write-Host ''
    Write-Host 'Stopping services...' -ForegroundColor Yellow
    
    # Stop monitor job
    if ($monitorJob) {
        Stop-Job -Id $monitorJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $monitorJob.Id -ErrorAction SilentlyContinue
    }
    
    # Stop backend job
    if ($backendJob) {
        Stop-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    }
    
    # Kill any remaining processes
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue).CommandLine
            $cmdLine -like '*uvicorn*'
        } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Get-Process node -ErrorAction SilentlyContinue | Where-Object {
        try {
            $conn = Get-NetTCPConnection -OwningProcess $_.Id -LocalPort 5173 -ErrorAction SilentlyContinue
            $conn -ne $null
        } catch { $false }
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host 'All services stopped' -ForegroundColor Green
}