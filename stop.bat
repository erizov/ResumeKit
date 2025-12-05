@echo off
setlocal enabledelayedexpansion
REM Stop ResumeKit Backend and Frontend
REM Usage: stop.bat

echo [Stop] Stopping ResumeKit services...

REM Clean up temporary start scripts
if exist .backend-start.ps1 del .backend-start.ps1
if exist .frontend-start.ps1 del .frontend-start.ps1
if exist .backend-start.bat del .backend-start.bat
if exist .frontend-start.bat del .frontend-start.bat

REM Close CMD windows with ResumeKit Backend title
taskkill /FI "WINDOWTITLE eq ResumeKit Backend*" /F >nul 2>&1
if not errorlevel 1 echo [Stop] [Backend] Backend window closed

REM Stop backend - kill Python processes by process name first
echo [Stop] [Backend] Checking Python processes...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /V "INFO:" 2^>nul') do (
    for /f "tokens=1 delims=," %%b in ("%%a") do (
        set proc_id=%%~b
        set proc_id=!proc_id:"=!
        wmic process where "ProcessId=!proc_id!" get CommandLine 2>nul | findstr /i "uvicorn\|app.main\|app/main" >nul
        if not errorlevel 1 (
            echo [Stop] [Backend] Killing Python backend process !proc_id!
            taskkill /F /PID !proc_id! >nul 2>&1
        )
    )
)

REM Stop backend (find process on port 8000) - retry up to 3 times
set retry_count=0
:kill_backend
set /a retry_count+=1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    echo [Stop] [Backend] Stopping process %%a on port 8000
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul
netstat -ano | findstr :8000 | findstr LISTENING >nul
if not errorlevel 1 (
    if !retry_count! LSS 3 goto kill_backend
)

REM Close CMD windows with ResumeKit Frontend title
taskkill /FI "WINDOWTITLE eq ResumeKit Frontend*" /F >nul 2>&1
if not errorlevel 1 echo [Stop] [Frontend] Frontend window closed

REM Stop frontend (find process on port 5173) - retry up to 3 times
set retry_count=0
:kill_frontend
set /a retry_count+=1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING 2^>nul') do (
    echo [Stop] [Frontend] Stopping process %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul
netstat -ano | findstr :5173 | findstr LISTENING >nul
if not errorlevel 1 (
    if !retry_count! LSS 3 goto kill_frontend
)

echo.
echo [Stop] All services stopped

