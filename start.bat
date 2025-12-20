@echo off
REM AegisAI - Quick Start Batch File
REM Double-click this file to start both servers

cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "%~dp0start.ps1"
pause

