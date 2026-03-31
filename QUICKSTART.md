# VSH 빠른 시작

## 1. 필수 준비

필수:

- Python 3.10+
- Node.js 18+

선택:

- `GEMINI_API_KEY` 또는 `OPENAI_API_KEY`: 실제 L2 추론 활성화
- `Semgrep`: 실제 L1 CLI 스캔 활성화
- `SONAR_TOKEN`: Sonar 기반 L3 연계
- `Docker`: PoC/L3 확장 흐름
- `Syft`: SBOM 보강

중요:

- `Semgrep`과 `Syft`는 현재 VSH에서 **Python 라이브러리보다 로컬 CLI 도구**로 취급합니다.
- 즉 `pip install`만으로 끝난다고 가정하지 말고, PATH에 잡히는 실행 파일 또는 수동 경로 설정이 필요할 수 있습니다.

## 2. 가장 빠른 실행

루트에서 아래 한 줄이면 됩니다.

```powershell
.\run_vsh.bat
```

이 스크립트는 다음을 자동 처리합니다.

1. Python 환경 확인
2. 필요한 Python 패키지 설치
3. Electron 의존성 확인
4. 런타임 DB 확인
5. 백엔드 실행 확인
6. 데스크톱 앱 실행

## 3. 시연 흐름

현재 기본 시연 흐름은 자동 타깃 지정이 아닙니다.

즉:

1. `run_vsh.bat` 실행
2. VSH Desktop 빈 화면으로 열림
3. `Select Project`
4. `VSH_Project_MVP\tests\fixtures\vuln_project` 선택
5. `Scan Project`

## 4. 수동 실행

### 백엔드 설치

```powershell
python -m pip install -r VSH_Project_MVP\requirements.txt
```

### 데스크톱 설치

```powershell
cd VSH_Project_MVP\vsh_desktop
npm install
```

### 런타임 DB 초기화

```powershell
cd ..
python -m scripts.bootstrap_runtime_dbs
```

### 백엔드 실행

```powershell
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000
```

### 설정 확인

앱이 뜬 뒤 `Settings -> Local Runtime`에서 아래를 바로 점검할 수 있습니다.

- `Check Semgrep`
- `Check Syft`
- Sonar URL / Token / Project Key 저장

또는 API로:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:3000/system/status' | ConvertTo-Json -Depth 6
```

### 데스크톱 빌드 및 실행

```powershell
cd vsh_desktop
npm run build
$env:VSH_USE_DIST='true'
$env:VSH_AUTO_START_API='false'
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
.\node_modules\electron\dist\electron.exe .
```

## 5. 런타임 경로

- SQLite: `C:\Users\<you>\.vsh\runtime_data\vsh.db`
- Chroma: `C:\Users\<you>\.vsh\runtime_data\chroma`

## 6. 참고 문서

- 프로젝트 개요: [`README.md`](/a:/VSH-main/README.md)
- 문제 해결: [`TROUBLESHOOTING.md`](/a:/VSH-main/TROUBLESHOOTING.md)
- L1 설명: [`L1_SEMGREP_ALGORITHM_KR.md`](/a:/VSH-main/VSH_Project_MVP/docs/L1_SEMGREP_ALGORITHM_KR.md)
