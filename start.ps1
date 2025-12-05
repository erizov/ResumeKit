# Start ResumeKit Backend and Frontend with Logging in Separate Window
# Usage: .\start.ps1

Write-Host "[Start] Starting ResumeKit services..." -ForegroundColor Cyan

# Check if backend is running
$backendRunning = $false
try {
    $backendConn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($backendConn) {
        $processId = $backendConn.OwningProcess
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            $backendRunning = $true
        }
    }
} catch { }

if ($backendRunning) {
    Write-Host "[Start] [Backend] Already running on port 8000" -ForegroundColor Yellow
} else {
    Write-Host "[Start] [Backend] Starting on http://localhost:8000..." -ForegroundColor Cyan
}

# Check if frontend is running
$frontendRunning = $false
try {
    $frontendConn = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($frontendConn) {
        $processId = $frontendConn.OwningProcess
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            $frontendRunning = $true
        }
    }
} catch { }

if ($frontendRunning) {
    Write-Host "[Start] [Frontend] Already running on port 5173" -ForegroundColor Yellow
} else {
    Write-Host "[Start] [Frontend] Starting on http://localhost:5173..." -ForegroundColor Cyan
}

# If both are already running, exit
if ($backendRunning -and $frontendRunning) {
    Write-Host "[Start] ✅ All services are already running" -ForegroundColor Green
    exit 0
}

# Get absolute paths
$projectPath = $PWD.Path
$frontendPath = Join-Path $projectPath "frontend"

# Check if npm is available (only if frontend needs to start)
if (-not $frontendRunning) {
    $npmCheck = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCheck) {
        Write-Host "[Start] [Frontend] ❌ npm not found in PATH!" -ForegroundColor Red
        exit 1
    }
}

# Create a script that runs both services with combined logs
$logScript = @'
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

# Start backend as background job (if not already running)
$backendJob = $null
$backendRunning = $false
try {
    $backendConn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($backendConn) {
        $processId = $backendConn.OwningProcess
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            $backendRunning = $true
            Write-Host '[Backend] Already running on port 8000' -ForegroundColor Yellow
        }
    }
} catch { }

if (-not $backendRunning) {
    Set-Location '@projectPath@'
    $backendJob = Start-Job -ScriptBlock {
        Set-Location '@projectPath@'
        $env:PYTHONUNBUFFERED = '1'
        python -u -m uvicorn app.main:app --reload 2>&1
    }
    Write-Host '[Backend] Starting on http://localhost:8000...' -ForegroundColor Cyan
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

# Start backend monitor if we have a job
if ($backendJob) {
    if (Get-Command Start-ThreadJob -ErrorAction SilentlyContinue) {
        $monitorJob = Start-ThreadJob -ScriptBlock $monitorBackend -ArgumentList $backendJob.Id
    } else {
        $monitorJob = Start-Job -ScriptBlock $monitorBackend -ArgumentList $backendJob.Id
    }
} else {
    $monitorJob = $null
}

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Start frontend in foreground (will block until Ctrl+C)
try {
    $frontendRunning = $false
    try {
        $frontendConn = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
        if ($frontendConn) {
            $processId = $frontendConn.OwningProcess
            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($proc) {
                $frontendRunning = $true
                Write-Host '[Frontend] Already running on port 5173' -ForegroundColor Yellow
            }
        }
    } catch { }

    if (-not $frontendRunning) {
        Set-Location '@frontendPath@'
        npm run dev 2>&1 | ForEach-Object {
            $timestamp = Get-Date -Format 'HH:mm:ss'
            Write-Host "[Frontend] [$timestamp] $_"
        }
    } else {
        # If frontend is already running, just monitor backend
        Write-Host ''
        Write-Host 'Monitoring backend logs...' -ForegroundColor Cyan
        Write-Host ('=' * 60) -ForegroundColor DarkGray
        Write-Host ''
        
        if ($backendJob) {
            while ($true) {
                $output = Receive-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
                if ($output) {
                    foreach ($line in $output) {
                        if ($line) {
                            $timestamp = Get-Date -Format 'HH:mm:ss'
                            Write-Host "[Backend] [$timestamp] $line"
                        }
                    }
                }
                Start-Sleep -Milliseconds 500
            }
        }
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
'@

# Replace placeholders with actual paths
$logScript = $logScript -replace '@projectPath@', $projectPath
$logScript = $logScript -replace '@frontendPath@', $frontendPath

# Save the log script to a temporary file with UTF-8 BOM for Windows compatibility
$logScriptPath = Join-Path $projectPath ".start-logs.ps1"
$utf8WithBom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($logScriptPath, $logScript, $utf8WithBom)

# Start the log window
$logProcess = Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$logScriptPath`"" -WindowStyle Normal -PassThru

if ($logProcess) {
    Write-Host "[Start] ✅ Services started in log window (PID: $($logProcess.Id))" -ForegroundColor Green
    Write-Host "[Start]    Logs are displayed in the separate window" -ForegroundColor Gray
    Write-Host "[Start]    This terminal will exit now" -ForegroundColor Gray
    Start-Sleep -Milliseconds 500  # Give window time to appear
} else {
    Write-Host "[Start] ❌ Failed to start log window" -ForegroundColor Red
    exit 1
}
