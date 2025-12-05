@echo off
setlocal enabledelayedexpansion
REM Start ResumeKit Backend and Frontend with Logging in Same Window
REM Usage: start.bat

echo [Start] Starting ResumeKit services...

REM Check if backend is running
set backend_running=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    set check_pid=%%a
    tasklist /FI "PID eq !check_pid!" 2>nul | findstr /C:"!check_pid!" >nul
    if not errorlevel 1 (
        set backend_running=1
    )
)
if !backend_running! == 1 (
    echo [Start] [Backend] Already running on port 8000
) else (
    echo [Start] [Backend] Starting on http://localhost:8000...
    REM Start backend in background
    start /b python -m uvicorn app.main:app --reload > backend.log 2>&1
    echo [Start] [Backend] Started in background
)

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Check if frontend is running
set frontend_running=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING 2^>nul') do (
    set check_pid=%%a
    tasklist /FI "PID eq !check_pid!" 2>nul | findstr /C:"!check_pid!" >nul
    if not errorlevel 1 (
        set frontend_running=1
    )
)
if !frontend_running! == 1 (
    echo [Start] [Frontend] Already running on port 5173
) else (
    echo [Start] [Frontend] Starting on http://localhost:5173...
    echo.
    echo [Start] ResumeKit is running!
    echo [Start]    Backend:  http://localhost:8000
    echo [Start]    Frontend: http://localhost:5173
    echo [Start]    API Docs: http://localhost:8000/docs
    echo.
    echo [Start] All logs appear in this window
    echo [Start] Press Ctrl+C to stop all services
    echo.
    
    REM Backend logs will be written to backend.log file
    REM Frontend will run in foreground and show its own logs
    
    REM Change to frontend directory and run
    cd /d "%CD%\frontend"
    npm run dev
    cd /d "%CD%\.."
)

endlocal
