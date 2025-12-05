# Restart ResumeKit Backend and Frontend
# Usage: .\restart.ps1

Write-Host "[Restart] Restarting ResumeKit services..." -ForegroundColor Cyan

# Helper function to aggressively kill a process by PID
function Stop-ProcessTree {
    param([int]$ProcessId)
    
    # First check if process actually exists
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Host "[Stop-ProcessTree] Process $ProcessId does not exist (already dead)" -ForegroundColor Gray
        return $true
    }
    
    Write-Host "[Stop-ProcessTree] Killing process $ProcessId ($($proc.ProcessName))..." -ForegroundColor Yellow
    
    try {
        # Method 1: taskkill with /T flag (kills process tree) - MOST RELIABLE
        Write-Host "[Stop-ProcessTree] Attempting taskkill /F /PID $ProcessId /T" -ForegroundColor Gray
        $result = & taskkill /F /PID $ProcessId /T 2>&1
        $exitCode = $LASTEXITCODE
        Write-Host "[Stop-ProcessTree] taskkill exit code: $exitCode" -ForegroundColor Gray
        if ($result) {
            Write-Host "[Stop-ProcessTree] taskkill output: $($result -join '; ')" -ForegroundColor Gray
        }
        Start-Sleep -Milliseconds 500
        
        # Method 2: Check if still running and try Stop-Process
        $stillRunning = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($stillRunning) {
            Write-Host "[Stop-ProcessTree] Process still running, trying Stop-Process -Force" -ForegroundColor Yellow
            Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 300
        }
        
        # Method 3: Final check and kill children individually
        $stillRunning = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($stillRunning) {
            Write-Host "[Stop-ProcessTree] Process STILL running, killing children individually..." -ForegroundColor Red
            # Get all child processes
            Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
                try {
                    $parentId = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue | 
                        Select-Object -ExpandProperty ParentProcessId -ErrorAction SilentlyContinue)
                    if ($parentId -eq $ProcessId) {
                        Write-Host "[Stop-ProcessTree] Killing child process $($_.Id)" -ForegroundColor Gray
                        & taskkill /F /PID $_.Id 2>&1 | Out-Null
                    }
                } catch { }
            }
            # Final attempt
            & taskkill /F /PID $ProcessId 2>&1 | Out-Null
            Start-Sleep -Milliseconds 500
        }
        
        # Final verification
        $finalCheck = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($finalCheck) {
            Write-Host "[Stop-ProcessTree] ❌ FAILED: Process $ProcessId is still alive!" -ForegroundColor Red
            return $false
        } else {
            Write-Host "[Stop-ProcessTree] ✅ SUCCESS: Process $ProcessId is dead" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "[Stop-ProcessTree] ⚠️  Exception: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

# Stop services first
& .\stop.ps1

# Wait a moment for processes to fully terminate
Write-Host "[Restart] Waiting for processes to terminate..." -ForegroundColor Gray
Start-Sleep -Seconds 2

# AGGRESSIVE KILL: Kill ALL Python processes that might be backend
Write-Host "[Restart] 🔥 Aggressively killing ALL backend Python processes..." -ForegroundColor Red
try {
    # Method 1: Kill by port 8000 - MOST AGGRESSIVE
    $port8000Connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    $port8000Pids = $port8000Connections | Select-Object -ExpandProperty OwningProcess -Unique
    if ($port8000Pids) {
        Write-Host "[Restart] Found $($port8000Pids.Count) process(es) on port 8000: $($port8000Pids -join ', ')" -ForegroundColor Yellow
    }
    foreach ($procId in $port8000Pids) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if (-not $proc) {
                $connState = ($port8000Connections | Where-Object { $_.OwningProcess -eq $procId } | 
                    Select-Object -First 1 -ExpandProperty State)
                Write-Host "[Restart] ℹ️  PID $procId on port 8000 doesn't exist (state: $connState, likely TIME_WAIT)" -ForegroundColor Gray
                continue
            }
            
            # Identify what this process is
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $procId" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            $connState = ($port8000Connections | Where-Object { $_.OwningProcess -eq $procId } | 
                Select-Object -First 1 -ExpandProperty State)
            
            # Check if it's the restart script itself
            if ($cmdLine -and $cmdLine -like "*restart.ps1*") {
                Write-Host "[Restart] ⚠️  Skipping PID $procId - it's the restart script itself!" -ForegroundColor Yellow
                continue
            }
            
            # Determine if it's a backend process
            $isBackend = $false
            $processType = "Unknown"
            if ($cmdLine) {
                if ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*app.main*" -or $cmdLine -like "*app/main*") {
                    $isBackend = $true
                    $processType = "Backend (uvicorn)"
                } elseif ($cmdLine -like "*restart.ps1*") {
                    $processType = "Restart script"
                } else {
                    $processType = "Other process"
                }
            } else {
                $processType = "$($proc.ProcessName) process"
            }
            
            Write-Host "[Restart] 🔥🔥🔥 KILLING $processType on port 8000 (PID: $procId, State: $connState)" -ForegroundColor Red
            if ($cmdLine) {
                $shortCmd = if ($cmdLine.Length -gt 100) { $cmdLine.Substring(0, 100) + "..." } else { $cmdLine }
                Write-Host "[Restart]    Command: $shortCmd" -ForegroundColor Gray
            }
            
            # Use taskkill directly - this is the most reliable method
            $result = & taskkill /F /PID $procId /T 2>&1
                Write-Host "[Restart]    taskkill result: $($result -join '; ')" -ForegroundColor Gray
                Start-Sleep -Milliseconds 500
                # Also try Stop-ProcessTree if process still exists
                $stillExists = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($stillExists) {
                    Stop-ProcessTree -ProcessId $procId
                    Start-Sleep -Milliseconds 500
                }
                # Verify it's dead
                $stillAlive = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($stillAlive) {
                Write-Host "[Restart] ⚠️  Process $procId is STILL ALIVE after all attempts!" -ForegroundColor Red
            } else {
                Write-Host "[Restart] ✅ Process $procId is DEAD" -ForegroundColor Green
            }
        } catch {
            Write-Host "[Restart] ⚠️  Error killing process ${procId}: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    # Method 2: Kill ALL Python processes and check command line
    $allPython = Get-Process python -ErrorAction SilentlyContinue
    Write-Host "[Restart] Found $($allPython.Count) Python process(es), checking all..." -ForegroundColor Yellow
    foreach ($proc in $allPython) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            $shouldKill = $false
            
            if ($cmdLine) {
                # Check for backend indicators
                if ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*app.main*" -or $cmdLine -like "*app/main*" -or 
                    $cmdLine -like "*ResumeKit*" -or $cmdLine -like "*backend*") {
                    $shouldKill = $true
                }
            }
            
            # Also check if using port 8000
            $usingPort = Get-NetTCPConnection -OwningProcess $proc.Id -LocalPort 8000 -ErrorAction SilentlyContinue
            if ($usingPort) {
                $shouldKill = $true
            }
            
            if ($shouldKill) {
                $killReason = if ($cmdLine -and ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*app.main*")) { "Command line match" } elseif ($usingPort) { "Using port 8000" } else { "Backend indicator" }
                Write-Host "[Restart] 🔥🔥🔥 KILLING Python backend process (PID: $($proc.Id)) - $killReason" -ForegroundColor Red
                # Use taskkill directly first - this is the most reliable
                $result = & taskkill /F /PID $proc.Id /T 2>&1
                Write-Host "[Restart]    taskkill result: $($result -join '; ')" -ForegroundColor Gray
                Start-Sleep -Milliseconds 500
                # Also try Stop-ProcessTree if process still exists
                $stillExists = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                if ($stillExists) {
                    Stop-ProcessTree -ProcessId $proc.Id
                    Start-Sleep -Milliseconds 500
                }
                # Verify it's dead
                $stillAlive = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                if ($stillAlive) {
                    Write-Host "[Restart] ⚠️  Process $($proc.Id) is STILL ALIVE after all attempts!" -ForegroundColor Red
                } else {
                    Write-Host "[Restart] ✅ Process $($proc.Id) is DEAD" -ForegroundColor Green
                }
            }
        } catch {
            Write-Host "[Restart] ⚠️  Error checking process $($proc.Id): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[Restart] ⚠️  Error in aggressive kill: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Kill PowerShell windows running backend/frontend scripts
Write-Host "[Restart] Killing PowerShell windows running backend/frontend..." -ForegroundColor Gray
try {
    Get-Process powershell, pwsh -ErrorAction SilentlyContinue | ForEach-Object {
        $proc = $_
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            if ($cmdLine) {
                # Check if it's running backend or frontend start script
                $isBackendWindow = $cmdLine -like "*backend-start.ps1*" -or $cmdLine -like "*ResumeKit Backend*" -or 
                                  ($cmdLine -like "*uvicorn*" -and $cmdLine -like "*app.main*")
                $isFrontendWindow = $cmdLine -like "*frontend-start.ps1*" -or $cmdLine -like "*ResumeKit Frontend*" -or
                                   ($cmdLine -like "*npm*" -and $cmdLine -like "*dev*" -and $cmdLine -like "*frontend*")
                
                if ($isBackendWindow) {
                    Write-Host "[Restart] 🔥🔥🔥 KILLING backend PowerShell window (PID: $($proc.Id))" -ForegroundColor Red
                    $procStillExists = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                    if ($procStillExists) {
                        Stop-ProcessTree -ProcessId $proc.Id
                    }
                } elseif ($isFrontendWindow) {
                    Write-Host "[Restart] 🔥🔥🔥 KILLING frontend PowerShell window (PID: $($proc.Id))" -ForegroundColor Red
                    $procStillExists = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                    if ($procStillExists) {
                        Stop-ProcessTree -ProcessId $proc.Id
                    }
                }
            }
        } catch {
            # Ignore errors
        }
    }
} catch {
    # Ignore errors
}

