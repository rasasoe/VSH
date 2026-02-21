# 🛡️ VSH 보안 진단 리포트

**프로젝트명** : demo_targets
**진단일시**   : 2026-02-21 01:04:40
**진단엔진**   : VSH v1.0 (Semgrep + SBOM + OSV + Registry Check)

## 📊 종합 보안 점수 : 45 / 100

## 🚨 코드 취약점
### [CRITICAL] SQL Injection 가능성: 사용자 입력이 쿼리에 직접 결합됩니다. — `python_sqli.py:5`
- **ID**           : VSH-PY-SQLI-001
- **CWE**          : CWE-89
- **CVE**          : CVE-2023-32315
- **CVSS**         : 9.8
- **Reachability** : YES
- **메시지**       : SQL Injection 가능성: 사용자 입력이 쿼리에 직접 결합됩니다.
- **조치**         : query = "SELECT * FROM users WHERE id = %s"; cursor.execute(query, (user_input,))
- **참고**         : KISA 시큐어코딩 가이드 - 입력데이터 검증 및 표현

## 📦 공급망 / 라이브러리 취약점 (OSV)
- **PyPI** `cryptography 41.0.7` → `GHSA-3ww4-gg4f-jr7f` : Python Cryptography package vulnerable to Bleichenbacher timing oracle attack
- **PyPI** `cryptography 41.0.7` → `GHSA-6vqw-3v5j-54x4` : cryptography NULL pointer dereference with pkcs12.serialize_key_and_certificates when called with a non-matching certificate and private key and an hmac_hash override
- **PyPI** `cryptography 41.0.7` → `GHSA-9v9h-cgj8-h64p` : Null pointer dereference in PKCS12 parsing
- **PyPI** `cryptography 41.0.7` → `GHSA-h4gh-qq45-vh27` : pyca/cryptography has a vulnerable OpenSSL included in cryptography wheels
- **PyPI** `cryptography 41.0.7` → `GHSA-r6ph-v2qm-q3c2` : cryptography Vulnerable to a Subgroup Attack Due to Missing Subgroup Validation for SECT Curves
- **PyPI** `cryptography 41.0.7` → `PYSEC-2024-225` : cryptography is a package designed to expose cryptographic primitives and recipes to Python developers. Starting in version 38.0.0 and prior to version 42.0.4, 
- **PyPI** `nbconvert 7.16.6` → `GHSA-xm59-rqc7-hhvf` : nbconvert has an uncontrolled search path that leads to unauthorized code execution on Windows
- **PyPI** `python-apt 2.7.7+ubuntu5` → `GHSA-pj65-3pf6-c5q4` : python-apt Does Not Check Hash Signature
- **PyPI** `python-apt 2.7.7+ubuntu5` → `GHSA-rp8m-h266-53jh` : python-apt Flawed Package Integrity Check
- **PyPI** `urllib3 2.5.0` → `GHSA-2xpw-w6gg-jr37` : urllib3 streaming API improperly handles highly compressed data
- **PyPI** `urllib3 2.5.0` → `GHSA-38jv-5279-wg99` : Decompression-bomb safeguards bypassed when following HTTP redirects (streaming API)
- **PyPI** `urllib3 2.5.0` → `GHSA-gm62-xv2j-4w53` : urllib3 allows an unbounded number of links in the decompression chain
- **PyPI** `wheel 0.42.0` → `GHSA-8rrh-rw8j-w5fx` : Wheel Affected by Arbitrary File Permission Modification via Path Traversal in wheel unpack

## 🧨 패키지 환각 / 존재성 이상
- ❌ 레지스트리 미존재 의심: `reqeusts`