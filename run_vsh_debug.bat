@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM ===== DEBUG VERSION =====
REM Simple, step-by-step execution with clear error messages

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%VSH_Project_MVP
set VENV_DIR=%PROJECT_DIR%\venv
set DESKTOP_DIR=%PROJECT_DIR%\vsh_desktop

echo.
echo ===== VSH Setup Debug v1 =====
echo.

REM Check project exists
if not exist "%PROJECT_DIR%\requirements.txt" (
  echo ERROR: VSH_Project_MVP\requirements.txt not found
  pause
  exit /b 1
)
echo OK: Project folder found

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not installed
  pause
  exit /b 2
)
echo OK: Python installed
python --version

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Node.js not installed
  pause
  exit /b 3
)
echo OK: Node.js installed
node --version

REM Create venv with absolute path
echo.
echo --- Creating venv ---
if not exist "%VENV_DIR%" (
  python -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo ERROR: Failed to create venv
    pause
    exit /b 4
  )
  echo OK: venv created
) else (
  echo OK: venv already exists
)

REM Python install (using venv python directly)
echo.
echo --- Installing Python packages ---
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip -q
"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%PROJECT_DIR%\requirements.txt" -q
if errorlevel 1 (
  echo ERROR: pip install failed
  pause
  exit /b 5
)
echo OK: Python packages installed

REM npm setup
echo.
echo --- Installing Node packages ---
cd /d "%DESKTOP_DIR%"
if errorlevel 1 (
  echo ERROR: Cannot change to vsh_desktop
  pause
  exit /b 6
)

REM Clean cache first
echo Cleaning npm cache...
call npm cache clean --force 2>nul >nul

REM Install
echo Installing npm packages (with timeout)...
call npm install --legacy-peer-deps --no-audit --no-fund --loglevel=error 2>nul >nul
if errorlevel 1 (
  echo Retry npm install...
  call npm install --legacy-peer-deps --no-audit --no-fund --loglevel=error 2>nul >nul
  if errorlevel 1 (
    echo ERROR: npm install failed
    pause
    exit /b 7
  )
)
echo OK: npm packages installed

REM Start API
echo.
echo --- Starting API server ---
cd /d "%PROJECT_DIR%"
set PATH=%VENV_DIR%\Scripts;%PATH%

start "VSH-API" "%VENV_DIR%\Scripts\python.exe" -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000 --log-level warning

echo Waiting for API...
timeout /t 3 /nobreak >nul

REM Check API health
set RETRY=0
:check_api
set /a RETRY=RETRY+1
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:3000/health' -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop; exit 0 } catch { exit 1 }" 2>nul
if errorlevel 0 (
  echo OK: API running
  goto start_frontend
)
if %RETRY% gtr 30 (
  echo ERROR: API timeout
  taskkill /FI "WINDOWTITLE eq VSH-API" /T /F 2>nul
  pause
  exit /b 8
)
timeout /t 1 /nobreak >nul
goto check_api

:start_frontend
echo.
echo --- Starting Vite frontend ---
cd /d "%DESKTOP_DIR%"
start "VSH-Vite" npm run dev

echo Waiting for Vite...
timeout /t 5 /nobreak >nul

echo.
echo --- Opening browser ---
start http://localhost:5173

echo.
echo ===== SUCCESS =====
echo VSH is running:
echo   API: http://127.0.0.1:3000
echo   Web: http://localhost:5173
echo.
echo Press Ctrl+C in this window to stop all services
echo.

REM Keep alive
:loop
timeout /t 5 /nobreak >nul
goto loop

exit /b 0
