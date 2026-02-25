# PROGRESS.md — 개발 진행 상태

## 현재 단계: Step 3 준비 중

---

## Step 진행 현황

| Step | 내용 | 상태 | 분기점 통과 |
|------|------|------|------------|
| 0 | 프로젝트 세팅 | 완료 | 260225 |
| 1 | Domain Model | 완료 | 260225 |
| 2 | Repository + Mock DB | 완료 | 260225 |
| 3 | Scanner (L1) | 대기 | - |
| 4 | Analyzer (L2) | 대기 | - |
| 5 | Pipeline | 대기 | - |
| 6 | MCP 툴 등록 | 대기 | - |
| 7 | Dashboard | 대기 | - |
| 8 | E2E 테스트 | 대기 | - |

---

## 각 Step 분기점 체크리스트

### Step 0 — 프로젝트 세팅
- [x] 폴더 구조 생성 완료
- [x] pip install 오류 없음 (Semgrep 제외)
- [x] python -c "import fastmcp, anthropic, fastapi" 오류 없음

### Step 1 — Domain Model
- [x] models/ import 오류 없음
- [x] 모델 간 의존성 방향 올바름
- [x] ScanResult, Vulnerability, FixSuggestion 인스턴스 생성 확인

### Step 2 — Repository + Mock DB
- [x] JSON 파일 정상 로드 확인
- [x] MockRepo 인스턴스 생성 오류 없음
- [x] find_by_id(), save() 호출 결과 확인

### Step 3 — Scanner (L1)
- [ ] 테스트용 취약 파일로 SemgrepScanner 실행 결과 확인
- [ ] TreeSitterScanner Python 파싱 확인
- [ ] SBOMScanner requirements.txt 취약 패키지 탐지 확인
- [ ] supported_languages() 반환값 확인

### Step 4 — Analyzer (L2)
- [ ] L1 결과를 넘겼을 때 Claude API 응답 확인
- [ ] 취약점 판단 결과 파싱 확인 (있음/없음/오탐)
- [ ] 수정 제안 코드 생성 확인

### Step 5 — Pipeline
- [ ] 취약한 파일 → L1 → L2 흐름 정상 실행
- [ ] 아무것도 없는 파일 → clean 반환 확인
- [ ] PipelineFactory 인스턴스 생성 확인

### Step 6 — MCP 툴 등록
- [ ] mcp_server.py 실행 오류 없음
- [ ] validate_code 툴 호출 → 파이프라인 실행 확인
- [ ] get_results 툴 호출 → log.json 반환 확인

### Step 7 — Dashboard
- [ ] localhost:3000 접속 확인
- [ ] 분석 결과 화면 표시 확인
- [ ] Accept 클릭 → 파일 수정 확인
- [ ] Dismiss 클릭 → 로그 기록 확인

### Step 8 — E2E 테스트
- [ ] 취약한 파일 → 대시보드 결과 → Accept → 파일 수정
- [ ] 수정된 파일 재스캔 → clean 처리
- [ ] log.json 전체 이력 기록 확인

---

## 이슈 및 결정 사항 로그

| 날짜 | 내용 |
|------|------|
| 250225 | 아키텍처 설계 확정 (기능+레이어 혼합, OOP 원칙 적용) |
| 250225 | MVP 지원 언어: Python (Tree-sitter) |
| 250225 | 대시보드 포트: 3000 |
| 250225 | 프로젝트 루트: VSH_Project_MVP |
| 260225 | Step 0 완료: 프로젝트 구조 세팅, 의존성 설치, 레이어별 __init__.py 및 클래스 스켈레톤 작성 |
| 260225 | Step 1 완료: Domain Model 구현 (Pydantic 채택 - 데이터 검증 및 직렬화 용이성), 다음: Repository + Mock DB |
| 260225 | Step 2 완료: Repository Layer 구현 및 Mock DB 연동 |
| 260225 | [결정] BaseRead/WriteRepository 분리: LSP 위반 방지 및 읽기 전용 데이터의 무결성 보장 |
| 260225 | [결정] find_by_id() 반환값: 항목 부재 시 None 반환 ({} 반환 시 존재 여부 확인 로직 모호성 제거) |
| 260225 | [결정] config.py 추가: 참조 데이터 경로는 상수로 관리하고 런타임 로그 경로만 .env로 관리 |
