# Restart ResumeKit Backend and Frontend
# Usage: .\restart.ps1

Write-Host "[Restart] Restarting ResumeKit services..." -ForegroundColor Cyan

# Stop services first
& .\stop.ps1

# Wait a moment
Start-Sleep -Seconds 2

# Start services
& .\start.ps1

Write-Host "`n[Restart] ✅ Services restarted!" -ForegroundColor Green

