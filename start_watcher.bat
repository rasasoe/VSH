@echo off
REM File watcher - continuous monitoring
setlocal enabledelayedexpansion
cd /d %~dp0

if exist "VSH_Project_MVP\.venv\Scripts\activate.bat" (
    call VSH_Project_MVP\.venv\Scripts\activate.bat
)

cd VSH_Project_MVP
python scripts/watch_and_scan.py

endlocal
