@echo off
REM Restart ResumeKit Backend and Frontend
REM Usage: restart.bat

echo [Restart] Restarting ResumeKit services...

call stop.bat
timeout /t 2 /nobreak >nul
call start.bat

echo.
echo [Restart] Services restarted!

