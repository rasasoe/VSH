# 테스트 및 검증 폴더

VSH 프로젝트의 모든 테스트, 샘플, 검증 코드를 중앙화한 폴더입니다.

## 📁 폴더 구조

```
test/
├── samples/          # 테스트 샘플 코드
│   ├── test_sample.py
│   └── test_vsh_sample.py
├── verification/     # L3 통합 검증
│   ├── check_l3_integration.py
│   └── verify_l3_integration.py
├── mvp/             # MVP 전체 테스트
│   └── test_vsh_mvp.py
├── results/         # 테스트 실행 결과
│   └── test-results/
│       └── l1/
└── README.md        # 이 파일
```

## 🎯 각 폴더 용도

### `samples/`
- **용도**: 취약점 샘플 코드 테스트
- **파일**: 작은 규모의 샘플 스캔 테스트

### `verification/`
- **용도**: L3 통합 검증
- **파일**:
  - `verify_l3_integration.py` - L3 검증 실행
  - `check_l3_integration.py` - L3 상세 검증

### `mvp/`
- **용도**: VSH MVP 전체 기능 테스트
- **파일**: `test_vsh_mvp.py` - 9개 테스트 케이스 (모두 통과 ✅)

### `results/`
- **용도**: 테스트 실행 결과 저장
- **내용**: L1 성능, 로그, 진단 데이터

## 🚀 실행 방법

```bash
# 모든 샘플 테스트
python test/samples/test_vsh_sample.py

# MVP 전체 테스트
python test/mvp/test_vsh_mvp.py

# L3 검증
python test/verification/verify_l3_integration.py
```

## ⚠️ 주의사항

- **VSH_Project_MVP/** 은 실제 프로젝트 소스 코드이므로 이 폴더와는 독립적입니다
- 테스트 결과는 `results/` 에만 저장됩니다
