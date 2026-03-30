# L1 / Semgrep 알고리즘 상세 설명

## 문서 목적

이 문서는 팀원들에게 현재 VSH의 `L1`이 어떤 방식으로 동작하는지 설명하기 위한 문서입니다.

중요한 전제부터 먼저 정리하면:

- 현재 레포의 L1은 이름상 `Semgrep` 계층을 포함하지만
- 실제 Semgrep CLI 바이너리를 실행하는 구조는 아닙니다.
- 현재 구현은 `Semgrep 스타일 규칙 기반 탐지`를 경량화해서 직접 구현한 형태입니다.

즉, 팀 설명 시에는 아래처럼 말하는 것이 가장 정확합니다.

> 현재 VSH L1은 실제 Semgrep 바이너리 호출이 아니라, 정규식 기반 규칙 매칭 + 구조 보조 스캐너 + reachability 추정 + 정규화 파이프라인으로 구성된 Semgrep-like 탐지 계층이다.

---

## 1. 전체 L1 구성

현재 L1의 메인 진입점은 [`layer1/scanner/vsh_l1_scanner.py`](/a:/VSH-main/VSH_Project_MVP/layer1/scanner/vsh_l1_scanner.py) 입니다.

이 스캐너는 내부적으로 여러 하위 탐지기를 조합합니다.

1. `MockSemgrepScanner`
2. `TreeSitterScanner` (사용 가능할 때만)
3. `pattern_scan`
4. `import_risk` 기반 typosquatting 탐지
5. `SBOMScanner`
6. `reachability` annotation
7. `deduplicate_findings`
8. `normalize_scan_result`

즉 L1은 단일 엔진이 아니라, 여러 탐지 결과를 모아서 하나의 `ScanResult`로 만드는 통합 스캐너입니다.

---

## 2. 파일/프로젝트 스캔 흐름

### 파일 스캔

`_scan_file()` 흐름은 대략 아래 순서입니다.

1. 언어 추정
2. `_scan_single_file_findings()` 호출
3. `annotate_reachability()` 적용
4. `SBOMScanner` 결과 병합
5. `deduplicate_findings()`
6. `normalize_scan_result()`

### 프로젝트 스캔

`_scan_project()`는 프로젝트 전체를 순회하면서 확장자가 아래 집합에 포함되는 파일만 분석합니다.

- `.py`
- `.js`
- `.jsx`
- `.ts`
- `.tsx`
- `.mjs`

각 파일별로:

1. 언어 추정
2. `_scan_single_file_findings()`
3. `annotate_reachability()`
4. 전체 findings에 누적

그 후:

5. 프로젝트 기준 `SBOMScanner` 결과 추가
6. dedup
7. `project_languages=...` note 추가
8. `normalize_scan_result()`

---

## 3. MockSemgrepScanner의 원리

구현 파일:

- [`layer1/scanner/mock_semgrep_scanner.py`](/a:/VSH-main/VSH_Project_MVP/layer1/scanner/mock_semgrep_scanner.py)

이 스캐너는 `knowledge_repo.find_all()`에서 규칙 목록을 읽고, 파일을 한 줄씩 읽으면서 각 줄에 대해 `re.search(pattern, line)`를 수행합니다.

즉 알고리즘은 매우 단순합니다.

1. 지식 저장소에서 규칙 목록 로드
2. 파일을 line-by-line으로 읽음
3. 각 줄에 대해 모든 pattern을 순회
4. 정규식이 매칭되면 `Vulnerability` 생성
5. findings 배열에 추가

### 특징

- Python 파일에만 적용됨
- 규칙 출처는 knowledge repository
- 패턴은 문자열 정규식 기반
- AST 구조를 직접 보지 않음
- 줄 단위 매칭이기 때문에 빠르지만 문맥 이해가 제한적임

### 장점

- 구현이 단순하고 빠름
- 지식 저장소만 바꾸면 규칙 추가가 쉬움
- 데모와 초기 탐지 계층으로 적합

### 한계

- 실제 Semgrep처럼 AST 구조 제약을 강하게 걸지 못함
- 여러 줄에 걸친 구조는 잘 못 잡음
- false positive / false negative 가능성이 큼
- line context만 보고 판단하므로 의미 기반 분석이 약함

---

## 4. pattern_scan의 원리

구현 파일:

- [`layer1/common/pattern_scan.py`](/a:/VSH-main/VSH_Project_MVP/layer1/common/pattern_scan.py)

`pattern_scan`은 knowledge repo 기반이 아니라, 코드 안에 하드코딩된 룰 집합을 사용합니다.

예시 룰:

- `VSH-PY-EVAL-001`
- `VSH-PY-SUBPROCESS-001`
- `VSH-PY-OS-SYSTEM-001`
- `VSH-JS-XSS-001`
- `VSH-JS-DOCUMENT-WRITE-001`

