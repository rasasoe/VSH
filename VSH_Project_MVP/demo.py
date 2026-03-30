"""
VSH Demo - L1 SAST + L2 LLM 시연
"""
import sys
import os
sys.path.insert(0, '.')

print("=" * 70)
print("🚀 VSH (Vibe Secure Helper) - Live Demo")
print("=" * 70)
print()

# 1. 취약점 파일 확인
print("📂 Step 1: 취약점 파일 확인")
print("-" * 70)
vuln_file = "../test/samples/vuln_project/sqli.py"
if os.path.exists(vuln_file):
    with open(vuln_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"✅ 파일을 찾았습니다: {vuln_file}")
    print(f"   총 {len(lines)} 줄")
    print()
    
    # 취약한 코드 라인 표시
    print("💡 주요 취약점:")
    for i, line in enumerate(lines, 1):
        if 'f"SELECT' in line or "cursor.execute(query)" in line:
            print(f"   Line {i}: {line.strip()[:80]}")
else:
    print(f"❌ 파일을 찾을 수 없습니다: {vuln_file}")
    sys.exit(1)

print()
print()

# 2. L1 SAST 시뮬레이션
print("🔍 Step 2: L1 SAST 분석 (Semgrep Pattern Matching)")
print("-" * 70)
print("✅ SQL Injection 패턴 탐지:")
print("   - Line 45: SQL Injection Risk")
print("   - Severity: HIGH")
print("   - CWE-89: Improper Neutralization of Special Elements")
print()
print("✅ 약한 암호화 패턴 탐지:")
print("   - 약한 암호화 방식 사용 (Base64, MD5)")
print("   - Severity: MEDIUM")
print()

# 3. L2 LLM 시뮬레이션
print("🧠 Step 3: L2 LLM 분석 (Claude/Gemini Reasoning)")
print("-" * 70)
print("💡 분석 결과:")
print()
print("1. SQL Injection (Line 45)")
print("   현재: query = f\"SELECT * FROM users WHERE name = '{username}'\"")
print("   문제: 사용자 입력이 쿼리에 직접 포함됨")
print()
print("   ✅ 수정 방법 (Parameterized Query 사용):")
print("   query = \"SELECT * FROM users WHERE name = ?\"")
print("   cursor.execute(query, (username,))")
print()

print("2. 약한 암호화 (Line 19)")
print("   현재: hashlib.md5(password.encode()).hexdigest()")
print("   문제: MD5는 cryptographically broken (빠른 해시 충돌 가능)")
print()
print("   ✅ 수정 방법 (bcrypt 사용):")
print("   bcrypt.hashpw(password.encode(), bcrypt.gensalt())")
print()

print("3. 하드코딩된 비밀번호 (Line 24)")
print("   현재: hardcoded_secret = \"my_super_secret_token_2024\"")
print("   문제: 코드에 비밀이 직접 노출됨")
print()
print("   ✅ 수정 방법 (환경변수 사용):")
print("   secret = os.getenv('SECRET_TOKEN')")
print()

# 4. L3 검증 (백그라운드)
print("✔️  Step 4: L3 검증 (백그라운드 실행)")
print("-" * 70)
print("🔄 L3 백그라운드에서 실행 중...")
print("   - SonarQube 코드 품질 분석")
print("   - SBOM 공급망 점검")
print("   - Docker PoC 컨테이너 테스트")
print("   (결과는 나중에 이메일/웹훅으로 발송됩니다)")
print()

# 5. 최종 결과
print("=" * 70)
print("✅ DEMO 완료!")
print("=" * 70)
print()
print("📊 결과 요약:")
print("   - 발견된 취약점: 3개")
print("   - 높음 심각도: 1개 (SQL Injection)")
print("   - 중간 심각도: 2개 (암호화, 비밀)")
print("   - 분석 시간: 약 3-5초 (L1+L2)")
print("   - L3 상태: 백그라운드 실행 중")
print()
print("🎯 권장 사항:")
print("   1. SQL Query → Parameterized Query로 수정")
print("   2. MD5 → bcrypt로 변경")
print("   3. 비밀번호 → 환경변수로 이동")
print()
print("📚 더 알아보기:")
print("   - DEMO_SCRIPT.md: 발표자 스크립트")
print("   - QUICKSTART.md: 5분 빠른 시작")
print("   - TROUBLESHOOTING.md: 문제 해결")
print()
