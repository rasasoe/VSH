"""
RAG (Retrieval-Augmented Generation) 寃???쒖뒪??
?ㅼ젣 DB?먯꽌 愿???뺣낫瑜?寃?됲빐??LLM???쒓났
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Tuple, Optional
from shared.vulnerability_db import VulnerabilityDatabase
import json

class RAGRetriever:
    """
    RAG ?쒖뒪?쒖쓽 Retrieval 遺遺?
    - ?ㅼ젣 DB?먯꽌 愿???뺣낫 寃??
    - 臾몃㎘ 湲곕컲 ??궧
    - Top-K 寃곌낵 諛섑솚
    """
    
    def __init__(self, db_path: str = "mock_db/vsh.db"):
        self.db = VulnerabilityDatabase(db_path)
        self.cache = {}
    
    def retrieve(self, 
                 cwe_id: str, 
                 code_snippet: str = "",
                 top_k: int = 3) -> Dict:
        """CWE ID瑜?湲곕컲?쇰줈 愿???뺣낫 寃??""
        
        results = {
            "cwe_id": cwe_id,
            "vulnerability_info": None,
            "fix_suggestions": None,
            "related_vulnerabilities": [],
            "context": ""
        }
        
        # 1. CWE 痍⑥빟???뺣낫 議고쉶
        vuln = self.db.search_by_cwe(cwe_id)
        if vuln:
            results["vulnerability_info"] = vuln
        
        # 2. ?섏젙 諛⑸쾿 議고쉶
        fix = self.db.get_fix_for_cwe(cwe_id)
        if fix:
            results["fix_suggestions"] = fix
        
        # 3. 愿??痍⑥빟??寃??
        if code_snippet:
            keywords = self._extract_keywords(code_snippet)
            for keyword in keywords[:2]:  # ?곸쐞 2媛??ㅼ썙??
                related = self.db.search_by_keyword(keyword, limit=2)
                if related:
                    results["related_vulnerabilities"].extend(related)
        
        # 4. 寃??臾몃㎘ ?앹꽦
        results["context"] = self._build_context(results)
        
        return results
    
    def _extract_keywords(self, code: str) -> List[str]:
        """肄붾뱶?먯꽌 ?ㅼ썙??異붿텧"""
        keywords = []
        
        # ?⑥닔紐??⑦꽩
        patterns = {
            'execute': ['execute', 'query', 'sql'],
            'injection': ['subprocess', 'os.system', 'exec', 'eval'],
            'crypto': ['md5', 'sha1', 'hash', 'encrypt', 'decrypt'],
            'validation': ['input', 'user_input', 'request', 'parameter'],
        }
        
        for keyword in ['execute', 'subprocess', 'md5', 'input', 'password', 'key']:
            if keyword in code.lower():
                keywords.append(keyword)
        
        return keywords
    
    def _build_context(self, results: Dict) -> str:
        """寃??寃곌낵濡쒕???臾몃㎘ 援ъ꽦"""
        context_parts = []
        
        if results["vulnerability_info"]:
            vuln = results["vulnerability_info"]
            context_parts.append(f"痍⑥빟?? {vuln.get('name')}")
            context_parts.append(f"?ㅻ챸: {vuln.get('description')}")
            context_parts.append(f"?ш컖?? {vuln.get('severity')}")
            context_parts.append(f"湲곗?: {vuln.get('reference')}")
        
        if results["fix_suggestions"]:
            fix = results["fix_suggestions"]
            context_parts.append(f"\n?섏젙 諛⑸쾿: {fix.get('explanation')}")
            context_parts.append(f"肄붾뱶 蹂寃? {fix.get('vulnerable_code')} ??{fix.get('safe_code')}")
        
        return "\n".join(context_parts)
    
    def close(self):
        """?곌껐 醫낅즺"""
        self.db.close()