# Final wait
Start-Sleep -Seconds 2

# FINAL VERIFICATION: Check if any backend processes are still running and kill them
Write-Host "[Restart] 🔍 Final verification - checking for any remaining backend processes..." -ForegroundColor Cyan
$port8000Free = $false
$port5173Free = $false
$canStart = $false

try {
    # Check port 8000 one more time
    $stillOnPort = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($stillOnPort) {
        $pids = $stillOnPort | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            # First check if process actually exists
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if (-not $proc) {
                Write-Host "[Restart] ℹ️  Port 8000 shows PID $procId but process doesn't exist (TIME_WAIT state)" -ForegroundColor Gray
                continue
            }
            
            # Identify what this process is
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $procId" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            $connState = ($stillOnPort | Where-Object { $_.OwningProcess -eq $procId } | 
                Select-Object -First 1 -ExpandProperty State)
            
            # Check if it's the restart script itself (shouldn't happen, but check anyway)
            if ($cmdLine -and $cmdLine -like "*restart.ps1*") {
                Write-Host "[Restart] ℹ️  Process $procId is the restart script itself, skipping..." -ForegroundColor Yellow
                continue
            }
            
            # Check if it's a backend process
            $isBackend = $false
            if ($cmdLine) {
                $isBackend = ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*app.main*" -or 
                             $cmdLine -like "*app/main*" -or $cmdLine -like "*ResumeKit*")
            }
            
            # Only kill if it's actually listening (not TIME_WAIT) and is a backend process
            if ($connState -eq "Listen" -and $isBackend) {
                Write-Host "[Restart] ⚠️  Backend process $procId ($($proc.ProcessName)) still LISTENING on port 8000! Force killing..." -ForegroundColor Red
                if ($cmdLine) {
                    Write-Host "[Restart]    Command: $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))" -ForegroundColor Gray
                }
                $procStillExists = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($procStillExists) {
                    Stop-ProcessTree -ProcessId $procId
                    Start-Sleep -Milliseconds 500
                }
            } elseif ($connState -ne "Listen") {
                Write-Host "[Restart] ℹ️  Process $procId on port 8000 is in $connState state (not LISTEN), will clear automatically" -ForegroundColor Gray
            } elseif (-not $isBackend) {
                Write-Host "[Restart] ⚠️  Process $procId on port 8000 is not a backend process:" -ForegroundColor Yellow
                if ($cmdLine) {
                    Write-Host "[Restart]    Command: $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))" -ForegroundColor Gray
                } else {
                    Write-Host "[Restart]    Process: $($proc.ProcessName)" -ForegroundColor Gray
                }
            }
        }
    }
    
    # Check all Python processes one more time
    $allPython = Get-Process python -ErrorAction SilentlyContinue
    foreach ($proc in $allPython) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            $usingPort = Get-NetTCPConnection -OwningProcess $proc.Id -LocalPort 8000 -ErrorAction SilentlyContinue
            
            if (($cmdLine -and ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*app.main*")) -or $usingPort) {
                Write-Host "[Restart] ⚠️  Python process $($proc.Id) still running! Force killing..." -ForegroundColor Red
                $procStillExists = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                if ($procStillExists) {
                    Stop-ProcessTree -ProcessId $proc.Id
                    Start-Sleep -Milliseconds 500
                }
            }
        } catch { }
    }
    
    # Final check - verify if processes actually exist (not just TIME_WAIT state)
    Start-Sleep -Seconds 2  # Wait longer for port to be released
    $finalCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    
    if ($finalCheck) {
        # Check if the process actually exists or if it's just TIME_WAIT
        $pidsOnPort = $finalCheck | Select-Object -ExpandProperty OwningProcess -Unique
        $actualProcesses = @()
        foreach ($procId in $pidsOnPort) {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc) {
                $actualProcesses += $procId
                Write-Host "[Restart] ⚠️  Process $procId ($($proc.ProcessName)) is STILL ALIVE on port 8000!" -ForegroundColor Red
                Write-Host "[Restart]    Attempting final kill..." -ForegroundColor Yellow
                $procStillExists = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($procStillExists) {
                    Stop-ProcessTree -ProcessId $procId
                    Start-Sleep -Seconds 1
                }
            } else {
                Write-Host "[Restart] ℹ️  Port 8000 shows PID $procId but process doesn't exist (likely TIME_WAIT state)" -ForegroundColor Gray
                Write-Host "[Restart]    TIME_WAIT will clear automatically in a few seconds" -ForegroundColor Gray
            }
        }
        
        if ($actualProcesses.Count -eq 0) {
            # No actual processes, just TIME_WAIT - port will be free soon
            Write-Host "[Restart] ✅ No active processes on port 8000 (TIME_WAIT will clear)" -ForegroundColor Green
            $port8000Free = $true
        } else {
            # Still have active processes
            Write-Host "[Restart] ❌ ERROR: Port 8000 still has active processes: $($actualProcesses -join ', ')" -ForegroundColor Red
            Write-Host "[Restart]    Cannot start backend. Please manually kill these processes." -ForegroundColor Yellow
            $port8000Free = $false
        }
    } else {
        Write-Host "[Restart] ✅ Port 8000 is now free" -ForegroundColor Green
        $port8000Free = $true
    }
    
    # Check port 5173
    $finalCheck5173 = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
    $port5173Free = -not $finalCheck5173
    
    if (-not $port5173Free) {
        Write-Host "[Restart] ⚠️  WARNING: Port 5173 is still in use" -ForegroundColor Yellow
        $pids5173 = $finalCheck5173 | Select-Object -ExpandProperty OwningProcess -Unique
        Write-Host "[Restart]    Process IDs: $($pids5173 -join ', ')" -ForegroundColor Yellow
    } else {
        Write-Host "[Restart] ✅ Port 5173 is now free" -ForegroundColor Green
    }
    
    # Set canStart flag
    $canStart = $port8000Free  # Only need backend port free to start
    
} catch {
    Write-Host "[Restart] ⚠️  Error in final verification: $($_.Exception.Message)" -ForegroundColor Yellow
    $port8000Free = $false
    $port5173Free = $false
    $canStart = $false
}

