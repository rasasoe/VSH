# 🛡️ VSH v1.0 - Vibe Secure Helper

**VSH(Vibe Secure Helper)** 는 실시간 AppSec 가로채기(interceptor) 도구로, 코드 취약점, 공급망 보안, 패키지 환각(hallucination) 감지를 통합합니다.

## 🎯 핵심 기능 (v1.0)

### L1 Hot Path (0.3~1.0s)
- **Semgrep 기반 패턴 탐지**: SQL Injection, XSS, Command Injection 등
- **패키지 환각/타이포스쿼팅 감지**: PyPI/npm 레지스트리 존재성 검증
- **SBOM 생성**: syft 지원 (없으면 requirements.txt/package-lock.json 자동 fallback)
- **OSV API 취약점 조회**: 라이브러리 취약점 데이터베이스 조회
- **간이 Reachability**: 소스(외부입력) → 싱크(취약 호출) 간 파일 내 근접성 분석

### 출력
- **IDE 주석 스타일 알림**: 코드 위치에 직접 삽입 가능한 형식
- **Markdown 리포트**: 종합 보안 점수 + 취약점 + 공급망 위험 + 환각 패키지

---

## 📁 프로젝트 구조

```
vsh/
  ├─ pyproject.toml
  ├─ README.md
  ├─ vsh/
  │  ├─ __init__.py
  │  ├─ cli.py                      # 메인 CLI 진입점
  │  ├─ core/
  │  │  ├─ __init__.py
  │  │  ├─ config.py                # VSHConfig 설정 클래스
  │  │  ├─ models.py                # Pydantic 데이터 모델
  │  │  └─ utils.py                 # 공용 유틸리티 함수
  │  ├─ engines/
  │  │  ├─ __init__.py
  │  │  ├─ semgrep_engine.py        # Semgrep 실행
  │  │  ├─ registry_engine.py       # 패키지 존재성 검증
  │  │  ├─ sbom_engine.py           # SBOM 생성
  │  │  ├─ osv_engine.py            # OSV API 조회
  │  │  ├─ reachability_engine.py   # 간이 Reachability
  │  │  └─ report_engine.py         # 리포트 생성
  │  ├─ rules/
  │  │  └─ semgrep/
  │  │     ├─ python.yml            # Python 취약 패턴 룰
  │  │     └─ javascript.yml        # JavaScript 취약 패턴 룰
  │  └─ demo_targets/
  │     ├─ python_sqli.py           # SQL Injection 데모
  │     ├─ js_xss.js                # XSS 데모
  │     └─ python_pkg_hallucination.py  # 패키지 환각 데모
  ├─ scripts/
  │  └─ install_semgrep.sh
  └─ docker/
     ├─ Dockerfile
     └─ docker-compose.yml
```

---

## 🚀 빠른 시작

### 1️⃣ 환경 설정

#### Windows 환경
```powershell
# Python 3.10+ 필요
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -e .
pip install semgrep
```

#### Linux/macOS 환경
```bash
python -m venv .venv
source .venv/bin/activate

pip install -e .
pip install semgrep
```

### 2️⃣ 데모 스캔

```bash
# Python 데모 스캔 (SQL Injection + 패키지 환각)
vsh vsh/demo_targets --out vsh_out --lang python --no-syft

# JavaScript 데모 스캔 (XSS)
vsh vsh/demo_targets --out vsh_out --lang javascript --no-syft
```

### 3️⃣ 결과 확인

```bash
# 콘솔 출력
# ✅ 요약 표(findings, 공급망 취약점, 환각 패키지 개수, 보안 점수)
# ✅ 인라인 주석 스타일 알림 (장성 문제가 있는 파일별)
# ✅ 패키지 환각 목록

# 마크다운 리포트
cat vsh_out/VSH_REPORT.md
```

---

## 🔧 명령어 옵션

```bash
vsh <project_path> [OPTIONS]

옵션:
  --out <dir>           # 출력 디렉토리 (기본값: vsh_out)
  --lang <lang>         # 강제 언어 설정 (python|javascript, 기본값: auto detect)
  --no-syft             # syft 비활성화 (fallback 사용)
```

### 예시

```bash
# 특정 프로젝트 스캔
vsh /path/to/myproject --out results --lang python

# syft 없이 스캔
vsh . --no-syft

# JavaScript 프로젝트
vsh ./frontend --lang javascript
```

---

## 📊 출력 형식

