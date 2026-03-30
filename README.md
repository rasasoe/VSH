# VSH

VSH는 FastAPI 백엔드, Electron 데스크톱 UI, L1 정적 탐지, L2 추론, L3 심화 검증 경로를 결합한 데스크톱 중심 애플리케이션 보안 분석 프로젝트입니다.

이 레포는 다음 세 가지 실행 모드를 기준으로 정리되어 있습니다.

- 기본 실행 모드: Python + Node.js만으로 동작
- 추론 강화 모드: Gemini/OpenAI API 키를 넣어 L2 품질 강화
- 심화 검증 모드: Docker + Sonar 연동으로 L3 확장

## 목차

- 프로젝트 개요
- 현재 상태
- 주요 기능
- 전체 구조
- 빠른 실행
- 수동 실행
- 데스크톱 사용 흐름
- 런타임 DB 구조
- L1 / L2 / L3 설명
- L1 상세 문서
- 데모 대상
- 환경 변수
- 트러블슈팅
- 향후 개발

## 프로젝트 개요

VSH는 계층형 분석 모델로 구성됩니다.

- L1: 빠른 정적 탐지와 기본 정규화
- L2: 탐지 결과에 대한 추론, 설명, 수정 가이드 생성
- L3: Sonar, SBOM, PoC 검증과 같은 심화 검증 경로
- Desktop UI: Electron 기반 분석 앱
- Backend API: FastAPI 기반 스캔/설정/상태 API

핵심 의도는 선택 기능이 빠져도 제품의 기본 흐름은 항상 살아 있게 만드는 것입니다.

## 현재 상태

현재 레포는 데스크톱 시연이 가능한 상태로 정리되어 있습니다.

- FastAPI 백엔드 실행 가능
- Electron 데스크톱 빌드 가능
- `tests/fixtures/vuln_project` 스캔 가능
- SQLite / Chroma 런타임 DB 사용
- LLM 키 없이도 mock 기반으로 실행 가능
- Docker / Sonar 없이도 기본 스캔 가능

현재 샘플 프로젝트 기준 검출 수:

- 대상: `VSH_Project_MVP\tests\fixtures\vuln_project`
- 검출 수: `5`

## 주요 기능

### 1. 데스크톱 중심 분석 흐름

- Electron 앱에서 파일/프로젝트 선택
- `Scan File`, `Scan Project` 실행
- 대시보드, Findings Table, Detail Panel, Code Preview 제공
- JSON 리포트 Export 지원

### 2. FastAPI 백엔드

주요 API:

- `GET /health`
- `GET /system/status`
- `POST /scan/file`
- `POST /scan/project`
- `POST /watch/start`
- `POST /watch/stop`
- `GET /watch/status`
- `GET /settings`
- `POST /settings`
- `POST /settings/test-llm`
- `POST /settings/check-syft`

### 3. 계층형 보안 분석

- L1: 규칙 기반 정적 스캔, reachability annotation, 정규화
- L2: reasoning, attack scenario, fix suggestion
- L3: Sonar/SBOM/PoC 연계용 심화 경로

### 4. 실제 런타임 DB 사용

현재 앱 실행 경로는 repo 내부 mock 저장소를 직접 쓰지 않고, 사용자 런타임 경로의 실제 DB를 사용합니다.

- SQLite: 구조화 취약점/지식 데이터 저장
- Chroma: RAG 검색용 벡터 저장소
- JSON seed: knowledge/fix 데이터 초기 복사본

## 전체 구조

```text
VSH/
├─ README.md
├─ QUICKSTART.md
├─ TROUBLESHOOTING.md
├─ run_vsh.ps1
├─ run_vsh.bat
├─ setup_and_run.ps1
├─ .env.example
└─ VSH_Project_MVP/
   ├─ requirements.txt
   ├─ config.py
   ├─ vsh_api/
   ├─ vsh_desktop/
   ├─ vsh_runtime/
   ├─ layer1/
   ├─ layer2/
   ├─ l3/
   ├─ repository/
   ├─ shared/
   ├─ scripts/
   └─ tests/
```

디렉터리 역할 요약:

- `vsh_api/`: FastAPI 엔트리와 HTTP 라우트
- `vsh_desktop/`: Electron + React UI
- `layer1/`: L1 스캐너와 정규화 보조 로직
- `layer2/`: reasoning, retriever, analyzer
- `l3/`: Sonar, SBOM, PoC 검증 자산
- `vsh_runtime/`: 실제 분석 오케스트레이션
- `shared/`: 공용 유틸, 계약, 런타임 설정
- `tests/`: 취약 샘플과 단위 테스트

## 빠른 실행

시연용 기준 가장 간단한 실행 방법은 아래입니다.

```powershell
.\run_vsh.bat
```

현재 `run_vsh.bat` / `run_vsh.ps1`는 다음을 자동으로 처리합니다.

1. Python 실행 가능 여부 확인
2. 필요한 경우 Python requirements 설치
3. Electron 의존성 확인
4. 런타임 DB 존재 여부 확인
5. 백엔드 실행 확인
6. Electron 앱 실행

중요:

- 현재는 `vuln_project` 자동 선택/자동 스캔을 제거해 두었습니다.
- 즉 앱이 빈 상태로 열리고, 사용자가 직접 `Select Project` 후 `Scan Project`를 누르는 시연 흐름입니다.

## 수동 실행

### 1. 백엔드 실행

```powershell
cd VSH_Project_MVP
python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000
```

### 2. 프런트 빌드

```powershell
cd VSH_Project_MVP\vsh_desktop
npm run build
```

### 3. Electron 실행

```powershell
$env:VSH_USE_DIST='true'
$env:VSH_AUTO_START_API='false'
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
.\node_modules\electron\dist\electron.exe .
```

