@echo off
REM Restart ResumeKit Backend and Frontend
REM Usage: restart.bat

echo [Restart] Restarting ResumeKit services...

call stop.bat

REM Wait for processes to fully terminate
echo [Restart] Waiting for processes to terminate...
timeout /t 3 /nobreak >nul

REM Double-check ports are free and force kill if needed
setlocal enabledelayedexpansion

REM Check and cleanup backend port (max 5 retries)
set backend_retry=0
:check_backend
set /a backend_retry+=1
netstat -ano | findstr :8000 | findstr LISTENING >nul
if errorlevel 1 (
    echo [Restart] Backend port 8000 is free
    goto backend_done
)
if !backend_retry! LSS 6 (
    echo [Restart] Backend port 8000 still in use, forcing cleanup... (attempt !backend_retry!/5)
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
        set kill_pid=%%a
        tasklist /FI "PID eq !kill_pid!" 2>nul | findstr /C:"!kill_pid!" >nul
        if not errorlevel 1 (
            echo [Restart] Killing process !kill_pid!
            taskkill /F /PID !kill_pid! >nul 2>&1
        )
    )
    REM Also try killing ALL Python processes that might be backend (by process name)
    echo [Restart] Checking Python processes for backend...
    for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /V "INFO:" 2^>nul') do (
        for /f "tokens=1 delims=," %%b in ("%%a") do (
            set proc_id=%%~b
            set proc_id=!proc_id:"=!
            wmic process where "ProcessId=!proc_id!" get CommandLine 2>nul | findstr /i "uvicorn\|app.main\|app/main" >nul
            if not errorlevel 1 (
                echo [Restart] Killing Python backend process !proc_id!
                taskkill /F /PID !proc_id! >nul 2>&1
            ) else (
                REM Also check if this Python process is using port 8000
                netstat -ano | findstr :8000 | findstr "!proc_id!" >nul
                if not errorlevel 1 (
                    echo [Restart] Killing Python process !proc_id! using port 8000
                    taskkill /F /PID !proc_id! >nul 2>&1
                )
            )
        )
    )
    timeout /t 2 /nobreak >nul
    goto check_backend
) else (
    echo [Restart] WARNING: Backend port 8000 still in use after 5 attempts. Continuing anyway...
)
:backend_done

REM Check and cleanup frontend port (max 5 retries)
set frontend_retry=0
:check_frontend
set /a frontend_retry+=1
netstat -ano | findstr :5173 | findstr LISTENING >nul
if errorlevel 1 (
    echo [Restart] Frontend port 5173 is free
    goto frontend_done
)
if !frontend_retry! LSS 6 (
    echo [Restart] Frontend port 5173 still in use, forcing cleanup... (attempt !frontend_retry!/5)
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING 2^>nul') do (
        set kill_pid=%%a
        tasklist /FI "PID eq !kill_pid!" 2>nul | findstr /C:"!kill_pid!" >nul
        if not errorlevel 1 (
            echo [Restart] Killing process !kill_pid!
            taskkill /F /PID !kill_pid! >nul 2>&1
        )
    )
    REM Also try killing all node processes that might be vite
    for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO CSV ^| findstr /V "INFO:" 2^>nul') do (
        for /f "tokens=1 delims=," %%b in ("%%a") do (
            set pid=%%~b
            set pid=!pid:"=!
            wmic process where "ProcessId=!pid!" get CommandLine 2>nul | findstr /i "vite\|5173" >nul
            if not errorlevel 1 (
                echo [Restart] Killing node process !pid!
                taskkill /F /PID !pid! >nul 2>&1
            )
        )
    )
    timeout /t 2 /nobreak >nul
    goto check_frontend
) else (
    echo [Restart] WARNING: Frontend port 5173 still in use after 5 attempts. Continuing anyway...
)
:frontend_done

endlocal

REM Final wait
timeout /t 1 /nobreak >nul

call start.bat

echo.
echo [Restart] Services restarted!
