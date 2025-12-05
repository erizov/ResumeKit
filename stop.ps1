# Stop ResumeKit Backend and Frontend
# Usage: .\stop.ps1

Write-Host "[Stop] Stopping ResumeKit services..." -ForegroundColor Yellow

# Clean up temporary start scripts and log files
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
if (Test-Path ".restart-logs.ps1") {
    Remove-Item ".restart-logs.ps1" -ErrorAction SilentlyContinue
}
if (Test-Path ".start-logs.ps1") {
    Remove-Item ".start-logs.ps1" -ErrorAction SilentlyContinue
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
                # Kill the PowerShell window process
                Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
                Write-Host "[Stop] ✅ Backend window closed (PID: $backendPid)" -ForegroundColor Green
                $stopped = $true
            }
        } catch {
            # Continue to port-based detection
        }
    }
    Remove-Item ".backend.pid" -ErrorAction SilentlyContinue
}

# Close PowerShell windows running backend start script
try {
    Get-Process powershell, pwsh -ErrorAction SilentlyContinue | ForEach-Object {
        $proc = $_
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            if ($cmdLine) {
                # Check for backend window (script or uvicorn command)
                $isBackendWindow = $cmdLine -like "*backend-start.ps1*" -or $cmdLine -like "*ResumeKit Backend*" -or
                                  ($cmdLine -like "*uvicorn*" -and $cmdLine -like "*app.main*")
                if ($isBackendWindow) {
                    Write-Host "[Stop] ✅ Killing backend PowerShell window (PID: $($proc.Id))" -ForegroundColor Green
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                    $stopped = $true
                }
            }
        } catch {
            # Ignore errors
        }
    }
} catch {
    # Ignore errors
}

# Try to find and kill any process on port 8000 (only LISTENING, not TIME_WAIT)
try {
    $backendConnections = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($backendConnections) {
        $backendProcesses = $backendConnections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $backendProcesses) {
            try {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    # Kill the process and all its children
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Write-Host "[Stop] ✅ Backend stopped (PID: $procId)" -ForegroundColor Green
                    $stopped = $true
                }
            } catch {
                # Process might already be gone
            }
        }
    }
} catch {
    # Ignore errors
}

# Kill ALL Python processes that might be backend (by process name and command line)
try {
    # First, kill any Python process using port 8000 (most direct method)
    Write-Host "[Stop] Checking for Python processes using port 8000..." -ForegroundColor Gray
    $port8000Connections = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($port8000Connections) {
        $port8000Processes = $port8000Connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $port8000Processes) {
            try {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc -and $proc.ProcessName -eq "python") {
                    Write-Host "[Stop] ✅ Killing Python process using port 8000 (PID: $procId)" -ForegroundColor Green
                    Stop-Process -Id $procId -Force -ErrorAction Stop
                    Start-Sleep -Milliseconds 200
                    # Also kill children (check if process still exists first)
                    $procStillExists = Get-Process -Id $procId -ErrorAction SilentlyContinue
                    if ($procStillExists) {
                        & taskkill /F /PID $procId /T 2>&1 | Out-Null
                    }
                    $stopped = $true
                }
            } catch {
                Write-Host "[Stop] ⚠️  Error killing process on port 8000 (PID: $procId): $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    
    # Then check all Python processes by command line
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        Write-Host "[Stop] Found $($pythonProcesses.Count) Python process(es), checking command lines..." -ForegroundColor Gray
    }
    foreach ($proc in $pythonProcesses) {
        try {
            $shouldKill = $false
            $reason = ""
            
            # Method 1: Check command line
            try {
                $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                    Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
                if ($cmdLine) {
                    if ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*app.main*" -or $cmdLine -like "*app/main*" -or $cmdLine -like "*ResumeKit*") {
                        $shouldKill = $true
                        $reason = "Command line contains backend keywords"
                    }
                }
            } catch {
                # If we can't get command line, try other methods
            }
            
            # Method 2: Check if using port 8000
            if (-not $shouldKill) {
                try {
                    $portConn = Get-NetTCPConnection -OwningProcess $proc.Id -LocalPort 8000 -ErrorAction SilentlyContinue
                    if ($portConn) {
                        $shouldKill = $true
                        $reason = "Using port 8000"
                    }
                } catch { }
            }
            
            # Method 3: Check parent process (uvicorn might spawn child processes)
            if (-not $shouldKill) {
                try {
                    $parentProc = Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                        Select-Object -ExpandProperty ParentProcessId -ErrorAction SilentlyContinue
                    if ($parentProc) {
                        $parentCmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $parentProc" -ErrorAction SilentlyContinue | 
                            Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
                        if ($parentCmdLine -and ($parentCmdLine -like "*uvicorn*" -or $parentCmdLine -like "*app.main*")) {
                            $shouldKill = $true
                            $reason = "Child of backend process"
                        }
                    }
                } catch { }
            }
            
            if ($shouldKill) {
                Write-Host "[Stop] ✅ Killing backend Python process (PID: $($proc.Id)) - $reason" -ForegroundColor Green
                if ($cmdLine) {
                    Write-Host "[Stop]    Command: $($cmdLine.Substring(0, [Math]::Min(100, $cmdLine.Length)))..." -ForegroundColor Gray
                }
                
                # Kill the process and all its children
                try {
                    # First try graceful termination
                    Stop-Process -Id $proc.Id -ErrorAction Stop
                    Start-Sleep -Milliseconds 300
                    
                    # Check if still running, force kill if needed
                    $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                    if ($stillRunning) {
                        Write-Host "[Stop]    Process still running, forcing kill..." -ForegroundColor Yellow
                        Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                    }
                    
                    # Also kill any child processes (multiprocessing spawn processes)
                    Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
                        try {
                            $childParent = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue | 
                                Select-Object -ExpandProperty ParentProcessId -ErrorAction SilentlyContinue)
                            if ($childParent -eq $proc.Id) {
                                Write-Host "[Stop]    Killing child process (PID: $($_.Id))" -ForegroundColor Gray
                                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                            }
                        } catch { }
                    }
                    
                    $stopped = $true
                } catch {
                    Write-Host "[Stop]    ⚠️  Error killing process: $($_.Exception.Message)" -ForegroundColor Yellow
                    # Try taskkill as fallback
                    try {
                        & taskkill /F /PID $proc.Id /T 2>&1 | Out-Null
                        $stopped = $true
                    } catch { }
                }
            }
        } catch {
            Write-Host "[Stop] ⚠️  Error killing process $($proc.Id): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[Stop] ⚠️  Error checking Python processes: $($_.Exception.Message)" -ForegroundColor Yellow
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
                # Kill the PowerShell window process
                Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue
                Write-Host "[Stop] ✅ Frontend window closed (PID: $frontendPid)" -ForegroundColor Green
                $stopped = $true
            }
        } catch {
            # Continue to port-based detection
        }
    }
    Remove-Item ".frontend.pid" -ErrorAction SilentlyContinue
}

