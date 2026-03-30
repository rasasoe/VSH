"""
L2 분석기에 RAG 시스템 통합
mock_db 대신 실제 DB 참조
"""

from typing import Dict, List
from models.scan_result import ScanResult
from models.fix_suggestion import FixSuggestion
from shared.rag_system import RAGSystem
from shared.contracts import BaseAnalyzer


class RAGBasedAnalyzer(BaseAnalyzer):
    """
    RAG (Retrieval-Augmented Generation) 기반 L2 분석기
    - 실제 DB에서 정보 검색
    - LLM과 함께 상세 분석 제공
    """
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.rag_system = RAGSystem()
        self.last_error: str | None = None
    
    def analyze(
        self,
        scan_result: ScanResult,
        knowledge: List[Dict],
        fix_hints: List[Dict],
        evidence_map: Dict[str, Dict] | None = None,
    ) -> List[FixSuggestion]:
        """
        RAG 기반 분석 실행
        
        Args:
            scan_result: L1 스캔 결과
            knowledge: 지식베이스 (사용안함 - DB에서 조회)
            fix_hints: 수정 힌트 (사용안함 - DB에서 조회)
            evidence_map: 증거 맵
        
        Returns:
            FixSuggestion 리스트
        """
        
        suggestions = []
        
        if not scan_result.findings:
            return suggestions
        
        for finding in scan_result.findings:
            try:
                # RAG 시스템으로 분석
                rag_result = self.rag_system.analyze(
                    cwe_id=finding.cwe_id,
                    code_snippet=finding.code_snippet or "",
                    severity=finding.severity or "MEDIUM"
                )
                
                # FixSuggestion으로 변환
                suggestion = self._convert_to_fix_suggestion(finding, rag_result)
                suggestions.append(suggestion)
                
                # 스캔 히스토리 기록
                self.rag_system.retriever.db.log_scan(
                    scan_result.file_path,
                    finding.cwe_id,
                    finding.severity
                )
                
            except Exception as e:
                self.last_error = str(e)
                print(f"[RAG 분석 에러] {finding.cwe_id}: {e}")
                continue
        
        return suggestions
    
    def _convert_to_fix_suggestion(self, finding, rag_result: Dict) -> FixSuggestion:
        """RAG 결과를 FixSuggestion으로 변환"""
        
        retrieved = rag_result['retrieval_results']
        fix = retrieved['fix_suggestions'] or {}
        
        return FixSuggestion(
            file_path=finding.file_path or "",
            line_number=finding.line_number,
            cwe_id=finding.cwe_id,
            title=retrieved['vulnerability_info'].get('name', 'Unknown') if retrieved['vulnerability_info'] else finding.rule_name,
            description=retrieved['vulnerability_info'].get('description', '') if retrieved['vulnerability_info'] else '',
            fixed_code=fix.get('safe_code', ''),
            reference=retrieved['vulnerability_info'].get('reference', '') if retrieved['vulnerability_info'] else '',
            decision_status="VULNERABLE",
            confidence_score=95,
            confidence_reason="RAG DB에서 확인된 알려진 취약점",
        )
    
    def close(self):
        """연결 종료"""
        self.rag_system.close()


# L2 분석기를 RAG기반으로 교체하는 함수
def setup_rag_analysis():
    """RAG 분석기 설정"""
    print("\n" + "="*80)
    print("📊 RAG 기반 L2 분석기 설정")
    print("="*80 + "\n")
    
    analyzer = RAGBasedAnalyzer()
    
    # 테스트 스캔 결과 생성
    from models.scan_result import ScanResult
    from models.vulnerability import Vulnerability
    
    # SQL Injection 취약점
    sql_vuln = Vulnerability(
        rule_name="SQL Injection",
        cwe_id="CWE-89",
        severity="CRITICAL",
        line_number=21,
        code_snippet='query = "SELECT * FROM users WHERE name = \'" + username + "\'"',
        message="SQL Injection Risk",
        file_path="sqli.py"
    )
    
    # Hardcoded Secret 취약점
    secret_vuln = Vulnerability(
        rule_name="Hardcoded Secret",
        cwe_id="CWE-798",
        severity="HIGH",
        line_number=1,
        code_snippet='API_KEY = "hardcoded-secret-key-12345"',
        message="Hardcoded API Key",
        file_path="secret.py"
    )
    
    scan_result = ScanResult(
        file_path="test.py",
        language="python",
        findings=[sql_vuln, secret_vuln]
    )
    
    # 분석 실행
    print("🔍 RAG 분석 중...\n")
    suggestions = analyzer.analyze(scan_result, [], [])
    
    # 결과 출력
    print(f"✅ {len(suggestions)}개 취약점 분석 완료\n")
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"[{i}] {suggestion.cwe_id}: {suggestion.title}")
        print(f"    파일: {suggestion.file_path}:{suggestion.line_number}")
        print(f"    설명: {suggestion.description}")
        print(f"    수정: {suggestion.fixed_code[:100]}...")
        print()
    
    analyzer.close()
    
    print("="*80)
    print("✅ RAG 분석기 설정 완료!")
    print("="*80 + "\n")


if __name__ == "__main__":
    setup_rag_analysis()
