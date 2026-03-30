"""
L3의 AbstractSharedDB 계약을 만족하는 SharedDB adapter 구현
기존 repository 계층과 L3 파이프라인을 연결
"""

import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from models.common_schema import VulnRecord, PackageRecord
import logging

logger = logging.getLogger(__name__)


class SharedDBAdapter:
    """L3 SharedDB 계약 구현 (L3와 기존 repository 연결)"""

    def __init__(self, db_file: str = ".vsh/shared_db.json"):
        """
        Args:
            db_file: 저장할 JSON 파일 경로
        """
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(exist_ok=True, parents=True)
        self._lock = asyncio.Lock()
        self._vulns: List[Dict[str, Any]] = []
        self._packages: List[Dict[str, Any]] = []
        self._load_db()

    def _load_db(self):
        """내부 DB 로드 (시작 시)"""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._vulns = data.get('vulns', [])
                    self._packages = data.get('packages', [])
                    logger.info(f"Loaded {len(self._vulns)} vulns, {len(self._packages)} packages from SharedDB")
            except Exception as e:
                logger.error(f"Failed to load SharedDB: {e}")
                self._vulns = []
                self._packages = []
        else:
            self._vulns = []
            self._packages = []

    def _save_db(self):
        """내부 DB 저장"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        'vulns': self._vulns,
                        'packages': self._packages
                    },
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save SharedDB: {e}")

    async def write(self, record: Union['VulnRecord', 'PackageRecord']) -> None:
        """
        L3 AbstractSharedDB 계약 구현
        분석 결과를 저장소에 저장
        
        Args:
            record: VulnRecord 또는 PackageRecord
        """
        async with self._lock:
            try:
                if hasattr(record, 'vuln_id'):  # VulnRecord
                    record_dict = record.model_dump() if hasattr(record, 'model_dump') else record.__dict__
                    vuln_id = record_dict.get('vuln_id')
                    
                    # 중복 제거 (vuln_id 기줄)
                    self._vulns = [v for v in self._vulns if v.get('vuln_id') != vuln_id]
                    self._vulns.append(dict(record_dict))
                    
                    logger.debug(f"Wrote vuln {vuln_id} to SharedDB")
                    
                elif hasattr(record, 'package_id'):  # PackageRecord
                    record_dict = record.model_dump() if hasattr(record, 'model_dump') else record.__dict__
                    package_id = record_dict.get('package_id')
                    
                    # 중복 제거 (package_id 기준)
                    self._packages = [p for p in self._packages if p.get('package_id') != package_id]
                    self._packages.append(dict(record_dict))
                    
                    logger.debug(f"Wrote package {package_id} to SharedDB")
                
                self._save_db()
                
            except Exception as e:
                logger.error(f"Failed to write record to SharedDB: {e}")

    async def read_all_vuln(self) -> List[VulnRecord]:
        """
        L3 AbstractSharedDB 계약 구현
        저장된 모든 취약점 조회
        
        Returns:
            VulnRecord 리스트
        """
        async with self._lock:
            try:
                # dict → VulnRecord 변환
                result: list[VulnRecord] = []
                for v in self._vulns:
                    try:
                        # VulnRecord 생성 (실패 시 skip)
                        vuln = VulnRecord(**v)
                        result.append(vuln)
                    except Exception as e:
                        logger.warning(f"Failed to parse vuln record: {e}")
                        continue
                
                logger.debug(f"Read {len(result)} vulns from SharedDB")
                return result
                
            except Exception as e:
                logger.error(f"Failed to read vulns from SharedDB: {e}")
                return []

    async def read_all_package(self) -> List[PackageRecord]:
        """
        L3 AbstractSharedDB 계약 구현
        저장된 모든 패키지 조회
        
        Returns:
            PackageRecord 리스트
        """
        async with self._lock:
            try:
                # dict → PackageRecord 변환
                result: list[PackageRecord] = []
                for p in self._packages:
                    try:
                        pkg = PackageRecord(**p)
                        result.append(pkg)
                    except Exception as e:
                        logger.warning(f"Failed to parse package record: {e}")
                        continue
                
                logger.debug(f"Read {len(result)} packages from SharedDB")
                return result
                
            except Exception as e:
                logger.error(f"Failed to read packages from SharedDB: {e}")
                return []

    async def get_all(self) -> Dict[str, list[Dict[str, Any]]]:
        """
        현재 저장소의 모든 데이터 반환 (리포트 생성용)
        
        Returns:
            dict: {'vulns': [...], 'packages': [...]}
        """
        async with self._lock:
            return {
                'vulns': self._vulns.copy(),
                'packages': self._packages.copy()
            }

    def clear(self):
        """저장소 초기화 (테스트용)"""
        self._vulns = []
        self._packages = []
        self._save_db()

    def get_stats(self) -> Dict[str, int]:
        """통계 반환"""
        return {
            'total_vulns': len(self._vulns),
            'total_packages': len(self._packages),
            'critical': len([v for v in self._vulns if v.get('severity') == 'CRITICAL']),
            'high': len([v for v in self._vulns if v.get('severity') == 'HIGH']),
        }


# 전역 인스턴스
_shared_db: Optional[SharedDBAdapter] = None


def get_shared_db(db_file: str = ".vsh/shared_db.json") -> SharedDBAdapter:
    """싱글톤 SharedDB 획득"""
    global _shared_db
    if _shared_db is None:
        _shared_db = SharedDBAdapter(db_file)
    return _shared_db
