@echo off
REM ============================================
REM VSH Demo Launcher - 발표자용 시작 스크립트
REM ============================================
REM 목표: 한 번의 클릭으로 API/Watcher/GUI 전 시스템 시작

setlocal enabledelayedexpansion
cd /d %~dp0

echo.
echo =========================================
echo VSH (Vibe Secure Helper) Engine
echo Integrated SAST + LLM + Evidence-based Verification
echo =========================================
echo.

REM 1. Python 버전 확인
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python found

REM 2. 가상환경 활성화
echo.
echo [2/4] Activating virtual environment...
if exist "VSH_Project_MVP\.venv\Scripts\activate.bat" (
    call VSH_Project_MVP\.venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ⚠️  Virtual environment not found. Creating...
    python -m venv VSH_Project_MVP\.venv
    call VSH_Project_MVP\.venv\Scripts\activate.bat
    pip install -r VSH_Project_MVP/requirements.txt >nul 2>&1
    echo ✅ Virtual environment created
)

REM 3. .env 파일 확인
echo.
echo [3/4] Checking configuration...
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from .env.example...
    if exist ".env.example" (
        copy .env.example .env >nul
    ) else (
        REM 최소 .env 생성
        (
            echo # VSH Configuration
            echo LLM_PROVIDER=gemini
            echo GEMINI_API_KEY=
            echo SONARQUBE_TOKEN=
        ) > .env
    )
    echo ✅ .env created (please update with your API keys)
)

REM 4. API 서버 실행
echo.
echo [4/4] Starting VSH API server...
echo 🚀 VSH API starting on http://127.0.0.1:3000
echo.
echo Press Ctrl+C to stop the server
echo.

cd VSH_Project_MVP
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000 --reload

endlocal
