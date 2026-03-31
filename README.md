# VSH

> Desktop-first Application Security Verification Platform

VSH는 정적 탐지, 추론, 심화 검증 흐름을 하나의 데스크톱 경험으로 묶기 위해 만든 보안 분석 프로젝트입니다. FastAPI 백엔드와 Electron 데스크톱 UI를 중심으로 구성되어 있으며, 로컬 환경만으로도 기본 분석이 가능하고, 필요 시 LLM·Sonar·Docker 같은 외부 요소를 단계적으로 확장할 수 있습니다.

## 왜 VSH인가

보안 도구는 흔히 다음 둘 중 하나에 치우칩니다.

- 탐지는 빠르지만 결과 설명과 후속 판단이 약함
- 검증은 깊지만 실행 환경이 무겁고 시연/운영이 어려움

VSH는 이 간극을 줄이는 것을 목표로 합니다.

- L1에서 빠르게 후보 취약점을 찾고
- L2에서 그 결과를 설명 가능하게 정리하고
- L3에서 가능한 경우 Sonar/SBOM/PoC 검증으로 더 깊게 들어갑니다.

즉, “탐지에서 끝나는 도구”가 아니라 “검토와 설명, 그리고 확장 가능한 검증 흐름”까지 포함한 데스크톱 제품 경험을 지향합니다.

## 핵심 가치

- 빠른 실행: Python + Node.js만으로 기본 동작 가능
- 데스크톱 중심 UX: 파일 선택, 프로젝트 스캔, 상세 패널, 코드 프리뷰 제공
- 점진적 확장: API 키, Sonar, Docker를 붙이면 상위 계층 확장 가능
- 설명 가능성: 단순 검출 수치가 아니라 reasoning과 fix suggestion까지 연결
- 데모 친화성: 빈 상태로 앱을 열고 사용자가 직접 프로젝트를 선택하는 흐름 지원

## 현재 상태

현재 레포는 시연 가능한 데스크톱 안정화 상태입니다.

- FastAPI 백엔드 실행 가능
- Electron 데스크톱 빌드 가능
- `tests/fixtures/vuln_project` 스캔 가능
- SQLite / Chroma 런타임 DB 사용
- LLM 키 없이도 mock reasoning으로 동작
- Docker / Sonar 없이도 기본 분석 가능

현재 샘플 프로젝트 기준 검출 수:

- 대상: `VSH_Project_MVP\tests\fixtures\vuln_project`
- 검출 수: `5`

## 아키텍처 개요

VSH는 계층형 구조를 따릅니다.

- `L1`: 규칙 기반 정적 탐지와 기본 정규화
- `L2`: 탐지 결과 보강, reasoning, attack scenario, fix suggestion
- `L3`: Sonar / SBOM / PoC 검증을 위한 심화 경로
- `Desktop UI`: Electron + React 기반 사용자 인터페이스
- `Backend API`: FastAPI 기반 스캔/설정/상태 관리

### 레이어별 역할

#### L1

- 파일/프로젝트 단위 정적 분석
- rule 기반 취약점 후보 검출
- reachability 추정
- 공통 스키마 `vuln_records`, `package_records` 생성

#### L2

- L1 결과를 바탕으로 reasoning 수행
- mock 또는 실제 Gemini/OpenAI provider 사용
- 취약 여부 보강, 공격 시나리오, 수정 가이드 생성

#### L3

- Docker와 Sonar 설정이 준비되면 Sonar/SBOM/PoC 연계
- 현재는 선택형 경로이며, 기본 실행에서는 없어도 동작

## L1을 왜 이렇게 구현했는가

처음 L1은 이름상 `Semgrep` 계층을 포함했지만, **실제 Semgrep CLI를 호출하지 않고 Semgrep 스타일 탐지기를 직접 구현한 상태**였습니다.

이번 업데이트로 L1은 아래 두 축을 함께 사용하는 **하이브리드 구조**가 되었습니다.

- 실제 `Semgrep` CLI 호출 (`SemgrepCLIScanner`)
- 직접 구현한 경량 규칙 엔진 (`MockSemgrepScanner`, `pattern_scan`, `TreeSitterScanner`, `reachability`)

즉 지금의 VSH L1은 “Semgrep을 버린 구조”도 아니고, “Semgrep만 black-box로 붙인 구조”도 아닙니다.

