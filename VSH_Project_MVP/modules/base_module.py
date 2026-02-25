from abc import ABC, abstractmethod
from typing import List
from models.scan_result import ScanResult

class BaseScanner(ABC):
    """
    모든 스캐너의 기본이 되는 추상 클래스.
    """

    @abstractmethod
    def scan(self, file_path: str) -> ScanResult:
        """
        파일을 스캔하여 취약점을 탐지합니다.

        Args:
            file_path (str): 스캔할 파일의 경로

        Returns:
            ScanResult: 스캔 결과 (취약점 목록 포함)
        """
        pass

    @abstractmethod
    def supported_languages(self) -> List[str]:
        """
        이 스캐너가 지원하는 언어 목록을 반환합니다.

        Returns:
            List[str]: 지원하는 언어 문자열 목록 (예: ["python"])
        """
        pass
