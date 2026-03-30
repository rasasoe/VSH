@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%VSH_Project_MVP"
set "VENV_DIR=%PROJECT_DIR%\venv"
set "DESKTOP_DIR=%PROJECT_DIR%\vsh_desktop"
set "WORK_DIR=%SCRIPT_DIR%"

REM OneDrive 감지 및 C 드라이브로 복사
if "!SCRIPT_DIR!"=="*OneDrive*" (
  if exist "C:\VSH_RUNTIME" (
    rmdir /s /q "C:\VSH_RUNTIME" >nul 2>&1
  )
  mkdir "C:\VSH_RUNTIME" >nul 2>&1
  echo [VSH] OneDrive 경로 감지. C:\VSH_RUNTIME으로 복사 중... 이 과정은 시간이 걸릴 수 있습니다.
  xcopy "!SCRIPT_DIR!" "C:\VSH_RUNTIME\" /s /e /y /q >nul 2>&1
  if !errorlevel! equ 0 (
    set "WORK_DIR=C:\VSH_RUNTIME"
    set "PROJECT_DIR=!WORK_DIR!\VSH_Project_MVP"
    set "VENV_DIR=!PROJECT_DIR!\venv"
    set "DESKTOP_DIR=!PROJECT_DIR!\vsh_desktop"
    echo [VSH] ✓ 복사 완료. C:\VSH_RUNTIME에서 실행합니다.
  ) else (
    echo [VSH] WARNING: 복사 실패. OneDrive 경로에서 계속 진행합니다. (npm 에러 가능성 있음)
  )
) else (
  echo [VSH] ✓ OneDrive 경로 아님. 로컬에서 실행합니다.
)

echo.
echo [VSH] ============================================
echo [VSH] VSH Integrated Security Hub
echo [VSH] ============================================
echo [VSH] Working dir: !WORK_DIR!
echo [VSH] Project dir: !PROJECT_DIR!
echo.

REM 프로젝트 디렉토리 확인
if not exist "!PROJECT_DIR!\requirements.txt" (
  echo [VSH] ERROR: VSH_Project_MVP 폴더를 찾을 수 없습니다
  echo [VSH] ACTION: run_vsh.bat이 루트 디렉토리에 있는지 확인하세요
  pause
  exit /b 1
)

REM Python 버전 체크
echo [VSH] Python 버전 체크...
python --version >nul 2>&1
if !errorlevel! neq 0 (
  echo [VSH] ERROR: Python 미설치
  echo [VSH] ACTION: https://www.python.org 에서 3.9 이상 설치
  pause
  exit /b 10
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
  set "PY_VERSION=%%i"
  set "PY_MAJOR=!PY_VERSION:~0,1!"
  set "PY_MINOR=!PY_VERSION:~2,2!"
)
echo [VSH] ✓ Python !PY_VERSION! 확인

REM Python 3.9 이상 확인
if !PY_MAJOR! lss 3 (
  echo [VSH] ERROR: Python 3.9 이상 필요 ^(현재: !PY_VERSION!^)
  pause
  exit /b 11
)

REM Node.js 버전 체크
echo [VSH] Node.js 버전 체크...
node --version >nul 2>&1
if !errorlevel! neq 0 (
  echo [VSH] ERROR: Node.js 미설치
  echo [VSH] ACTION: https://nodejs.org 에서 16 LTS 이상 설치
  pause
  exit /b 12
)

for /f %%i in ('node --version 2^>^&1') do set "NODE_VERSION=%%i"
echo [VSH] ✓ Node.js !NODE_VERSION! 확인

REM npm cache 정리
echo [VSH] npm 캐시 정리...
call npm cache clean --force >nul 2>&1
echo [VSH] ✓ npm 캐시 정리됨

REM venv 생성
cd /d "!PROJECT_DIR!"
if !errorlevel! neq 0 (
  echo [VSH] ERROR: 프로젝트 디렉토리 접근 불가
  pause
  exit /b 2
)

if not exist "!VENV_DIR!" (
  echo [VSH] venv 생성 중...
  python -m venv "!VENV_DIR!"
  if !errorlevel! neq 0 (
    echo [VSH] ERROR: venv 생성 실패
    pause
    exit /b 3
  )
  echo [VSH] ✓ venv 생성 완료
)

REM venv 활성화
echo [VSH] venv 활성화...
call "!VENV_DIR!\Scripts\activate.bat"
if !errorlevel! neq 0 (
  echo [VSH] ERROR: venv 활성화 실패
  pause
  exit /b 4
)
echo [VSH] ✓ venv 활성화됨