class RAGGenerator:
    """
    RAG??Generation 遺遺?
    - 寃??寃곌낵瑜?湲곕컲?쇰줈 ?곸꽭 遺꾩꽍 ?앹꽦
    - LLM ?꾨＼?꾪듃 援ъ꽦
    """
    
    def __init__(self, retriever: RAGRetriever):
        self.retriever = retriever
    
    def generate_analysis(self, 
                         cwe_id: str, 
                         code_snippet: str,
                         severity: str = "HIGH") -> Dict:
        """
        RAG 湲곕컲 遺꾩꽍 ?앹꽦
        
        Args:
            cwe_id: 痍⑥빟??CWE ID
            code_snippet: 痍⑥빟??肄붾뱶
            severity: ?ш컖??
        
        Returns:
            ?곸꽭 遺꾩꽍 寃곌낵
        """
        
        # 1. Retrieval: 愿???뺣낫 寃??
        retrieved = self.retriever.retrieve(cwe_id, code_snippet)
        
        # 2. Generation: LLM ?꾨＼?꾪듃 ?앹꽦
        prompt = self._build_prompt(retrieved, code_snippet, severity)
        
        # 3. 寃곌낵 援ъ꽦
        analysis = {
            "cwe_id": cwe_id,
            "severity": severity,
            "retrieval_results": retrieved,
            "llm_prompt": prompt,
            "analysis": self._generate_text_analysis(retrieved)
        }
        
        return analysis
    
    def _build_prompt(self, retrieved: Dict, code_snippet: str, severity: str) -> str:
        """LLM???꾪븳 ?꾨＼?꾪듃 ?앹꽦"""
        context = retrieved.get("context", "")
        
        prompt = f"""
?뱀떊? 蹂댁븞 肄붾뱶 寃???꾨Ц媛?낅땲??

## 諛쒓껄??痍⑥빟??
- CWE ID: {retrieved['cwe_id']}
- ?ш컖?? {severity}

## 諛깃렇?쇱슫???뺣낫 (RAG 寃??寃곌낵)
{context}

## 遺꾩꽍??肄붾뱶
```python
{code_snippet}
```

## ?붿껌?ы빆
1. ??肄붾뱶媛 ?뺣쭚 痍⑥빟?쒖? ?먮떒
2. 援ъ껜?곸씤 ?꾪뿕???ㅻ챸
3. ?④퀎蹂??섏젙 諛⑸쾿 ?쒖떆
4. ?섏젙???덉쟾??肄붾뱶 ?덉젣 ?묒꽦

JSON ?뺤떇?쇰줈 ?듬??섏꽭??
{{
  "is_vulnerable": true/false,
  "risk_assessment": "?꾪뿕???됯?",
  "step_by_step_fix": ["?④퀎 1", "?④퀎 2", ...],
  "safe_code": "?섏젙??肄붾뱶"
}}
"""
        return prompt
    
    def _generate_text_analysis(self, retrieved: Dict) -> str:
        """?띿뒪??湲곕컲 遺꾩꽍 ?앹꽦"""
        analysis = []
        
        vuln = retrieved.get("vulnerability_info", {})
        if vuln:
            analysis.append(f"[痍⑥빟?? {vuln.get('name')}")
            analysis.append(f"[?ㅻ챸] {vuln.get('description')}")
            analysis.append(f"[?ш컖?? {vuln.get('severity')}")
        
        fix = retrieved.get("fix_suggestions", {})
        if fix:
            analysis.append(f"\n[?섏젙 諛⑸쾿]")
            analysis.append(f"{fix.get('explanation')}")
            analysis.append(f"\n[肄붾뱶 蹂寃?")
            analysis.append(f"???섎せ?? {fix.get('vulnerable_code')}")
            analysis.append(f"???щ컮由? {fix.get('safe_code')}")
        
        return "\n".join(analysis)


class RAGSystem:
    """
    ?꾩쟾??RAG ?쒖뒪??
    Retrieval + Generation???듯빀
    """
    
    def __init__(self, db_path: str = "mock_db/vsh.db"):
        self.retriever = RAGRetriever(db_path)
        self.generator = RAGGenerator(self.retriever)
    
    def analyze(self, 
                cwe_id: str, 
                code_snippet: str,
                severity: str = "HIGH") -> Dict:
        """?듯빀 遺꾩꽍 ?ㅽ뻾"""
        return self.generator.generate_analysis(cwe_id, code_snippet, severity)
    
    def close(self):
        """醫낅즺"""
        self.retriever.close()



