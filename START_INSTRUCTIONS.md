# AegisAI - Startup Instructions

This project provides multiple ways to start both the backend and frontend servers together.

## Quick Start Options

### Option 1: PowerShell Script (Recommended)
Double-click `start.ps1` or run from PowerShell:
```powershell
.\start.ps1
```

### Option 2: Batch File (Easiest)
Double-click `start.bat` - this will run the PowerShell script automatically.

### Option 3: Python Script
Run the Python startup script:
```powershell
python start_app.py
```

## Creating a Single Executable

To create a standalone executable that runs both servers:

### Using PyInstaller

1. Install PyInstaller:
```powershell
pip install pyinstaller
```

2. Create the executable:
```powershell
pyinstaller --onefile --name AegisAI --icon=NONE start_app.py
```

3. The executable will be in the `dist` folder. You can move it anywhere and run it.

### Using cx_Freeze (Alternative)

1. Install cx_Freeze:
```powershell
pip install cx_Freeze
```

2. Create a `setup.py`:
```python
from cx_Freeze import setup, Executable

setup(
    name="AegisAI",
    version="1.0",
    description="AegisAI Application Launcher",
    executables=[Executable("start_app.py", base=None)]
)
```

3. Build:
```powershell
python setup.py build
```

## Prerequisites

Before running, ensure you have:

1. ✅ Virtual environment created and activated
2. ✅ Dependencies installed (`pip install -r requirements.txt`)
3. ✅ Frontend dependencies installed (`cd website && npm install`)
4. ✅ Google credentials file (`aegis-key.json`) in the project root

## Ports

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:8080

## Stopping the Servers

- Press `Ctrl+C` in the terminal/console
- Or close the server windows if running in separate windows

## Troubleshooting

### PowerShell Execution Policy
If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use
If ports 8000 or 8080 are already in use:
- Backend: Change port in `src/backend/main.py` (line 295)
- Frontend: Change port in `website/vite.config.ts` (line 10)

### Virtual Environment Not Found
Run the setup commands:
```powershell
python3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

