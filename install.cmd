@echo off
REM eve-cli Windows installer wrapper
REM Launches install.ps1 with ExecutionPolicy bypass
chcp 65001 >nul 2>&1
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0install.ps1" %*
