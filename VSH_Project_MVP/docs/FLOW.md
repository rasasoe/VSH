# Process Flows

## Domain Model Flow

Domain Model은 레이어 간 데이터 전달의 핵심이며, 모든 레이어는 이 모델을 기준으로 통신합니다.

### Data Flow Diagram

1. **Scanner (L1)**: 소스 파일을 읽고 취약점을 탐지하여 `ScanResult` 객체를 생성합니다.
   - `ScanResult(findings=[Vulnerability(...)])`

2. **Pipeline**: `ScanResult.is_clean()` 메서드로 취약점 유무를 판단합니다.
   - **Clean**: 추가 처리 없이 종료.
   - **Vulnerable**: `ScanResult` 객체를 Analyzer(L2)로 전달합니다.

3. **Analyzer (L2)**: 취약점 분석 후 수정 제안을 담은 `FixSuggestion` 객체를 생성합니다.
   - `FixSuggestion(issue_id, original_code, fixed_code, description)`

4. **Repository**: `FixSuggestion` 및 `ScanResult` 정보를 DB에 저장합니다.

---

### Layer Dependency

`Pipeline` -> `models`
`Scanner` -> `models`
`Analyzer` -> `models`
`Repository` -> `models`

모든 레이어는 `models` 패키지에 정의된 클래스에 의존하며, 레이어 간에는 객체 인스턴스로 데이터를 주고받습니다.

---

## Repository Layer Flow

Repository 레이어는 상위 레이어가 데이터의 물리적 저장소에 관계없이 동일한 인터페이스로 데이터를 다룰 수 있게 합니다.

### Inheritance Structure
- **BaseReadRepository (Abstract)**
  - `MockKnowledgeRepo`: `knowledge.json` 보안 지식 읽기 전용
  - `MockFixRepo`: `kisa_fix.json` 수정 가이드 읽기 전용
- **BaseWriteRepository (Abstract, extends BaseReadRepository)**
  - `MockLogRepo`: `log.json` 분석 결과 로그 읽기/쓰기/상태 업데이트

### Mock to Real DB Migration
나중에 실제 Vector DB(ChromaDB 등)나 RDBMS로 교체할 때:
1. `BaseRepository` 인터페이스를 상속받는 새로운 클래스(예: `ChromaRepo`)를 구현합니다.
2. `PipelineFactory` 등 객체를 조립하는 부분에서 `MockRepo` 대신 `ChromaRepo`를 주입하도록 설정만 변경합니다.
3. 상위 레이어(`Pipeline`, `Tools`)의 비즈니스 로직 코드는 일절 수정하지 않아도 동작이 유지됩니다.

---

## Entire L1 → L2 Pipeline Flow (Step 5)

이 흐름은 `AnalysisPipeline.run(file_path)` 호출 시 내부적으로 오케스트레이션 되는 전체 과정입니다.

1. **입력 수신**: `file_path` 문자열
2. **L1 스캔 (탐지)**: 
   - 주입된 3개의 스캐너(`Semgrep`, `TreeSitter`, `SBOM`)를 차례대로 실행하여 각각의 `ScanResult` 반환. (언어 미지원 등 예외 발생 시 `WARN` 로그만 남기고 스킵)
3. **통합 및 중복 제거**:
   - 수집된 모든 `findings` 통합.
   - `_deduplicate()` 메서드(`cwe_id` + `line_number` 기준)로 중복된 취약점 제거.
4. **분석 분기**:
   - 중복 제거된 findings로 통합 `ScanResult` 생성.
   - 결과가 안전하다면(`is_clean == True`), 빈 결과 dict 반환 후 종료.
5. **L2 분석 (심층 분석 및 수정 제안)**:
   - `knowledge_repo.find_all()`과 `fix_repo.find_all()`을 통해 전체 데이터를 가져옴.
   - `analyzer.analyze()` 호출 (LLM API 1회 통합 호출 수행).
6. **로깅 및 상태 추적**:
   - Analyzer가 반환한 `fix_suggestions`를 순회하며 `LogRepo`에 초기 상태(`status="pending"`)와 함께 상세 정보(`severity`, `code_snippet` 등) 저장.
7. **출력 반환**:
   - `scan_results`와 `fix_suggestions` 객체들을 JSON으로 직렬화할 수 있는 `dict` 리스트 형태로 변환하여 최종 반환.

### Real Semgrep 교체 전략 (Migration)
나중에 Windows 환경이 아닌 곳에서 실제 Semgrep을 사용할 경우:
- `modules/scanner/semgrep_scanner.py` 구현 (CLI 호출 방식).
- `modules/__init__.py` 수정:
  ```python
  # 기존
  from .scanner.mock_semgrep_scanner import MockSemgrepScanner as SemgrepScanner
  # 변경
  from .scanner.semgrep_scanner import SemgrepScanner
  ```
- 이 변경만으로 나머지 모든 시스템(`Pipeline`, `Tools`)은 수정 없이 실제 Semgrep을 사용하게 됩니다.