# Double-check and force kill any remaining processes on ports (with retries)
# Only check for LISTENING connections, ignore TIME_WAIT
$maxRetries = 5
for ($retry = 1; $retry -le $maxRetries; $retry++) {
    $backendPort = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    $frontendPort = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    
    if ($backendPort) {
        # Only check for LISTENING connections, not TIME_WAIT
        $listeningConnections = $backendPort | Where-Object { $_.State -eq "Listen" }
        if ($listeningConnections) {
            Write-Host "[Restart] ⚠️  Backend port 8000 still in use (attempt $retry/$maxRetries), forcing cleanup..." -ForegroundColor Yellow
            $listeningConnections | ForEach-Object { 
                try {
                    $procId = $_.OwningProcess
                    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                    if ($proc) {
                        Write-Host "[Restart] 🔥🔥🔥 FORCE KILLING process on port 8000 (PID: $procId)" -ForegroundColor Red
                        Stop-ProcessTree -ProcessId $procId
                        Start-Sleep -Milliseconds 500
                    }
                } catch { }
            }
        }
    }
    
    if ($frontendPort) {
        Write-Host "[Restart] ⚠️  Frontend port 5173 still in use (attempt $retry/$maxRetries), forcing cleanup..." -ForegroundColor Yellow
        Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | 
            ForEach-Object { 
                try {
                    $procId = $_.OwningProcess
                    Write-Host "[Restart] 🔥 Force killing process on port 5173 (PID: $procId)" -ForegroundColor Red
                    & taskkill /F /PID $procId /T 2>&1 | Out-Null
                    Start-Sleep -Milliseconds 200
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                } catch { }
            }
    }
    
    # If both ports are free, break
    if (-not $backendPort -and -not $frontendPort) {
        break
    }
    
    if ($retry -lt $maxRetries) {
        Start-Sleep -Seconds 1
    }
}