동작 원리:

1. 파일 언어 추정
2. Python 또는 JS/TS 룰셋 선택
3. 파일 전체를 읽고 line-by-line 순회
4. 각 줄에 대해 rule pattern을 `re.search()`로 검사
5. `(rule_id, line_number, line.strip())` 기준으로 중복 방지
6. `Vulnerability` 생성

### 핵심 포인트

이 계층은 현재 실질적으로 가장 중요한 L1 규칙 탐지기입니다.

이유:

- `rule_id`
- `cwe_id`
- `severity`
- `references`
- `engine=vsh_pattern`

같은 정형 정보가 명확하게 들어가므로, 후단 L2/L3와 연결하기가 쉽습니다.

---

## 5. Tree-sitter 보조 탐지

구현 파일:

- [`layer1/scanner/treesitter_scanner.py`](/a:/VSH-main/VSH_Project_MVP/layer1/scanner/treesitter_scanner.py)

`VSHL1Scanner`는 `TreeSitterScanner`를 import할 수 있으면 같이 사용합니다.

역할은 다음과 같습니다.

- 소스 코드를 구조적으로 파싱
- 특정 snippet 또는 패턴과의 정합성을 보조
- 문자열 정규식보다 구조적인 힌트를 일부 제공

다만 현재 레포 기준으로는 Tree-sitter가 L1 전체를 주도하는 엔진이 아니라, 보조적인 구조 탐지기입니다.

즉 현재 L1의 실질적인 중심은 여전히 `pattern_scan`과 `MockSemgrepScanner`입니다.

---

## 6. Reachability 추정 원리

구현 파일:

- [`layer1/common/reachability.py`](/a:/VSH-main/VSH_Project_MVP/layer1/common/reachability.py)

이 단계는 탐지된 finding에 대해 “실제로 입력(source)에서 위험 sink까지 닿을 가능성이 있는가?”를 거칠게 추정합니다.

### 사용되는 개념

- `source pattern`
  - Python: `input()`, `request.args`, `request.form`, `sys.argv`, `os.environ` 등
  - JavaScript: `req.body`, `window.location`, `document.URL` 등
- `sink pattern`
  - Python: `eval`, `subprocess`, `os.system`, `.execute` 등
  - JavaScript: `innerHTML`, `eval`, `document.write` 등

### 처리 단계

1. 파일 전체에서 source line 찾기
2. 파일 전체에서 sink line 찾기
3. 함수 정의 경계 추출
4. 함수 호출 그래프(call graph) 생성
5. source가 있는 함수 집합 계산
6. source에서 도달 가능한 함수 집합 계산
7. 각 finding이 있는 함수가 reachable인지 판정

### 판정 결과

- `reachable`
- `conditionally_reachable`
- `unknown`
- `unreachable`

### 이 알고리즘의 의미

이건 정적 taint analysis 엔진 수준의 정밀한 데이터 흐름 분석은 아닙니다.
대신 “간단한 함수 경계 + 호출 그래프 + source/sink 룰”을 이용한 lightweight reachability annotation입니다.

즉:

- 빠름
- 설명 가능함
- 구현 단순함
- 하지만 깊은 interprocedural analysis는 아님

---

## 7. Typosquatting / SBOM 보조 경로

### Typosquatting

구현 위치:

- [`layer1/common/import_risk.py`](/a:/VSH-main/VSH_Project_MVP/layer1/common/import_risk.py)

역할:

- import / requirement 기반으로 의심 패키지 사용 탐지
- 공급망 리스크를 L1 finding으로 추가

### SBOMScanner

구현 위치:

- [`layer1/scanner/sbom_scanner.py`](/a:/VSH-main/VSH_Project_MVP/layer1/scanner/sbom_scanner.py)

역할:

- 프로젝트 또는 파일 기준 패키지/의존성 관련 리스크를 findings 또는 package_records로 연결
- 후속 L2/L3에서 활용할 수 있는 package 관점 데이터 생성

---

## 8. Dedup과 Normalize

### Dedup

구현 위치:

- `shared.finding_dedup`

여러 엔진이 같은 줄, 같은 취약점을 동시에 잡을 수 있기 때문에 중복 제거가 필요합니다.

L1은 여러 스캐너 결과를 합친 뒤 `deduplicate_findings()`로 중복을 줄입니다.

### Normalize

구현 파일:

- [`layer1/common/schema_normalizer.py`](/a:/VSH-main/VSH_Project_MVP/layer1/common/schema_normalizer.py)

이 단계에서 L1 결과를 후속 계층이 이해할 수 있는 공통 스키마로 변환합니다.

주요 출력:

