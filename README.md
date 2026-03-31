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
- 실제 `Semgrep` CLI 연동 가능
- 실제 `Syft` CLI 연동 가능
- Windows에서 `Semgrep` / `Syft`를 Docker wrapper로 우회 실행 가능
- 로컬 `SonarQube` Docker 서버를 이용한 완전 로컬 L3 구성 가능
- 샘플 프로젝트 기준 로컬 SonarQube 스캔 검증 완료

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

## 직접구현 휴리스틱이 무엇을 보충하는가

지금 L1에서 `Semgrep`을 붙였다고 해서 직접구현 계층이 의미를 잃은 것은 아닙니다. 현재 직접구현 휴리스틱은 아래 역할을 보충합니다.

### 1. reachability annotation

[`VSH_Project_MVP/layer1/common/reachability.py`](VSH_Project_MVP/layer1/common/reachability.py) 는 source/sink 패턴과 간단한 함수 호출 그래프를 이용해 다음 상태를 붙입니다.

- `reachable`
- `conditionally_reachable`
- `unknown`
- `unreachable`

즉 `Semgrep`이 “패턴이 존재한다”를 잘 잡는다면, VSH 휴리스틱은 “사용자 입력이 실제 sink까지 닿는 코드 구조로 보이느냐”를 추가로 표현합니다.

### 2. knowledge 기반 custom rule 보조

[`VSH_Project_MVP/layer1/scanner/mock_semgrep_scanner.py`](VSH_Project_MVP/layer1/scanner/mock_semgrep_scanner.py) 는 `knowledge.json`의 rule을 line-by-line으로 순회합니다.

이 계층은:

- 내부 지식 저장소 기반 룰 실험
- Semgrep 설치 여부와 무관한 최소 탐지선 확보
- 레포 내부에서 수정 비용이 낮은 custom rule 유지

에 유리합니다.

### 3. hard-coded pattern rule 보강

[`VSH_Project_MVP/layer1/common/pattern_scan.py`](VSH_Project_MVP/layer1/common/pattern_scan.py) 는 Python/JS/TS에 대해 VSH 내부 룰셋을 돌립니다.

예:

- `eval()`
- `os.system()`
- `subprocess(..., shell=True)`
- `document.write()`
- `innerHTML`

이 계층은 빠르고 설명 가능성이 높아서, 데모와 반복 시연에 여전히 강합니다.

### 4. Tree-sitter 구조 보조

`TreeSitterScanner`는 현재 주력 엔진은 아니지만, 문자열 정규식보다 구조적인 힌트를 일부 보강합니다.

### 5. typosquatting / 공급망 보조 신호

[`VSH_Project_MVP/layer1/common/import_risk.py`](VSH_Project_MVP/layer1/common/import_risk.py) 기반으로 import 이름 유사도와 알려진 패키지 이름을 비교해 typosquatting 가능성을 탐지합니다. 이건 일반적인 코드 패턴 취약점과는 다른 축의 신호입니다.

### 6. SBOM / 패키지 보강

`SBOMScanner`와 `Syft` 연계를 통해 코드 취약점 외에도:

- 취약 버전 패키지
- dependency 관점 리스크
- package record

를 별도 축으로 수집합니다.

정리하면 현재 L1은:

- `Semgrep CLI`가 syntax-aware rule matching을 담당하고
- VSH 휴리스틱이 reachability, custom rule, typosquatting, SBOM, 후단 스키마 정규화를 보강하는 구조입니다.

## 지금까지 실제로 반영된 작업

최근까지 이 레포에 실제 반영된 큰 작업은 아래와 같습니다.

### L1 / Semgrep

- 실제 `Semgrep CLI` 호출 추가
- `Semgrep` 미설치 시 내부 휴리스틱으로 폴백
- `Semgrep`, `pattern_scan`, `MockSemgrep`, `Tree-sitter`, `reachability`를 합치는 하이브리드 L1 구성
- Windows에서 직접 설치형 `semgrep.exe`가 불안정할 때를 대비해 Docker wrapper 추가

관련 파일:

- [`VSH_Project_MVP/layer1/scanner/semgrep_cli_scanner.py`](VSH_Project_MVP/layer1/scanner/semgrep_cli_scanner.py)
- [`VSH_Project_MVP/tools/semgrep-docker.cmd`](VSH_Project_MVP/tools/semgrep-docker.cmd)

### Syft / SBOM

- `Syft`를 Python 라이브러리가 아니라 로컬 CLI로 취급하도록 정리
- 경로 자동 감지와 수동 override 추가
- Docker wrapper 추가

관련 파일:

- [`VSH_Project_MVP/tools/syft-docker.cmd`](VSH_Project_MVP/tools/syft-docker.cmd)
- [`VSH_Project_MVP/l3/providers/sbom/real.py`](VSH_Project_MVP/l3/providers/sbom/real.py)

### 설정 / 상태 노출

- `Semgrep`, `Syft`, `Docker`, `Sonar`, `L3 readiness` 상태를 `/system/status`로 노출
- Settings 화면에서 `Check Semgrep`, `Check Syft`, Sonar URL/Token/Project Key 설정 가능
- 저장 후 L3 상태 즉시 재평가