# Final check - kill ALL Python processes that are backend (by process name)
Start-Sleep -Seconds 1
try {
    # First, kill any Python process using port 8000 (most direct method)
    Write-Host "[Restart] Checking for Python processes using port 8000..." -ForegroundColor Gray
    $port8000Processes = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $port8000Processes) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -eq "python") {
                Write-Host "[Restart] 🔥🔥🔥 KILLING Python backend process using port 8000 (PID: $procId)" -ForegroundColor Red
                $procStillExists = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($procStillExists) {
                    Stop-ProcessTree -ProcessId $procId
                    Start-Sleep -Milliseconds 500
                }
            }
        } catch {
            Write-Host "[Restart] ⚠️  Error killing process on port 8000 (PID: $procId): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    # Then check all Python processes by command line
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        Write-Host "[Restart] Checking $($pythonProcesses.Count) Python process(es) for backend..." -ForegroundColor Gray
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
            } catch { }
            
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
            
            # Method 3: Check parent process
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
                Write-Host "[Restart] ✅ Killing backend Python process (PID: $($proc.Id)) - $reason" -ForegroundColor Green
                try {
                    # First try graceful termination
                    Stop-Process -Id $proc.Id -ErrorAction Stop
                    Start-Sleep -Milliseconds 300
                    
                    # Check if still running, force kill if needed
                    $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
                    if ($stillRunning) {
                        Write-Host "[Restart]    Process still running, forcing kill..." -ForegroundColor Yellow
                        Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                    }
                    
                    # Also kill any child processes
                    Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
                        try {
                            $childParent = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)" -ErrorAction SilentlyContinue | 
                                Select-Object -ExpandProperty ParentProcessId -ErrorAction SilentlyContinue)
                            if ($childParent -eq $proc.Id) {
                                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                            }
                        } catch { }
                    }
                } catch {
                    Write-Host "[Restart]    ⚠️  Error killing process: $($_.Exception.Message)" -ForegroundColor Yellow
                    # Try taskkill as fallback
                    try {
                        & taskkill /F /PID $proc.Id /T 2>&1 | Out-Null
                    } catch { }
                }
            }
        } catch {
            Write-Host "[Restart] ⚠️  Error killing process $($proc.Id): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[Restart] ⚠️  Error checking Python processes: $($_.Exception.Message)" -ForegroundColor Yellow
}