### 콘솔 요약
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ VSH Scan Summary                                          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Type                     │ Count                          │
├──────────────────────────┼────────────────────────────────┤
│ Code Findings            │ 1                              │
│ Dependency Vulns (OSV)   │ 0                              │
│ Hallucinated Packages    │ 1                              │
│ Score                    │ 65 / 100                       │
└──────────────────────────┴────────────────────────────────┘
```

### 인라인 주석 (IDEe 주석 삽입용)
```python
# ⚠️ [VSH 알림] SQL Injection 가능성: 사용자 입력이 쿼리에 직접 결합됩니다.
# ─────────────────────────────────────────────────
# 위험도      : ★★★★★ CRITICAL | CVSS 9.8
# 취약점      : CWE-89
# CVE         : CVE-2023-32315
# Reachability: ✅ 실제 도달 가능
#
# 💬 메시지   : SQL Injection 가능성: 사용자 입력이 쿼리에 직접 결합됩니다.
#
# 🔧 권장 수정 코드:
# query = "SELECT * FROM users WHERE id = %s"; cursor.execute(query, (user_input,))
```

### Markdown 리포트 (`vsh_out/VSH_REPORT.md`)
```markdown
# 🛡️ VSH 보안 진단 리포트

**프로젝트명** : demo_targets
**진단일시**   : 2026-02-20 14:30:45
**진단엔진**   : VSH v1.0 (Semgrep + SBOM + OSV + Registry Check)

## 📊 종합 보안 점수 : 65 / 100

## 🚨 코드 취약점
### [CRITICAL] SQL Injection 가능성 — `python_sqli.py:6`
- **ID**           : VSH-PY-SQLI-001
- **CWE**          : CWE-89
- **CVE**          : CVE-2023-32315
- **CVSS**         : 9.8
- **Reachability** : YES
- **메시지**       : SQL Injection 가능성: 사용자 입력이 쿼리에 직접 결합됩니다.
- **조치**         : query = "SELECT * FROM users WHERE id = %s"; cursor.execute(query, (user_input,))
- **참고**         : KISA 시큐어코딩 가이드 - 입력데이터 검증 및 표현

## 📦 공급망 / 라이브러리 취약점 (OSV)
- 탐지된 라이브러리 취약점 없음(또는 조회 실패)

## 🧨 패키지 환각 / 존재성 이상
- ❌ 레지스트리 미존재 의심: `reqeusts`
```

---

## 🎬 발표 데모 시나리오 (2분)

1. **SQL Injection 탐지**
   ```bash
   vsh vsh/demo_targets --lang python --no-syft
   ```
   - 결과: `python_sqli.py` 에서 **CRITICAL** SQLi 발견
   - Reachability: **YES** (실제 도달 가능)

2. **패키지 환각 감지**
   - 결과: `python_pkg_hallucination.py` 에서 `reqeusts` 미존재
   - 타이포스쿼팅 공격 예방 가능

3. **Markdown 리포트 검토**
   - `vsh_out/VSH_REPORT.md` 열기
   - 종합 점수 65/100 확인
   - 취약점, 공급망, 환각 항목 검토

---

## 🔐 지원 언어 & 취약점 유형 (v1.0)

### Python 규칙
- **VSH-PY-SQLI-001**: SQL Injection (f-string)
- **VSH-PY-SECRET-001**: 하드코딩된 Secret Key
- **VSH-PY-CMDI-001**: Command Injection

### JavaScript 규칙
- **VSH-JS-XSS-001**: DOM XSS (innerHTML)

### 공급망 (SBOM/OSV)
- PyPI 라이브러리
- npm 패키지

### 패키지 검증
- PyPI 레지스트리 존재성 확인
- npm 레지스트리 존재성 확인

---

## 🛠️ 의존성

### 필수
- Python >= 3.10
- `pydantic>=2.6`
- `rich>=13.7`
- `pyyaml>=6.0`
- `requests>=2.31`
- `semgrep` (자동 설치 아님, 수동 설치 권장)

### 선택
- `syft`: SBOM 생성 (없으면 requirements.txt/package-lock.json 사용)

---

## 📦 설치 및 개발

### 소스에서 설치
```bash
git clone <repo>
cd vsh
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
pip install semgrep
```

### Docker 실행
```bash
cd docker
docker-compose up
```

---

## 🚧 알려진 제한사항 (v1.0)

- **Reachability**: 간단한 휴리스틱 기반 (taint 분석 미포함)
- **Semgrep 룰**: 데모 목적의 기본 룰만 포함 (확장 가능)
- **OSV API**: 네트워크 필수 (오프라인 미지원)
- **동적 분석**: 정적 분석만 지원

---

## 📚 다음 스텝 (v2.0+)

- [ ] FastMCP 서버 (Cursor/Claude 에이전트 연동)
- [ ] SonarQube 연동 (L3 분석)
- [ ] CI/CD 파이프라인 (GitHub Actions)
- [ ] KISA/금융보안원 RAG DB 통합 (근거 자동 인용)
- [ ] 고도화된 Reachability (Tree-sitter + taint 분석)
- [ ] 실시간 IDE 플러그인 (VS Code)

---

## ⚠️ Codespaces / 컨테이너 환경 주의 및 설치 팁

GitHub Codespaces(또는 일부 컨테이너 기반 개발환경)는 시스템 Python을 배포 패키지 관리자(apt)로 관리하고 PEP 668 정책을 적용합니다. 이로 인해 다음과 같은 제약이 있습니다:

- `pip install`이 시스템 site-packages에 바로 쓰기를 차단할 수 있습니다 ("externally-managed-environment").
- 컨테이너 이미지에 `python3-venv`/`ensurepip`가 없어 `python -m venv`가 실패할 수 있습니다.

해결/권장 방법:

- 권장(로컬/권한 있는 환경): 가상환경 생성 후 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install semgrep
```

