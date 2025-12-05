@echo off
REM Stop ResumeKit Backend and Frontend
REM Usage: stop.bat

echo [Stop] Stopping ResumeKit services...

REM Clean up temporary start scripts
if exist .backend-start.ps1 del .backend-start.ps1
if exist .frontend-start.ps1 del .frontend-start.ps1
if exist .backend-start.bat del .backend-start.bat
if exist .frontend-start.bat del .frontend-start.bat

REM Stop backend (find process on port 8000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo [Stop] [Backend] Stopping process %%a
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 echo [Stop] [Backend] Process %%a not found or already stopped
)

REM Stop frontend (find process on port 5173)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    echo [Stop] [Frontend] Stopping process %%a
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 echo [Stop] [Frontend] Process %%a not found or already stopped
)

REM Also kill any node processes (vite)
taskkill /F /IM node.exe >nul 2>&1

echo.
echo [Stop] All services stopped