## 데스크톱 사용 흐름

권장 시연 순서:

1. `run_vsh.bat` 실행
2. 앱이 빈 상태로 열림
3. `Select Project` 클릭
4. `VSH_Project_MVP\tests\fixtures\vuln_project` 선택
5. `Scan Project` 클릭
6. 대시보드 확인
7. Findings 항목 클릭 후 Detail / Code Preview 확인

현재 구현 기준 동작 차이:

- `Scan File`: 단일 파일 스캔 결과를 같은 대시보드/Findings 영역에 표시
- `Scan Project`: 프로젝트 전체 결과를 대시보드/Findings 영역에 표시
- `Watch`: 백엔드 감시는 시작하지만, 프런트 대시보드는 자동 갱신되지 않음

## 런타임 DB 구조

활성 런타임 경로:

```text
C:\Users\<user>\.vsh\runtime_data
```

주요 구성:

- `vsh.db`: SQLite 런타임 DB
- `chroma/`: Chroma persistent storage
- `knowledge.json`: 시드 지식 데이터 복사본
- `kisa_fix.json`: 수정 가이드 시드 복사본
- `log.json`: 런타임 로그

왜 repo 밖으로 이동했는가:

- 특정 Windows 드라이브/워크스페이스 조합에서 SQLite `disk I/O error` 발생
- Chroma도 repo 내부 경로에서 불안정하게 동작
- 사용자 프로필 경로로 옮긴 뒤 안정화

## L1 / L2 / L3 설명

### L1

항상 기본 실행에 포함됩니다.

역할:

- 규칙 기반 취약점 탐지
- 파일/프로젝트 단위 정적 분석
- reachability 추정
- 공통 스키마 `vuln_records`, `package_records` 정규화

주의:

- 현재 레포의 `Semgrep`은 실제 Semgrep 바이너리 호출이 아니라
- `MockSemgrepScanner + pattern rule + reachability + dedup + normalize`로 구성된 경량 유사 Semgrep 레이어입니다.
- 즉 팀 설명 시에는 “Semgrep 스타일 규칙 기반 탐지 계층”으로 설명하는 것이 정확합니다.

### L2

두 가지 모드가 있습니다.

- mock: API 키 없이 동작
- real: Gemini/OpenAI 키가 있으면 실 호출

역할:

- 취약 여부 판단 보강
- reasoning 텍스트 생성
- attack scenario / fix suggestion 생성

### L3

선택 기능이며 외부 의존성이 있어야 완전히 살아납니다.

필요 조건:

- `SONAR_TOKEN` 또는 `SONARQUBE_TOKEN`
- Docker
- 추가 외부 툴 경로

현재 실사용 기준:

- 코드 경로는 존재
- 외부 조건이 없으면 기본 실행에서는 비활성
- 기본 앱 흐름은 L3 없이도 동작

## L1 상세 문서

팀원 설명용 별도 문서를 추가했습니다.

- [`VSH_Project_MVP/docs/L1_SEMGREP_ALGORITHM_KR.md`](/a:/VSH-main/VSH_Project_MVP/docs/L1_SEMGREP_ALGORITHM_KR.md)

이 문서에는 아래가 포함됩니다.

- 현재 L1의 실제 구현 구조
- `MockSemgrepScanner`와 `pattern_scan`의 차이
- 규칙 매칭 원리
- reachability call graph 추정 방식
- dedup / normalize 흐름
- 실제 Semgrep과 현재 구현의 차이점
- 장점 / 한계 / 개선 방향

## 데모 대상

기본 시연용 취약 프로젝트:

```text
VSH_Project_MVP\tests\fixtures\vuln_project
```

포함 취약 패턴 예시:

- command injection
- eval / code execution
- DOM-based XSS

## 환경 변수

`.env.example` 기준 주요 값:

- `LLM_PROVIDER`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `SONAR_TOKEN`
- `SONARQUBE_TOKEN`
- `SONARQUBE_URL`
- `SONARQUBE_PROJECT_KEY`
- `SYFT_PATH`
- `VSH_AUTO_START_API`
- `VSH_USE_DIST`

복사 예시:

```powershell
Copy-Item .env.example .env
```

## 트러블슈팅

### 1. Electron이 Node 모드로 뜸

원인:

- `ELECTRON_RUN_AS_NODE=1`

해결:

```powershell
Remove-Item Env:ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
```

### 2. SQLite / Chroma가 repo 내부에서 불안정함

증상:

- `sqlite3.OperationalError: disk I/O error`
- Chroma 초기화 실패

해결:

- 런타임 DB를 `C:\Users\<user>\.vsh\runtime_data`로 이동

### 3. L3가 비활성으로 보임

원인:

- Sonar 토큰 미설정
- Docker 미설치

이 경우 기본 동작에는 영향 없고, 심화 검증만 꺼집니다.

### 4. Watch를 켰는데 대시보드가 자동 갱신되지 않음

현재 구현 한계입니다.

- 백엔드 감시는 시작됨
- `.vsh/report.json`, `.vsh/diagnostics.json`은 저장됨
- 그러나 프런트가 watch 결과를 다시 polling 하지는 않음

## 향후 개발

우선순위 높은 다음 단계:

- 실제 Semgrep 바이너리 연동 또는 구조적 규칙 엔진 강화
- Tree-sitter 기반 구조 탐지 범위 확장
- watch 결과의 실시간 UI 반영
- L3 Sonar / PoC 실운영 연동 완성
- Windows/Electron 권한 문제를 피하는 배포 패키징 정리
- L1/L2/L3 상태를 UI 카드에서 더 명확히 표시
- 리포트 이력과 재실행 이력 관리 기능 추가
