# AegisAI - Start Script
# This script starts both the backend and frontend servers

Write-Host "🚀 Starting AegisAI..." -ForegroundColor Cyan

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found. Please run setup first:" -ForegroundColor Red
    Write-Host "   python3 -m venv .venv" -ForegroundColor Yellow
    Write-Host "   .venv\Scripts\activate" -ForegroundColor Yellow
    Write-Host "   pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Green
& ".venv\Scripts\Activate.ps1"

# Set Google Application Credentials
$keyPath = Join-Path $scriptDir "aegis-key.json"
if (Test-Path $keyPath) {
    $env:GOOGLE_APPLICATION_CREDENTIALS = (Resolve-Path $keyPath).Path
    Write-Host "✅ Google credentials configured" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: aegis-key.json not found" -ForegroundColor Yellow
}

# Check if node_modules exists for frontend
$websiteDir = Join-Path $scriptDir "website"
if (-not (Test-Path (Join-Path $websiteDir "node_modules"))) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Green
    Set-Location $websiteDir
    npm install
    Set-Location $scriptDir
}

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
    return -not $connection
}

# Function to kill process on port
function Stop-ProcessOnPort {
    param([int]$Port)
    $netstat = netstat -ano | Select-String ":$Port.*LISTENING"
    if ($netstat) {
        $pid = ($netstat -split '\s+')[-1]
        if ($pid) {
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Host "✅ Killed process $pid on port $Port" -ForegroundColor Green
                Start-Sleep -Seconds 1
                return $true
            } catch {
                return $false
            }
        }
    }
    return $false
}

# Check backend port (now 8080)
if (-not (Test-Port -Port 8080)) {
    Write-Host "⚠️  Port 8080 is already in use" -ForegroundColor Yellow
    $response = Read-Host "   Kill existing process and continue? (y/n)"
    if ($response -eq 'y') {
        if (-not (Stop-ProcessOnPort -Port 8080)) {
            Write-Host "❌ Could not free port 8080. Please close the application using it manually." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ Cannot start backend on port 8080" -ForegroundColor Red
        exit 1
    }
}

# Check frontend port (now 3000)
if (-not (Test-Port -Port 3000)) {
    Write-Host "⚠️  Port 3000 is already in use" -ForegroundColor Yellow
    $response = Read-Host "   Kill existing process and continue? (y/n)"
    if ($response -eq 'y') {
        if (-not (Stop-ProcessOnPort -Port 3000)) {
            Write-Host "❌ Could not free port 3000. Please close the application using it manually." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ Cannot start frontend on port 3000" -ForegroundColor Red
        exit 1
    }
}

# Function to handle cleanup on exit
function Cleanup {
    Write-Host "`n🛑 Shutting down servers..." -ForegroundColor Yellow
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "✅ Servers stopped" -ForegroundColor Green
}

# Register cleanup on script exit
Register-EngineEvent PowerShell.Exiting -Action { Cleanup } | Out-Null
$null = Register-ObjectEvent -InputObject ([System.Console]) -EventName CancelKeyPress -Action { Cleanup; exit }

# Start backend server in a new window
Write-Host "🔧 Starting backend server (port 8080)..." -ForegroundColor Green
$backendScript = @"
import os
import sys
sys.path.insert(0, r'$scriptDir')
os.chdir(r'$scriptDir')
from src.backend.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8080, reload=False)
"@

$backendProcess = Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-c", $backendScript -PassThru -WindowStyle Normal

# Wait a moment for backend to start and verify
Start-Sleep -Seconds 3
if ($backendProcess.HasExited) {
    Write-Host "❌ Backend failed to start. Check the backend window for errors." -ForegroundColor Red
    exit 1
}

# Start frontend server in a new window
Write-Host "🎨 Starting frontend server (port 8080)..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $websiteDir -PassThru -WindowStyle Normal

# Wait a moment for frontend to start
Start-Sleep -Seconds 3

Write-Host "`n✅ AegisAI is running!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8080" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "`nBoth servers are running in separate windows." -ForegroundColor Yellow
Write-Host "Close those windows or press Ctrl+C here to stop monitoring.`n" -ForegroundColor Yellow

# Wait for user interrupt or process exit
try {
    while ($true) {
        Start-Sleep -Seconds 1
        # Check if processes are still running
        if ($backendProcess.HasExited) {
            Write-Host "❌ Backend process exited" -ForegroundColor Red
            break
        }
        if ($frontendProcess.HasExited) {
            Write-Host "❌ Frontend process exited" -ForegroundColor Red
            break
        }
    }
} catch {
    Write-Host "`nMonitoring stopped" -ForegroundColor Yellow
} finally {
    Write-Host "`n💡 Tip: Close the server windows to stop them, or run Cleanup manually" -ForegroundColor Cyan
}

