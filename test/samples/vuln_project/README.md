# Vulnerable Project - VSH Testing Fixtures

이 프로젝트는 **의도적으로 취약점을 포함**하고 있으며 SAST 도구 테스트용입니다.

## 파일별 취약점

### sqli.py
- **SQL Injection**: 직접 문자열 연결로 SQL 쿼리 생성
- **취약 코드**: `query = "SELECT * FROM users WHERE name = '" + username + "'"`
- **영향**: 데이터베이스 접근 제어 우회, 데이터 유출

### weak_crypto.py
- **Hardcoded Secrets**: API 키, 토큰이 코드에 하드코딩됨
- **약한 해시**: MD5 사용 (cryptographically broken)
- **가짜 암호화**: Base64를 암호화처럼 사용
- **취약 코드**: `API_KEY = "sk_test_..."`
- **영향**: 보안 자격증명 노출, 약한 암호화

### command_injection.py
- **Command Injection**: 사용자 입력이 OS 명령어에 직접 포함
- **Code Injection**: eval() 사용으로 임의 코드 실행
- **취약 코드**: `subprocess.run(f"ping {host}", shell=True)`
- **영향**: 원격 코드 실행 (RCE), 시스템 제어 탈취

## 사용 방법

```bash
# VSH로 취약점 스캔
python scripts/vsh_cli.py scan-file tests/fixtures/vuln_project/sqli.py

# 전체 프로젝트 스캔
python scripts/vsh_cli.py scan-project tests/fixtures/vuln_project/
```

## 이 취약점들이 탐지되는 이유

| 도구 | 탐지 방식 |
|------|---------|
| **L1 (Semgrep)** | 패턴 매칭: `f"...{user_input}..."`, `eval()`, `subprocess(...shell=True)` |
| **L2 (Claude/Gemini)** | 컨텍스트 분석: 입력 출처, 사용처, 완화 방법 |
| **L3 (SonarQube)** | 코드 흐름 분석: 데이터 플로우, 신뢰도 경계 |

## ⚠️ 주의

**프로덕션에 사용하지 마십시오!** 이 코드는 교육 및 테스트 목적으로만 작성되었습니다.

## 수정된 버전

각 파일의 `Safe...` 클래스/함수를 참고하면 안전한 패턴을 확인할 수 있습니다.

예:
- ✅ Parameterized queries for SQL
- ✅ Environment variables for secrets
- ✅ Subprocess list format (no shell) for commands