관련 파일:

- [`VSH_Project_MVP/shared/runtime_settings.py`](VSH_Project_MVP/shared/runtime_settings.py)
- [`VSH_Project_MVP/vsh_api/main.py`](VSH_Project_MVP/vsh_api/main.py)
- [`VSH_Project_MVP/vsh_desktop/src/components/SettingsPage.tsx`](VSH_Project_MVP/vsh_desktop/src/components/SettingsPage.tsx)

### L3 / Sonar

- SonarCloud token 기반 L3 연결 정리
- GitHub import 없이도 로컬 폴더를 Sonar 대상으로 돌릴 수 있는 방향으로 정리
- 로컬 `SonarQube` Docker 서버 자동 부트스트랩 스크립트 추가
- 로컬 SonarQube에서는 `organization` 없이도 프로젝트 생성/조회 가능하도록 provider 수정
- Docker scanner 컨테이너에서 `127.0.0.1` 대신 `host.docker.internal`을 쓰도록 보강

관련 파일:

- [`VSH_Project_MVP/scripts/setup_local_sonarqube.py`](VSH_Project_MVP/scripts/setup_local_sonarqube.py)
- [`VSH_Project_MVP/l3/providers/sonarqube/real.py`](VSH_Project_MVP/l3/providers/sonarqube/real.py)

검증 결과:

- 로컬 SonarQube 서버 `http://127.0.0.1:9000` 구동 확인
- `vsh-local` 프로젝트 생성 확인
- 샘플 프로젝트에 대해 실제 로컬 SonarQube 스캔 수행
- 이슈 `8`건 수집 확인

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

## 완전 로컬 L3

기본 VSH 스캔은 원래부터 GitHub 레포 연결 없이 로컬 파일/폴더를 바로 분석합니다. 여기에 `L3`까지 완전히 로컬로 붙이고 싶다면 로컬 `SonarQube`를 Docker로 띄우면 됩니다.

이미 자동 부트스트랩 스크립트가 포함되어 있습니다.

```powershell
cd VSH_Project_MVP
python -m scripts.setup_local_sonarqube
```

이 스크립트는:

1. `sonarqube:community` Docker 이미지를 pull
2. `vsh-sonarqube` 컨테이너 실행
3. `http://127.0.0.1:9000` 준비될 때까지 대기
4. 로컬 Sonar 토큰 생성
5. `vsh-local` 프로젝트 생성
6. VSH 설정 파일에 URL / token / project key 저장

즉 SonarCloud 계정 없이도 로컬 SonarQube만으로 L3를 붙일 수 있습니다.

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

- [`VSH_Project_MVP/docs/L1_SEMGREP_ALGORITHM_KR.md`](VSH_Project_MVP/docs/L1_SEMGREP_ALGORITHM_KR.md)

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

- 실제 Semgrep CLI와 내부 휴리스틱 엔진 간 rule parity 확장
- Tree-sitter 기반 구조 탐지 범위 확장
- watch 결과의 실시간 UI 반영
- L3 Sonar / PoC 실운영 연동 고도화
- Windows/Electron 권한 문제를 피하는 배포 패키징 정리
- L1/L2/L3 상태를 UI 카드에서 더 명확히 표시
- 리포트 이력과 재실행 이력 관리 기능 추가

## 자체 평가 및 보완

### L1

L1은 이번 단계에서 실제 `Semgrep CLI`를 연결하고, 기존 직접구현 휴리스틱 엔진과 결합하여 하이브리드 정적 분석 계층으로 고도화되었습니다. 특히 `pattern_scan`, `MockSemgrepScanner`, `reachability`, `import_risk`, `SBOM` 보조 경로를 통해 단순 코드 패턴뿐 아니라 공급망 위험과 프로젝트 맞춤형 보안 신호까지 함께 수집할 수 있게 된 점은 분명한 성과입니다. 또한 이 결과를 공통 스키마로 정규화하여 L2/L3 및 프런트 UI와 자연스럽게 연결한 것도 실제 제품 관점에서 의미가 있었습니다.

다만 현재 L1은 완전한 `Semgrep-only` 엔진이 아니라 실제 Semgrep 결과와 내부 휴리스틱 결과를 합치는 구조이므로, 중복 결과 병합과 신뢰도 우선순위 정리가 앞으로 더 정교해질 필요가 있습니다. 현재도 dedup 단계가 존재하지만, 향후에는 같은 위치를 여러 엔진이 잡았을 때 어떤 엔진을 더 신뢰할지, 어떤 메타데이터를 유지할지를 rule-level로 세밀하게 다듬어야 합니다.

또한 직접구현 휴리스틱의 상당 부분은 line-by-line 정규식 기반 탐지이기 때문에, 빠르고 설명 가능하다는 장점이 있는 반면 복잡한 다중 줄 문맥, 간접 호출, 프레임워크별 흐름, interprocedural data flow에는 한계가 있습니다. `reachability` 역시 완전한 taint analysis가 아니라 source/sink와 호출 그래프 기반의 경량 추정이므로, 실제 실행 흐름을 완전히 보장하지는 못합니다. 따라서 향후에는 Tree-sitter나 구조 기반 분석 비중을 높이고, Semgrep과 내부 룰 간 parity를 강화하며, false positive를 줄이기 위한 context filter를 추가하는 방향으로 보완할 예정입니다.

