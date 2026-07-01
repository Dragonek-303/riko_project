@echo off
setlocal enabledelayedexpansion
title Riko Project Selective Killer
echo ======================================
echo      Stopping Riko Project Ports...
echo ======================================

:: List of ports to clear
set PORTS=8001 5173 9880

for %%P in (%PORTS%) do (
    echo Checking port %%P...
    for /f "tokens=5" %%A in ('netstat -aon ^| findstr :%%P ^| findstr LISTENING') do (
        echo Found process PID %%A on port %%P. Killing...
        taskkill /F /PID %%A /T
    )
)

:: We close CMD windows with specific titles so they don't remain open and empty
echo.
echo Cleaning up console windows...
taskkill /F /FI "WINDOWTITLE eq VRM Animation Server*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Vite Client*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq GPT-SoVITS*" /T >nul 2>&1

echo.
echo ✅ Specific services on ports 8001, 5173, 9880 have been stopped.
pause
