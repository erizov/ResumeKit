@echo off
REM Start ResumeKit Backend and Frontend with Logging
REM Usage: start.bat

echo [Start] Starting ResumeKit services...

REM Check if backend is running
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo [Start] [Backend] Already running on port 8000
) else (
    echo [Start] [Backend] Starting on http://localhost:8000...
    echo @echo off > .backend-start.bat
    echo title ResumeKit Backend - Port 8000 >> .backend-start.bat
    echo echo [Backend] Starting ResumeKit Backend... >> .backend-start.bat
    echo echo [Backend] API: http://localhost:8000 >> .backend-start.bat
    echo echo. >> .backend-start.bat
    echo python -m uvicorn app.main:app --reload >> .backend-start.bat
    start "ResumeKit Backend" cmd /k .backend-start.bat
    echo [Start] [Backend] Started in new window
)

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Check if frontend is running
netstat -ano | findstr :5173 >nul
if %errorlevel% == 0 (
    echo [Start] [Frontend] Already running on port 5173
) else (
    echo [Start] [Frontend] Starting on http://localhost:5173...
    echo @echo off > .frontend-start.bat
    echo title ResumeKit Frontend - Port 5173 >> .frontend-start.bat
    echo cd /d "%CD%\frontend" >> .frontend-start.bat
    echo echo [Frontend] Starting ResumeKit Frontend... >> .frontend-start.bat
    echo echo [Frontend] Frontend: http://localhost:5173 >> .frontend-start.bat
    echo echo. >> .frontend-start.bat
    echo npm run dev >> .frontend-start.bat
    start "ResumeKit Frontend" cmd /k .frontend-start.bat
    echo [Start] [Frontend] Started in new window
)

echo.
echo [Start] ResumeKit is running!
echo [Start]    Backend:  http://localhost:8000
echo [Start]    Frontend: http://localhost:5173
echo [Start]    API Docs: http://localhost:8000/docs
echo.
echo [Start] Logs are displayed in separate command windows
echo [Start] Each window shows prefixed logs: [Backend] or [Frontend]
echo.
echo To stop services, run: stop.bat

