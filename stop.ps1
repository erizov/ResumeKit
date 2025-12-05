# Stop ResumeKit Backend and Frontend
# Usage: .\stop.ps1

Write-Host "[Stop] Stopping ResumeKit services..." -ForegroundColor Yellow

# Clean up temporary start scripts
if (Test-Path ".backend-start.ps1") {
    Remove-Item ".backend-start.ps1" -ErrorAction SilentlyContinue
}
if (Test-Path ".frontend-start.ps1") {
    Remove-Item ".frontend-start.ps1" -ErrorAction SilentlyContinue
}
if (Test-Path ".backend-start.bat") {
    Remove-Item ".backend-start.bat" -ErrorAction SilentlyContinue
}
if (Test-Path ".frontend-start.bat") {
    Remove-Item ".frontend-start.bat" -ErrorAction SilentlyContinue
}

# Stop any background jobs
Get-Job | Where-Object { $_.Name -like "*backend*" -or $_.Name -like "*frontend*" } | Stop-Job -ErrorAction SilentlyContinue
Get-Job | Where-Object { $_.Name -like "*backend*" -or $_.Name -like "*frontend*" } | Remove-Job -ErrorAction SilentlyContinue

$stopped = $false

# Stop backend - try PID file first
if (Test-Path ".backend.pid") {
    $backendPid = Get-Content ".backend.pid" -ErrorAction SilentlyContinue
    if ($backendPid) {
        try {
            $process = Get-Process -Id $backendPid -ErrorAction SilentlyContinue
            if ($process) {
                Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
                Write-Host "[Stop] ✅ Backend stopped (PID: $backendPid)" -ForegroundColor Green
                $stopped = $true
            }
        } catch {
            # Continue to port-based detection
        }
    }
    Remove-Item ".backend.pid" -ErrorAction SilentlyContinue
}

# Try to find and kill any process on port 8000
if (-not $stopped) {
    try {
        $backendProcesses = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
            Select-Object -ExpandProperty OwningProcess -Unique
        if ($backendProcesses) {
            foreach ($pid in $backendProcesses) {
                $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($proc -and ($proc.ProcessName -eq "python" -or $proc.CommandLine -like "*uvicorn*")) {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Write-Host "[Stop] ✅ Backend stopped (PID: $pid)" -ForegroundColor Green
                    $stopped = $true
                }
            }
        }
    } catch {
        # Ignore errors
    }
}

if (-not $stopped) {
    Write-Host "[Stop] ℹ️  Backend is not running" -ForegroundColor Gray
}

$stopped = $false

# Stop frontend - try PID file first
if (Test-Path ".frontend.pid") {
    $frontendPid = Get-Content ".frontend.pid" -ErrorAction SilentlyContinue
    if ($frontendPid) {
        try {
            $process = Get-Process -Id $frontendPid -ErrorAction SilentlyContinue
            if ($process) {
                Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue
                Write-Host "[Stop] ✅ Frontend stopped (PID: $frontendPid)" -ForegroundColor Green
                $stopped = $true
            }
        } catch {
            # Continue to port-based detection
        }
    }
    Remove-Item ".frontend.pid" -ErrorAction SilentlyContinue
}

# Try to find and kill any process on port 5173
if (-not $stopped) {
    try {
        $frontendProcesses = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | 
            Select-Object -ExpandProperty OwningProcess -Unique
        if ($frontendProcesses) {
            foreach ($pid in $frontendProcesses) {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Host "[Stop] ✅ Frontend stopped (PID: $pid)" -ForegroundColor Green
                $stopped = $true
            }
        }
    } catch {
        # Ignore errors
    }
}

# Also kill any node processes that might be vite
try {
    $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
    foreach ($proc in $nodeProcesses) {
        try {
            $connections = Get-NetTCPConnection -OwningProcess $proc.Id -LocalPort 5173 -ErrorAction SilentlyContinue
            if ($connections) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "[Stop] ✅ Frontend node process stopped (PID: $($proc.Id))" -ForegroundColor Green
            }
        } catch {
            # Ignore errors
        }
    }
} catch {
    # Ignore errors
}

if (-not $stopped) {
    Write-Host "[Stop] ℹ️  Frontend is not running" -ForegroundColor Gray
}

Write-Host "`n[Stop] ✅ All services stopped" -ForegroundColor Green

