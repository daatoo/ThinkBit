# Helper script to free port 8080 (backend port)
# Run this if port 8080 is stuck

Write-Host "🔍 Finding processes on port 8080..." -ForegroundColor Cyan

$result = netstat -ano | Select-String ":8080.*LISTENING"

if ($result) {
    Write-Host "`nFound processes on port 8080:" -ForegroundColor Yellow
    foreach ($line in $result) {
        Write-Host "  $line" -ForegroundColor White
        $parts = $line -split '\s+'
        $pid = $parts[-1]
        if ($pid -match '^\d+$') {
            Write-Host "  Attempting to kill PID: $pid" -ForegroundColor Cyan
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "  ✅ Killed process $pid" -ForegroundColor Green
            } catch {
                Write-Host "  ❌ Could not kill process $pid: $_" -ForegroundColor Red
            }
        }
    }
    
    Start-Sleep -Seconds 2
    Write-Host "`n✅ Done. Port 8080 should now be free." -ForegroundColor Green
} else {
    Write-Host "✅ No processes found on port 8080" -ForegroundColor Green
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

