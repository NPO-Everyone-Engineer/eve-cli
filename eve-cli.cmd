@echo off
REM eve-cli Windows launcher wrapper
REM Launches eve-cli.ps1 with ExecutionPolicy bypass for convenience
chcp 65001 >nul 2>&1
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0eve-cli.ps1" %*