- Semgrep이 설치되어 있으면 실제 바이너리를 호출해 structural/pattern rule 결과를 먼저 얻고
- Semgrep이 없으면 기존 직접구현 L1이 계속 동작하며
- 두 결과는 dedup과 normalize를 거쳐 동일한 `vuln_records` 스키마로 합쳐집니다.

직접 구현 계층은 여전히 아래 요소를 조합한 **Semgrep 스타일의 경량 정적 분석 계층**입니다.

- `MockSemgrepScanner`
- `SemgrepCLIScanner`
- `pattern_scan`
- `TreeSitterScanner` 보조 탐지
- `reachability` annotation
- `deduplicate_findings`
- `normalize_scan_result`

이렇게 설계한 이유는 세 가지입니다.

### 1. Semgrep의 원리를 이해하고 내부화하기 위해

단순히 외부 도구를 붙이는 수준이 아니라, Semgrep이 가진 “규칙 기반 정적 탐지” 사고방식을 팀이 직접 소화하고 싶었습니다.

즉:

- 어떤 식으로 규칙이 매칭되는지
- 구조 기반 탐지와 문자열 기반 탐지의 차이가 무엇인지
- false positive가 왜 생기는지
- 후속 L2/L3와 연결할 때 어떤 스키마가 필요한지

이것을 팀이 직접 이해하기 위해 경량 구현을 만들었습니다.

### 2. 우리 파이프라인에 맞게 제어하기 위해

실제 제품에서는 탐지 결과가 바로 끝나는 것이 아니라,

- reachability annotation
- 공통 스키마 정규화
- L2 reasoning 연결
- L3 handoff

까지 자연스럽게 이어져야 했습니다. 현재 L1 구조는 이 후속 파이프라인에 맞게 직접 제어하기 쉽습니다.

### 3. 시연과 로컬 실행 안정성을 확보하기 위해

실제 Semgrep CLI는 강력하지만, 외부 바이너리 의존성과 환경 차이, OS별 이슈를 동반합니다. 현재 프로젝트 단계에서는 “완전한 최종 탐지 엔진”보다 “빠르고 안정적으로 반복 실행 가능한 데모/개발 구조”가 더 중요했습니다.

## 실제 Semgrep과 현재 L1의 차이

### 실제 Semgrep

장점:

- AST 기반 구조적 패턴 매칭
- 언어별 parser 활용
- `pattern-inside`, metavariable 같은 고급 규칙 지원
- false positive를 줄이기 쉬움

단점:

- 외부 바이너리 의존성
- 실행 환경 변수 증가
- 프로젝트 내부 커스텀 파이프라인과 완전히 맞추려면 추가 통합 필요

### 현재 VSH L1

장점:

- 실제 Semgrep CLI를 붙일 수 있음
- 가볍고 빠름
- 레포 내부 제어가 쉬움
- L2/L3 공통 스키마와 연결하기 쉬움
- 데모와 반복 시연에 적합
- 규칙 추가 및 실험 비용이 낮음

단점:

- Semgrep 미설치 환경에서는 여전히 휴리스틱/정규식 비중이 큼
- 직접구현 계층은 정규식 중심이라 오탐/누락 가능성 존재
- 복잡한 다중 줄/다중 함수 흐름에 약함
- 현재 reachability는 정밀 taint analysis가 아니라 휴리스틱 기반 추정임

한 줄로 요약하면:

> 현재 VSH L1은 실제 Semgrep CLI와 직접 구현한 휴리스틱 탐지 계층을 함께 쓰는 하이브리드 L1이며, Semgrep의 핵심 아이디어를 팀이 이해하고 파이프라인에 흡수하기 위해 만든 직접구현 엔진도 계속 유지합니다.

## 주요 기능

### 데스크톱 중심 분석 흐름

- Electron 앱에서 파일/프로젝트 선택
- `Scan File`, `Scan Project` 실행
- Dashboard, Findings Table, Detail Panel, Code Preview 제공
- JSON 리포트 Export 지원

### FastAPI 백엔드

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
- `POST /settings/check-semgrep`
- `POST /settings/check-syft`

### 실제 런타임 DB 사용

