@echo off
title Riko Project Server Launcher
echo ======================================
echo      Starting Riko Project...
echo ======================================
echo.

:: PATHS
set PROJECT_ROOT=C:\Users\filip\Desktop\waifu github\ai
set VENV_PY=%PROJECT_ROOT%\.venv\Scripts\python.exe
set SERVER_PATH=%PROJECT_ROOT%\funcs
set CLIENT_PATH=%PROJECT_ROOT%\client
set SOVITS_PATH=C:\Users\filip\Desktop\my-waifu-tests\GPT-SoVITS-v3lora-20250228\GPT-SoVITS-v3lora-20250228

echo Using Python: %VENV_PY%
echo.

:: VRM SERVER
echo Starting VRM Animation Server...
start "VRM Animation Server" cmd /k "cd /d %PROJECT_ROOT% && "%VENV_PY%" -m uvicorn funcs.server:app --host 0.0.0.0 --port 8001"

:: VITE CLIENT
echo Starting Vite Client...
start "Vite Client" cmd /k "cd /d %CLIENT_PATH% && npx vite --host"

:: GPT-SOVITS
echo Starting GPT-SoVITS API...
start "GPT-SoVITS" cmd /k "cd /d %SOVITS_PATH% && runtime\python.exe api_v2.py"

echo.
echo All servers are launching!
echo Open subtitles page on: http://localhost:5173/captions.html
pause