try {
    Get-Process node -ErrorAction SilentlyContinue | ForEach-Object {
        $proc = $_
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty CommandLine -ErrorAction SilentlyContinue)
            if ($cmdLine -and ($cmdLine -like "*vite*" -or $cmdLine -like "*5173*")) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "[Restart] ✅ Killed remaining node process (PID: $($proc.Id))" -ForegroundColor Green
            }
        } catch { }
    }
} catch { }

# Final wait
Start-Sleep -Seconds 1

# Final check before starting - DO NOT START if port 8000 is still in use (LISTENING)
# Only check for LISTENING connections, ignore TIME_WAIT and other states
$port8000Check = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$port5173Check = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue

if ($port8000Check) {
    $pids = $port8000Check | Select-Object -ExpandProperty OwningProcess -Unique
    $activePids = @()
    foreach ($processId in $pids) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            $activePids += $processId
        }
    }
    
    if ($activePids.Count -gt 0) {
        Write-Host "[Restart] ❌ ERROR: Cannot start - Port 8000 is still LISTENING!" -ForegroundColor Red
        Write-Host "[Restart]    Active process IDs on port 8000: $($activePids -join ', ')" -ForegroundColor Yellow
        Write-Host "[Restart]    Aborting restart. Please manually kill the processes or restart your computer." -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "[Restart] ℹ️  Port 8000 shows connections but no active processes (TIME_WAIT), proceeding..." -ForegroundColor Gray
    }
}

