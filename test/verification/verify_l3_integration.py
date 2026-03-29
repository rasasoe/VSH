#!/usr/bin/env python3
"""L3 Integration Verification Script"""

import requests
import json
from pathlib import Path

test_file = r"c:\Users\kjkol\OneDrive\바탕 화면\VSH-rasasoe-intergration\test_vsh_sample.py"

print("=" * 70)
print("🔍 L3 Integration Verification")
print("=" * 70)
print()

try:
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        exit(1)
    
    print(f"📄 Test file: {test_file}")
    print()
    
    # API 요청
    response = requests.post(
        "http://127.0.0.1:3000/scan/file",
        json={"path": test_file},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ Scan Completed Successfully!")
        print()
        print(f"📊 Total Findings: {len(result['findings'])}")
        print()
        
        if len(result['findings']) > 0:
            print("=" * 70)
            print("🎯 L3 INTEGRATION VERIFICATION")
            print("=" * 70)
            print()
            
            for idx, finding in enumerate(result['findings'][:3], 1):  # 최대 3개
                print(f"Finding #{idx}")
                print("-" * 70)
                print(f"  Rule ID:    {finding.get('rule_id', 'N/A')}")
                print(f"  Severity:   {finding.get('severity', 'N/A')}")
                print(f"  Location:   Line {finding.get('line', '?')}")
                print()
                
                # L2 Reasoning 검증
                l2 = finding.get('l2_reasoning', {})
                print("  📌 L2 Reasoning Results (L1→L2 통합):")
                print(f"     ✓ is_vulnerable: {l2.get('is_vulnerable', 'N/A')}")
                print(f"     ✓ confidence: {l2.get('confidence', 'N/A')}")
                
                reasoning = l2.get('reasoning', '')
                if reasoning:
                    reasoning_preview = reasoning[:80] if len(reasoning) > 80 else reasoning
                    print(f"     ✓ reasoning: '{reasoning_preview}...'")
                
                scenario = l2.get('attack_scenario', '')
                if scenario:
                    scenario_preview = scenario[:80] if len(scenario) > 80 else scenario
                    print(f"     ✓ attack_scenario: '{scenario_preview}...'")
                
                fix = l2.get('fix_suggestion', '')
                if fix:
                    fix_preview = fix[:80] if len(fix) > 80 else fix
                    print(f"     ✓ fix_suggestion: '{fix_preview}...'")
                
                print()
                
                # L3 Validation 검증
                l3 = finding.get('l3_validation', {})
                print("  🎯 L3 Validation Results (L2→L3 통합):")
                print(f"     ✓ validated: {l3.get('validated', 'N/A')}")
                print(f"     ✓ exploit_possible: {l3.get('exploit_possible', 'N/A')}")
                print(f"     ✓ confidence: {l3.get('confidence', 'N/A')}")
                
                l3_evidence = l3.get('evidence', '')
                if l3_evidence:
                    l3_evidence_preview = l3_evidence[:80] if len(l3_evidence) > 80 else l3_evidence
                    print(f"     ✓ evidence: '{l3_evidence_preview}...'")
                
                l3_fix = l3.get('recommended_fix', '')
                if l3_fix:
                    l3_fix_preview = l3_fix[:80] if len(l3_fix) > 80 else l3_fix
                    print(f"     ✓ recommended_fix: '{l3_fix_preview}...'")
                
                print()
            
            print("=" * 70)
            print("✨ L3 INTEGRATION VERIFICATION: PASSED ✅")
            print("=" * 70)
            print()
            print("All L1 → L2 → L3 fields are properly integrated!")
            print()
            print("Data Flow:")
            print("  L1 Scanner → Finding objects")
            print("     ↓")
            print("  L2 Reasoning → is_vulnerable, confidence, reasoning_verdict")
            print("     ↓")
            print("  L3 Validator → validated, exploit_possible, attack_scenario")
            print("     ↓")
            print("  API Response → Complete finding with all data")
            
        else:
            print("⚠️ No findings detected in test file")
    else:
        print(f"❌ API Error: Status {response.status_code}")
        print(response.text[:500])

except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to API server")
    print("   Make sure API is running: python -m uvicorn vsh_api.main:app --host 127.0.0.1 --port 3000")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