- Codespaces에서 권한이 제한될 때(임시 대안): 사용자 설치 또는 --break-system-packages 사용

```bash
python3 -m pip install --break-system-packages -e . rich pydantic pyyaml requests tqdm pytest
# 또는 컨테이너 이미지에 python3-venv 패키지를 추가하여 venv 생성 가능하도록 구성
```

참고: 가능한 경우 DevContainer 정의나 CI 워크플로에서 `python3-venv`를 미리 설치하도록 설정하는 게 가장 안정적입니다.

## 🧾 SBOM(소프트웨어 구성 정보) 생성

VSH는 SBOM 생성을 위해 기본적으로 `syft`를 사용합니다. syft가 없으면 `requirements.txt` 또는 `package-lock.json`을 fallback으로 사용합니다.

- syft 사용 예:

```bash
# syft가 설치되어 있을 때
vsh <project> --out results --lang python
```

- fallback(Requirements) 사용 예 (빠른 대체 방법):

```bash
# 현재 환경 패키지를 requirements.txt로 만들고 스캔
python -m pip freeze > demo_targets/requirements.txt
vsh demo_targets --out vsh_out_with_requirements --no-syft --lang python
```

이번 리포트에서는 `vsh/demo_targets/requirements.txt` 를 생성해 SBOM fallback을 사용하여 `vsh_out_req_scan/VSH_REPORT.md` 를 만들었습니다.

### SBOM 상세(알고리즘 및 버전 수집 방식)

VSH의 SBOM 생성은 단계적(fallback) 알고리즘으로 동작합니다:

1. syft 실행(우선)
   - 외부 바이너리 `syft`를 실행해 JSON 출력을 파싱합니다.
   - syft 출력의 각 `artifact`에서 `name`, `version`, `purl` 등을 읽어 패키지와 버전을 결정합니다. `purl`에 `pypi`나 `npm` 문자열이 포함되어 있으면 생태계(`PyPI`/`npm`)를 판단합니다.

2. syft 미사용 또는 실패 시 (fallback)
   - `requirements.txt`가 존재하면 각 라인을 파싱합니다.
     - `==`로 고정된 항목(`name==1.2.3`)은 그대로 `name`과 `version`을 기록합니다.
     - 버전이 명시되지 않은 항목은 `version: null`로 기록합니다.
   - `package-lock.json`이 존재하면 잠금파일의 `packages` 또는 `dependencies`에서 패키지 이름과 `version`을 추출합니다.

3. 아무 것도 없으면 빈 SBOM(`{"source":"none","packages":[]}`)

버전 정보 출처 요약:
- `syft`: 설치된/분석된 아티팩트 메타데이터에서 직접 추출 (가장 신뢰도 높음)
- `requirements.txt`: 파일에 명시된 버전(또는 `pip freeze`로 생성된 결과)
- `package-lock.json`: 잠금파일에 기록된 `version`

이번 저장소에서 생성된 SBOM 예시:
- 파일 위치: `vsh_out_req_scan/sbom.json`
- 출처: `requirements.txt` fallback
- 포함 패키지 수: 126 (예시값)

한계 및 권장 사항:
- `pip freeze`로 만든 `requirements.txt`는 실행 환경에 설치된 모든 패키지를 덤프하므로 프로젝트에 필요한 최소 의존성만 포함하지 않을 수 있습니다. (SBOM이 과다해질 수 있음)
- 정확한 SBOM이 필요하면 프로젝트 전용 가상환경에서 `syft`로 생성하거나, 프로젝트의 잠금파일을 정확히 관리하세요.
- CI에서 안정적으로 SBOM을 생성하려면 워크플로에서 가상환경을 만들고(deps 설치 후) `syft`를 실행하는 것이 좋습니다.

추가: SBOM을 CycloneDX 또는 SPDX 포맷으로 변환해서 저장/업로드할 수 있도록 향후 기능을 고려하고 있습니다.

## .gitignore 권장 항목

프로젝트에 불필요한 아티팩트(.venv, vsh_out 등)가 포함되지 않도록 아래 항목들을 `.gitignore`에 추가하시길 권장합니다:

```
.venv/
vsh_out*
vsh_out_test_*
*.pyc
__pycache__/
```

## 📞 문의 & 기여

- 이슈: [GitHub Issues](https://github.com/your-repo/issues)
- Pull Requests 환영합니다!

---

**Made with ❤️ by Vibe Security Team**

VSH v1.0.0 | 2026-02-20