if ($port5173Check) {
    $pids = $port5173Check | Select-Object -ExpandProperty OwningProcess -Unique
    $activePids = @()
    foreach ($processId in $pids) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            $activePids += $processId
        }
    }
    
    if ($activePids.Count -gt 0) {
        Write-Host "[Restart] ⚠️  WARNING: Port 5173 is still LISTENING" -ForegroundColor Yellow
        Write-Host "[Restart]    Active process IDs on port 5173: $($activePids -join ', ')" -ForegroundColor Yellow
        Write-Host "[Restart]    Will try to start frontend anyway..." -ForegroundColor Yellow
    } else {
        Write-Host "[Restart] ℹ️  Port 5173 shows connections but no active processes (TIME_WAIT), proceeding..." -ForegroundColor Gray
    }
}

# Start services in a separate terminal window with combined logs
Write-Host "[Restart] ✅ Ports are free. Starting services in separate log window..." -ForegroundColor Green

# Check if frontend is already running
$frontendRunning = $false
try {
    $frontendConn = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
    if ($frontendConn) {
        $procId = $frontendConn.OwningProcess
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($proc) {
            $frontendRunning = $true
        }
    }
} catch { }

# Get absolute paths
$projectPath = $PWD.Path
$frontendPath = Join-Path $projectPath "frontend"

# Create a script that runs both services with combined logs
# Use single quotes for the here-string to avoid quote escaping issues
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

# Start backend as background job
Set-Location '@projectPath@'
$backendJob = Start-Job -ScriptBlock {
    Set-Location '@projectPath@'
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
    Set-Location '@frontendPath@'
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
'@

# Replace placeholders with actual paths
$logScript = $logScript -replace '@projectPath@', $projectPath
$logScript = $logScript -replace '@frontendPath@', $frontendPath

# Save the log script to a temporary file with UTF-8 BOM for Windows compatibility
$logScriptPath = Join-Path $projectPath ".restart-logs.ps1"
$utf8WithBom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($logScriptPath, $logScript, $utf8WithBom)

# Start the log window
Write-Host "[Restart] [Backend] Starting on http://localhost:8000..." -ForegroundColor Cyan
if (-not $frontendRunning) {
    Write-Host "[Restart] [Frontend] Starting on http://localhost:5173..." -ForegroundColor Cyan
} else {
    Write-Host "[Restart] [Frontend] Already running on port 5173" -ForegroundColor Yellow
}

$logProcess = Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$logScriptPath`"" -WindowStyle Normal -PassThru

if ($logProcess) {
    Write-Host "[Restart] ✅ Services started in log window (PID: $($logProcess.Id))" -ForegroundColor Green
    Write-Host "[Restart]    Logs are displayed in the separate window" -ForegroundColor Gray
    Write-Host "[Restart]    This terminal will exit now" -ForegroundColor Gray
    Start-Sleep -Milliseconds 500  # Give window time to appear
} else {
    Write-Host "[Restart] ❌ Failed to start log window" -ForegroundColor Red
    exit 1
}