- `vuln_records`
- `package_records`
- `notes`

여기서 붙는 대표 필드:

- `vuln_id`
- `rule_id`
- `source='L1'`
- `severity`
- `reachability_status`
- `fix_suggestion`
- `owasp_ref`
- `kisa_ref`

즉 normalize 단계가 있기 때문에, 뒤의 L2/L3는 “스캐너별 제각각 결과”를 직접 다루지 않고 공통 포맷만 보면 됩니다.

---

## 9. 현재 L1을 Semgrep 알고리즘이라고 부를 수 있는가?

엄밀히 말하면 **완전한 의미의 Semgrep 알고리즘은 아닙니다.**

실제 Semgrep은 일반적으로 다음 성격을 가집니다.

- AST 기반 structural pattern matching
- 언어별 parser를 활용한 구조 인식
- metavariable, pattern-inside, pattern-either 같은 구조 규칙 지원
- 단순 문자열 regex보다 코드 구조 중심 탐지

반면 현재 VSH의 L1은:

- 정규식 기반 rule matching
- knowledge 기반 line scan
- 일부 Tree-sitter 보조 구조 탐지
- source/sink + call graph 기반 lightweight reachability
- 다중 엔진 결과 통합

즉 표현을 정확히 하면 다음이 맞습니다.

- 잘못된 표현: “현재 VSH L1은 실제 Semgrep이다.”
- 정확한 표현: “현재 VSH L1은 Semgrep 스타일의 규칙 기반 정적 탐지 계층이다.”

---

## 10. 현재 구조의 장점

### 1. 구현이 단순하다

팀원이 구조를 읽기 쉽고, 룰 추가 비용이 낮습니다.

### 2. 속도가 빠르다

line-by-line 정규식 매칭 중심이라 초기 데모와 반복 시연에 유리합니다.

### 3. 후속 계층과 연결이 쉽다

normalize 단계 덕분에 L2/L3는 공통 스키마만 보면 됩니다.

### 4. 설명 가능성이 높다

“어떤 줄이 어떤 패턴에 걸렸는지”를 보여주기 쉽습니다.

---

## 11. 현재 구조의 한계

### 1. 구조 이해가 약하다

정규식 기반이라 코드 구조를 충분히 이해하지 못합니다.

### 2. 다중 줄/복잡한 흐름에 약하다

한 줄에 드러나지 않는 취약점은 놓치기 쉽습니다.

### 3. false positive가 생기기 쉽다

문맥 없이 sink pattern만 잡아도 취약점으로 볼 수 있습니다.

### 4. reachability도 근사치다

현재 reachability는 정적 taint analysis가 아니라 휴리스틱 기반 call graph 추정입니다.

---

## 12. 팀원 설명용 한 줄 요약

가장 추천하는 설명 문구는 아래입니다.

> VSH의 현재 L1은 실제 Semgrep CLI를 호출하는 구조는 아니고, Semgrep 스타일 규칙 매칭과 보조 구조 분석(Tree-sitter), source/sink 기반 reachability 추정, 공통 스키마 정규화를 결합한 경량 정적 분석 계층입니다.

더 짧게 말하면:

> L1은 “빠른 규칙 기반 정적 탐지 + reachability annotation + normalize”입니다.

---

## 13. 향후 개선 방향

1. 실제 Semgrep CLI 또는 AST rule engine 연동
2. Tree-sitter 구조 탐지 비중 확대
3. rule metadata 체계 강화
4. language별 source/sink 사전 확장
5. interprocedural data-flow 분석 보강
6. watch 모드와 결합한 incremental L1 재분석
7. false positive 감소용 context filter 추가

---

## 14. 관련 코드 경로

핵심 구현 파일:

- [`layer1/scanner/vsh_l1_scanner.py`](/a:/VSH-main/VSH_Project_MVP/layer1/scanner/vsh_l1_scanner.py)
- [`layer1/scanner/mock_semgrep_scanner.py`](/a:/VSH-main/VSH_Project_MVP/layer1/scanner/mock_semgrep_scanner.py)
- [`layer1/common/pattern_scan.py`](/a:/VSH-main/VSH_Project_MVP/layer1/common/pattern_scan.py)
- [`layer1/common/reachability.py`](/a:/VSH-main/VSH_Project_MVP/layer1/common/reachability.py)
- [`layer1/common/schema_normalizer.py`](/a:/VSH-main/VSH_Project_MVP/layer1/common/schema_normalizer.py)
- [`layer1/scanner/treesitter_scanner.py`](/a:/VSH-main/VSH_Project_MVP/layer1/scanner/treesitter_scanner.py)
- [`layer1/scanner/sbom_scanner.py`](/a:/VSH-main/VSH_Project_MVP/layer1/scanner/sbom_scanner.py)
