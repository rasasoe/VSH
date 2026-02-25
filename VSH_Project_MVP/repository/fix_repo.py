import json
import os
from typing import Optional, Dict, List
from .base_repository import BaseReadRepository
try:
    from config import FIX_PATH
except ImportError:
    # 테스트 등에서 config를 찾지 못하는 경우를 위한 fallback
    FIX_PATH = "mock_db/kisa_fix.json"

class MockFixRepo(BaseReadRepository):
    """
    Mock Fix DB(kisa_fix.json)를 읽기 위한 Repository 구현체.
    """

    def find_by_id(self, id: str) -> Optional[Dict]:
        """
        kisa_fix.json에서 ID로 항목을 조회합니다.

        Args:
            id (str): CWE ID (예: CWE-78)

        Returns:
            Optional[Dict]: 해당 항목 데이터, 없으면 None
        """
        if not os.path.exists(FIX_PATH):
            print(f"[WARN] Fix DB file not found: {FIX_PATH}")
            return None
        
        try:
            with open(FIX_PATH, "r", encoding="utf-8") as f:
                data: List[Dict] = json.load(f)
                
                if isinstance(data, list):
                    for item in data:
                        if item.get("id") == id:
                            return item
                else:
                    print(f"[ERROR] Fix DB structure is invalid (expected list).")

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse Fix DB JSON: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error accessing Fix DB: {e}")
            
        return None