REM Python 의존성 설치
echo [VSH] Python 의존성 설치 중... (첫 실행 시 1-2분 걸릴 수 있습니다)
pip install -q --upgrade pip 2>nul
pip install -q -r "!PROJECT_DIR!\requirements.txt"
if !errorlevel! neq 0 (
  echo [VSH] ERROR: pip install 실패
  echo [VSH] ACTION: 네트워크 연결 확인
  pause
  exit /b 5
)
echo [VSH] ✓ Python 의존성 설치 완료

REM Node 의존성 설치
echo [VSH] Node.js 의존성 설치 중... (첫 실행 시 1-2분 걸릴 수 있습니다)
cd /d "!DESKTOP_DIR!"
if !errorlevel! neq 0 (
  echo [VSH] ERROR: vsh_desktop 폴더 없음
  cd /d "!PROJECT_DIR!"
  pause
  exit /b 6
)

npm install --no-audit --no-fund --loglevel=error --legacy-peer-deps >nul 2>&1
if !errorlevel! neq 0 (
  echo [VSH] WARNING: npm install 실패. 재시도 중...
  npm cache clean --force >nul 2>&1
  npm install --no-audit --no-fund --loglevel=error --legacy-peer-deps >nul 2>&1
  if !errorlevel! neq 0 (
    echo [VSH] ERROR: npm install 최종 실패
    cd /d "!PROJECT_DIR!"
    pause
    exit /b 7
  )
)
echo [VSH] ✓ Node.js 의존성 설치 완료

REM API 서버 시작
echo.
echo [VSH] ============================================
echo [VSH] 서비스 시작 중...
echo [VSH] ============================================
echo [VSH] API 서버 시작 (포트 3000)...

cd /d "!PROJECT_DIR!"
start "VSH-API" /min cmd /c "!VENV_DIR!\Scripts\activate.bat && python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000 --log-level warning"

REM API 헬스체크
echo [VSH] API 활성화 대기 (최대 30초)...
set "RETRY=0"
:api_healthcheck
set /a RETRY+=1
if !RETRY! gtr 60 (
  echo [VSH] ERROR: API 서버 응답 없음. 포트 3000 확인하세요
  taskkill /FI "WINDOWTITLE eq VSH-API" /T /F 2>nul
  pause
  exit /b 8
)
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:3000/health' -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop; exit 0 } catch { exit 1 }" 2>nul
if !errorlevel! equ 0 (
  echo [VSH] ✓ API 서버 실행 중
  goto api_ready
)
timeout /T 1 /NOBREAK >nul
goto api_healthcheck

:api_ready
REM Vite 서버 시작
echo [VSH] Vite 개발 서버 시작 (포트 5173)...
cd /d "!DESKTOP_DIR!"
start "VSH-Vite" /min cmd /c npm run dev

echo [VSH] Vite 활성화 대기...
timeout /T 3 /NOBREAK >nul

REM 브라우저 자동 열기
echo [VSH] 브라우저 열기...
start http://localhost:5173

echo.
echo [VSH] ============================================
echo [VSH] ✓ 모든 서비스 실행 중!
echo [VSH] ============================================
echo [VSH] 
echo [VSH] 접속 주소:
echo [VSH]   - http://localhost:5173 (자동 열림)
echo [VSH]   - API: http://127.0.0.1:3000
echo [VSH]
echo [VSH] 사용 방법:
echo [VSH]   1. Dashboard - 취약점 통계 보기
echo [VSH]   2. Scan - 코드 폴더 선택 후 분석 시작
echo [VSH]   3. Results - L1/L2/L3 분석 결과 확인
echo [VSH]
echo [VSH] 샘플 스캔:
echo [VSH]   - 폴더: VSH_Project_MVP\tests\samples\vuln_project
echo [VSH]   - L1: SAST (200ms)
echo [VSH]   - L2: LLM (3-5초)
echo [VSH]   - L3: 검증 (백그라운드)
echo [VSH]
echo [VSH] 종료:
echo [VSH]   - 브라우저 닫기
echo [VSH]   - 또는 Ctrl+C (터미널)
echo [VSH]
echo [VSH] ============================================

REM 서비스 유지
:keep_running
timeout /T 5 /NOBREAK >nul
goto keep_running

REM 정리
:cleanup
taskkill /FI "WINDOWTITLE eq VSH-API" /T /F 2>nul
taskkill /FI "WINDOWTITLE eq VSH-Vite" /T /F 2>nul
exit /b 0
