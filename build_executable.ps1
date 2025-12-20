# Build AegisAI Executable Script
# This script creates a standalone executable using PyInstaller

Write-Host "🔨 Building AegisAI executable..." -ForegroundColor Cyan

# Check if PyInstaller is installed
$pyInstallerInstalled = python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Installing PyInstaller..." -ForegroundColor Green
    pip install pyinstaller
}

# Create the executable
Write-Host "⚙️  Creating executable..." -ForegroundColor Green
pyinstaller --onefile --name AegisAI --console start_app.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Executable created successfully!" -ForegroundColor Green
    Write-Host "   Location: dist\AegisAI.exe" -ForegroundColor Cyan
    Write-Host "`nYou can now run AegisAI.exe from anywhere!" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Build failed. Check the errors above." -ForegroundColor Red
}

