@echo off
REM eve-cli Windows launcher wrapper
REM Launches eve-cli.ps1 using the current PowerShell execution policy
chcp 65001 >nul 2>&1
powershell.exe -NoProfile -File "%~dp0eve-cli.ps1" %*
