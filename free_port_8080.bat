@echo off
REM Helper script to free port 8000
powershell.exe -ExecutionPolicy Bypass -File "%~dp0free_port_8000.ps1"
pause