현재 앱 실행 경로는 repo 내부 mock 저장소를 직접 쓰지 않고, 사용자 런타임 경로의 실제 DB를 사용합니다.

- SQLite: 구조화 취약점/지식 데이터 저장
- Chroma: RAG 검색용 벡터 저장소
- JSON seed: knowledge/fix 데이터 초기 복사본

## 저장소 구조

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
- `layer1/`: L1 스캐너와 정규화 로직
- `layer2/`: reasoning, retriever, analyzer
- `l3/`: Sonar, SBOM, PoC 검증 자산
- `vsh_runtime/`: 실제 분석 오케스트레이션
- `shared/`: 공용 유틸, 계약, 런타임 설정
- `tests/`: 취약 샘플과 단위 테스트

## 빠른 실행

시연용 기준 가장 간단한 실행 방법:

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
- 앱은 빈 상태로 열리고, 사용자가 직접 프로젝트를 선택하는 시연 흐름입니다.

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
6. Dashboard 확인
7. Findings 항목 클릭 후 Detail / Code Preview 확인

현재 구현 기준 동작 차이:

- `Scan File`: 단일 파일 결과를 같은 Dashboard/Findings 영역에 표시
- `Scan Project`: 프로젝트 전체 결과를 같은 Dashboard/Findings 영역에 표시
- `Watch`: 백엔드 감시는 시작하지만 프런트 대시보드는 자동 갱신되지 않음

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
- 사용자 프로필 경로로 이동한 뒤 안정화

## L1 상세 문서

팀원 설명용 별도 문서:

- [`VSH_Project_MVP/docs/L1_SEMGREP_ALGORITHM_KR.md`](/a:/VSH-main/VSH_Project_MVP/docs/L1_SEMGREP_ALGORITHM_KR.md)

이 문서에는 아래가 포함됩니다.

- 현재 L1의 실제 구현 구조
- `MockSemgrepScanner`와 `pattern_scan`의 차이
- 규칙 매칭 원리
- reachability call graph 추정 방식
- dedup / normalize 흐름
- 실제 Semgrep과 현재 구현의 차이점
- 왜 이 구조를 선택했는지에 대한 배경
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
- `SONAR_URL`
- `SONARQUBE_URL`
- `SONAR_ORG`
- `SONAR_PROJECT_KEY`
- `SEMGREP_PATH`
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
- Sonar project key 미설정

현재는 `/system/status`에서 아래를 함께 확인할 수 있습니다.

- `semgrep` 설치 여부
- `syft` 설치 여부
- `docker` 설치 여부
- `l3.sonar.has_token`
- `l3.sonar.project_key`

이 경우 기본 동작에는 영향 없고, 심화 검증만 꺼집니다.

### 4. Syft는 pip 패키지인가

아닙니다. 현재 VSH에서 취급하는 `Syft`는 Python 라이브러리가 아니라 **별도 로컬 CLI 도구**입니다.

즉:

- `pip install`만으로 VSH가 기대하는 `syft` 바이너리가 준비된다고 가정하면 안 되고
- 일반적으로는 공식 배포 바이너리나 OS 패키지 매니저 경로에 설치된 `syft` CLI가 필요합니다.

VSH는 이 전제를 기준으로:

- PATH 자동 감지
- 수동 경로 override
- `/settings/check-syft`

흐름을 제공합니다.

### 4. Watch를 켰는데 대시보드가 자동 갱신되지 않음

현재 구현 한계입니다.

- 백엔드 감시는 시작됨
- `.vsh/report.json`, `.vsh/diagnostics.json`은 저장됨
- 그러나 프런트가 watch 결과를 다시 polling 하지는 않음

## 향후 개발

우선순위 높은 다음 단계:

- 실제 Semgrep CLI 연동 또는 구조적 규칙 엔진 강화
- 실제 Semgrep CLI와 내부 휴리스틱 엔진 간 rule parity 확장
- Tree-sitter 기반 구조 탐지 범위 확장
- watch 결과의 실시간 UI 반영
- L3 Sonar / PoC 실운영 연동 고도화
- Windows/Electron 권한 문제를 피하는 배포 패키징 정리
- L1/L2/L3 상태를 UI 카드에서 더 명확히 표시
- 리포트 이력과 재실행 이력 관리 기능 추가
