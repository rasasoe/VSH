# API Reference

## Domain Models (models/)
`models/` 패키지에 정의된 도메인 모델들은 시스템의 모든 레이어 간 데이터 교환의 기준이 됩니다.

### ScanResult
스캐너(L1)가 생성하는 전체 스캔 결과 모델.

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `file_path` | `str` | 스캔 대상 파일 경로 |
| `language` | `str` | 파일의 언어 (예: python) |
| `findings` | `list[Vulnerability]` | 발견된 취약점 리스트 (기본값: 빈 리스트) |

**Methods:**
- `is_clean() -> bool`: 발견된 취약점이 하나도 없으면 `True`를 반환합니다.

---

### Vulnerability
단일 취약점 정보를 담는 모델.

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `cwe_id` | `str` | CWE ID (예: CWE-78) |
| `severity` | `str` | 취약점 심각도 (**HIGH**, **MEDIUM**, **LOW** 중 하나) |
| `line_number` | `int` | 취약점이 발견된 라인 번호 |
| `code_snippet` | `str` | 취약점이 포함된 코드 조각 |

**Validation:**
- `severity` 필드는 반드시 "HIGH", "MEDIUM", "LOW" 중 하나의 값이어야 하며, 그 외 입력 시 `ValueError`가 발생합니다.

---

### FixSuggestion
분석기(L2)가 제안하는 취약점 수정 정보.

| 필드명 | 타입 | 설명 |
|--------|------|------|
| `issue_id` | `str` | 취약점 ID |
| `original_code` | `str` | 수정 전 원본 코드 |
| `fixed_code` | `str` | 수정 후 제안 코드 |
| `description` | `str` | 수정 내용에 대한 설명 |

---

## Repository Layer (repository/)

### BaseReadRepository (Abstract)
읽기 전용 저장소를 위한 인터페이스.

- `find_by_id(id: str) -> dict | None`: ID로 항목 조회. 없으면 `None` 반환.

### BaseWriteRepository (Abstract)
읽기/쓰기가 가능한 저장소를 위한 인터페이스. `BaseReadRepository` 상속.

- `save(data: dict) -> bool`: 데이터 저장 및 업데이트. 성공 시 `True` 반환.
- `update_status(id: str, status: str) -> bool`: 항목의 처리 상태를 업데이트.

---

### MockKnowledgeRepo
보안 지식 베이스(`knowledge.json`) 조회 담당. `BaseReadRepository` 상속.

- `find_by_id(id: str) -> dict | None`: CWE ID로 보안 규칙 및 패턴 조회.

### MockFixRepo
KISA 수정 가이드(`kisa_fix.json`) 조회 담당. `BaseReadRepository` 상속.

- `find_by_id(id: str) -> dict | None`: CWE ID로 수정 코드 템플릿 및 설명 조회.

### MockLogRepo
분석 로그(`log.json`) 기록 및 상태 관리 담당. `BaseWriteRepository` 상속.

- `save(data: dict) -> bool`: 분석 결과를 로그에 기록. `issue_id` 중복 시 기존 항목 업데이트.
- `update_status(id: str, status: str) -> bool`: 특정 이슈의 진행 상태(`pending`, `accepted`, `dismissed`) 변경.
  - `ValueError`: 허용되지 않은 `status` 값 입력 시 발생.
