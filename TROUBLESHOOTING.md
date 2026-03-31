# VSH 트러블슈팅

## 1. 백엔드 import 오류

증상:

- `ModuleNotFoundError`
- `vsh_api`, `vsh_runtime` 같은 내부 모듈 import 실패

해결:

```powershell
cd VSH_Project_MVP
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000
```

## 2. 3000 포트가 이미 사용 중임

확인:

```powershell
netstat -ano | findstr :3000
```

종료:

```powershell
taskkill /PID <PID> /F
```

또는 다른 포트 사용:

```powershell
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3001
```

## 3. Electron이 Node 모드로 뜸

증상:

- Electron이 앱이 아니라 Node처럼 동작함
- 메인 프로세스가 비정상 종료됨

원인:

- `ELECTRON_RUN_AS_NODE=1`

해결:

```powershell
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
```

## 4. SQLite / Chroma가 repo 내부에서 불안정함

증상:

- `sqlite3.OperationalError: disk I/O error`
- Chroma init 또는 migration 실패

현재 적용된 해결:

- 활성 런타임 데이터를 `C:\Users\<you>\.vsh\runtime_data`로 이동

다시 초기화하려면:

```powershell
cd VSH_Project_MVP
python -m scripts.bootstrap_runtime_dbs
```

## 5. venv 생성이 실패함

증상:

- `python -m venv` 실패
- `ensurepip` 실패

현재 레포 대응:

- `run_vsh.ps1`와 `setup_and_run.ps1`는 필요한 경우 시스템 Python으로 폴백

## 6. L3가 계속 비활성 상태임

다음 중 하나라도 없으면 정상입니다.

- `SONAR_TOKEN` 또는 `SONARQUBE_TOKEN`
- `SONAR_PROJECT_KEY` 또는 `SONARQUBE_PROJECT_KEY`
- Docker
- 기타 L3 외부 의존성

상태 확인:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:3000/system/status' | ConvertTo-Json -Depth 5
```

확인 포인트:

- `l3.enabled`
- `l3.reason`
- `l3.docker.installed`
- `l3.sonar.has_token`
- `l3.sonar.project_key`

## 7. LLM이 실 provider를 사용하지 않음

다음 키가 비어 있으면 정상입니다.

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

이 경우 앱은 mock reasoning으로 계속 동작합니다.

## 8. 데스크톱 앱이 안 뜨거나 바로 닫힘

확인 순서:

- 백엔드가 `http://127.0.0.1:3000/health`에서 살아 있는지
- `npm install`이 완료되었는지
- `npm run build`가 성공했는지
- `node_modules\electron\dist\electron.exe`가 존재하는지
- `ELECTRON_RUN_AS_NODE`가 제거되었는지

## 9. Watch를 켰는데 UI가 자동 갱신되지 않음

현재 구현 한계입니다.

- 백엔드 감시는 시작됨
- `.vsh/report.json`, `.vsh/diagnostics.json`은 저장됨
- 프런트에서 watch 결과를 자동 polling 하지는 않음

## 10. 런타임 데이터 초기화가 필요함

런타임 데이터가 꼬였다고 판단되면 아래 순서로 초기화합니다.

```powershell
Remove-Item -Recurse -Force "$HOME\.vsh\runtime_data"
cd VSH_Project_MVP
python -m scripts.bootstrap_runtime_dbs
```

## 11. Semgrep이 안 잡힘

증상:

- `Settings`에서 `Semgrep not found`
- `/system/status`의 `semgrep.installed=false`

해결:

- `semgrep` CLI가 PATH에 있는지 확인
- PATH에 없으면 Settings의 `Override Semgrep path`에 실행 파일 경로 지정
- Semgrep이 없어도 VSH는 내부 휴리스틱 L1로 계속 동작하지만, 실제 CLI 결과는 비활성입니다.

## 12. Syft는 설치했는데 앱에서 못 찾음

중요:

- VSH가 찾는 것은 Python 모듈이 아니라 `syft` 실행 파일입니다.
- 따라서 `pip install`만 한 상태라면 기대한 CLI가 생기지 않을 수 있습니다.

해결:

- OS에 설치된 `syft` CLI가 PATH에 잡히는지 확인
- 또는 Settings의 `Override Syft path`에 실행 파일 경로 지정