# Close PowerShell windows running frontend start script
try {
    Get-Process powershell, pwsh -ErrorAction SilentlyContinue | ForEach-Object {
        $proc = $_
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            if ($cmdLine) {
                # Check for frontend window (script or npm dev command)
                $isFrontendWindow = $cmdLine -like "*frontend-start.ps1*" -or $cmdLine -like "*ResumeKit Frontend*" -or
                                   ($cmdLine -like "*npm*" -and $cmdLine -like "*dev*" -and $cmdLine -like "*frontend*")
                if ($isFrontendWindow) {
                    Write-Host "[Stop] ✅ Killing frontend PowerShell window (PID: $($proc.Id))" -ForegroundColor Green
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                    $stopped = $true
                }
            }
        } catch {
            # Ignore errors
        }
    }
} catch {
    # Ignore errors
}

# Try to find and kill any process on port 5173 (only LISTENING, not TIME_WAIT)
try {
    $frontendConnections = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($frontendConnections) {
        $frontendProcesses = $frontendConnections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $frontendProcesses) {
            try {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    # Kill the process and all its children (node processes)
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Write-Host "[Stop] ✅ Frontend stopped (PID: $procId)" -ForegroundColor Green
                    $stopped = $true
                }
            } catch {
                # Process might already be gone
            }
        }
    }
} catch {
    # Ignore errors
}

# Also kill any remaining node processes that might be related to vite
try {
    Get-Process node -ErrorAction SilentlyContinue | ForEach-Object {
        $proc = $_
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            if ($cmdLine -and ($cmdLine -like "*vite*" -or $cmdLine -like "*frontend*" -or $cmdLine -like "*npm*" -or $cmdLine -like "*5173*")) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "[Stop] ✅ Killed node process (PID: $($proc.Id))" -ForegroundColor Green
                $stopped = $true
            }
        } catch {
            # Ignore errors
        }
    }
} catch {
    # Ignore errors
}

# Also check for node processes using port 5173
try {
    $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
    foreach ($proc in $nodeProcesses) {
        try {
            $connections = Get-NetTCPConnection -OwningProcess $proc.Id -LocalPort 5173 -ErrorAction SilentlyContinue
            if ($connections) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "[Stop] ✅ Frontend node process stopped (PID: $($proc.Id))" -ForegroundColor Green
                $stopped = $true
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

