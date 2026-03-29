@echo off
REM API Server only startup
setlocal enabledelayedexpansion
cd /d %~dp0

if exist "VSH_Project_MVP\.venv\Scripts\activate.bat" (
    call VSH_Project_MVP\.venv\Scripts\activate.bat
)

cd VSH_Project_MVP
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000 --reload

endlocal