마지막으로 L1과 연결된 사용자 경험 측면에서는 `Semgrep`/`Syft` 실행 경로 감지, 상태 표시, 설정 저장 후 즉시 재평가, 인라인 경고 소비를 위한 메타데이터 정리까지 진행하였지만, 아직 watch 기반 실시간 UI 재반영과 IDE별 피드백 표준화는 추가 작업이 필요합니다. 즉 현재 L1은 탐지 엔진으로서뿐 아니라 프런트/IDE와 연결되는 제품형 보안 레이어로 발전하고 있으나, 탐지 정밀도와 사용자 피드백 루프는 계속 고도화해야 합니다.

### L2

- **Confidence**: LLM 자체의 “불확실성”을 직접 측정한다기보다, evidence 양과 verification 상태, retrieval hit 수 같은 파이프라인 신호를 heuristic으로 점수화한 구조에 가깝습니다.
- **Patch preview**: 실제 프로젝트 전체 문맥을 반영한 안전한 패치 생성이라기보다, 취약 코드 스니펫과 제안 코드를 비교한 preview 중심이라 실서비스 자동 패치로 쓰기에는 한계가 있습니다.
- **Retrieval 품질 루프**: RAG는 동작하지만, 검색 정확도 측정, hit-rate 평가, 프롬프트 튜닝 같은 반복 최적화 체계는 아직 충분히 갖춰지지 않았습니다.
- **Provider 운영**: 멀티 provider 지원은 강점이지만, 품질·비용·속도·안정성을 기준으로 어떤 provider를 어떤 상황에 쓸지에 대한 운영 정책은 더 정교해질 필요가 있습니다.

### RAG

**1. KISA 데이터 구조화 미흡**

- PDF 기반 원문을 페이지 단위 텍스트 덩어리로 저장한 비중이 있어, 취약 코드 예시, 안전 코드 예시, 조치 방법이 별도 필드로 충분히 구조화되지 않았습니다.
- 그 결과 실제 LLM에는 필요 이상의 원문이 함께 들어가 컨텍스트 낭비가 생길 수 있습니다.

**2. 한국어 임베딩 정확도**

- 현재 사용 중인 `all-MiniLM-L6-v2`는 범용 다국어 모델이지만, KISA/FSI 같은 한국어 보안 문서 검색에 특화된 임베딩은 아닙니다.
- 따라서 한국어 질의나 국내 보안 문서 맥락에서는 의미 유사도 품질이 기대보다 낮을 수 있습니다.

**3. 벡터 검색 중심 구조**

- 현재는 벡터 유사도 검색 비중이 크며, `"CWE-89"`, `"PreparedStatement"` 같은 정확한 키워드 매칭이 중요한 보안 질의에는 한계가 있습니다.
- 향후에는 BM25 같은 키워드 검색과 벡터 검색을 섞는 하이브리드 retrieval이 필요합니다.

**4. 정적 데이터베이스 성격**

- NVD CVE는 계속 업데이트되지만, 현재 파이프라인은 데이터 재수집과 재색인이 자동화되어 있지 않아 최신 취약점 반영이 지연될 수 있습니다.
- 따라서 운영 단계에서는 주기적 동기화 잡이나 incremental update 체계가 필요합니다.

### L3

L3는 이번 단계에서 로컬 `SonarQube`와 Docker 기반 PoC, `Syft` 기반 SBOM 경로까지 실제로 연동되면서 “심화 검증 레이어”로서의 형태를 갖추게 되었습니다. 특히 SonarCloud에 의존하지 않고 Docker로 띄운 로컬 SonarQube를 지원하게 되면서, 레포 업로드 없이도 로컬 프로젝트를 대상으로 L3를 구성할 수 있게 된 점은 실제 활용성과 시연 안정성 모두에 의미가 있었습니다.

다만 PoC 템플릿과 Docker 검증 환경은 아직 시연 친화적인 특정 시나리오 중심으로 구성되어 있어, 다양한 CWE를 일반화해 다루는 수준까지는 가지 못했습니다. 현재 구조는 Dispatcher와 템플릿 레지스트리 덕분에 확장 가능성은 확보했지만, 실제 운영 수준으로 가려면 CWE별 템플릿 수, 입력 다양성, 성공/실패 판정 기준을 더 풍부하게 만들어야 합니다.

또한 Sonar 계층은 예전 SonarCloud free tier 한계를 의식해 설계된 부분이 있었고, 현재는 로컬 SonarQube 지원으로 이를 일부 보완했지만, 여전히 룰셋 커버리지와 취약점 정탐률은 지속적으로 개선해야 합니다. 장기적으로는 Semgrep, Sonar, 자체 규칙 엔진, 공급망 분석 결과를 더 정교하게 결합하여 L3에서도 보다 높은 정탐률과 설명 가능성을 확보하는 방향으로 발전시킬 계획입니다.
