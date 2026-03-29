"""
L3 비동기 백그라운드 실행 관리자
- L3Pipeline 인스턴스화 및 생명주기 관리
- Docker/환경변수 확인
- 별도 스레드에서 비블로킹 실행
"""

import asyncio
import threading
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class L3BackgroundRunner:
    """L3 파이프라인을 비동기 백그라운드 스레드에서 관리"""

    def __init__(self, shared_db=None):
        """
        Args:
            shared_db: SharedDB adapter (L3 결과 저장용)
        """
        self.shared_db = shared_db
        self.pipeline = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        """
        L3 의존성 확인 및 파이프라인 초기화
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            # 1. Docker 확인
            import subprocess
            try:
                result = subprocess.run(
                    ["docker", "--version"],
                    capture_output=True,
                    timeout=2,
                    text=True
                )
                if result.returncode != 0:
                    logger.warning("⚠️  Docker not available. L3 PoC verification disabled.")
                    return False
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("⚠️  Docker not found. L3 PoC verification disabled.")
                return False

            # 2. L3 모듈 임포트 시도
            try:
                # L3-dev 코드 구조 가정: VSH_Project_MVP/l3/
                # 매개변수 조정 필요: 실제 L3-dev 코드의 import 경로 따를 것
                from l3.providers.sonarqube.real import RealSonarQubeProvider
                from l3.providers.sbom.real import RealSBOMProvider
                from l3.providers.poc.real import RealPoCProvider
                from l3.pipeline import L3Pipeline
                
                # LLM 어댑터 (Gemini 또는 Mock)
                try:
                    from l3.llm.gemini_adapter import GeminiAdapter
                    llm = GeminiAdapter()
                except ImportError:
                    logger.warning("Gemini adapter not available, using mock")
                    llm = None

                # SonarQube 토큰 확인
                sonar_token = os.getenv("SONARQUBE_TOKEN")
                if not sonar_token:
                    logger.warning("⚠️  SONARQUBE_TOKEN not set. L3 SonarQube disabled.")
                    # SonarQube 없어도 SBOM/PoC는 진행 가능

                # L3Pipeline 인스턴스화
                self.pipeline = L3Pipeline(
                    sonarqube=RealSonarQubeProvider(llm=llm) if sonar_token else None,
                    sbom=RealSBOMProvider(),
                    poc=RealPoCProvider(llm=llm),
                    shared_db=self.shared_db
                )
                logger.info("✅ L3 pipeline initialized successfully")
                return True

            except ImportError as e:
                logger.warning(f"❌ L3 modules not available: {e}")
                logger.info("L3 disabled - L1/L2 analysis will proceed normally")
                return False

        except Exception as e:
            logger.error(f"❌ L3 initialization failed: {e}", exc_info=True)
            return False

    def run_async(self, project_path: str) -> bool:
        """
        백그라운드 스레드에서 L3 파이프라인 실행 (비블로킹)
        
        Args:
            project_path: 분석할 프로젝트/파일 경로
            
        Returns:
            bool: 스레드 시작 성공 여부
        """
        if not self.pipeline:
            logger.debug("L3 pipeline not initialized. Skipping L3.")
            return False

        with self._lock:
            # 기존 스레드가 실행 중이면 스킵
            if self._thread and self._thread.is_alive():
                logger.debug(f"L3 already running for {project_path}. Skipping duplicate.")
                return False

            # 새 스레드 시작
            self._thread = threading.Thread(
                target=self._run_l3_thread,
                args=(project_path,),
                daemon=False  # 정상 종료 가능하게
            )
            self._thread.start()
            logger.info(f"🔄 L3 pipeline started in background for {project_path}")
            return True

    def _run_l3_thread(self, project_path: str):
        """
        스레드 내에서 L3 파이프라인 실행
        
        Args:
            project_path: 분석 대상 경로
        """
        try:
            # 스레드 내에서 새로운 asyncio 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # L3Pipeline.run() 실행
            loop.run_until_complete(
                self.pipeline.run(project_path)
            )
            
            loop.close()
            logger.info(f"✅ L3 pipeline completed for {project_path}")
            
        except Exception as e:
            logger.error(
                f"❌ L3 pipeline failed for {project_path}: {e}",
                exc_info=True
            )
            # L3 실패는 전체 시스템을 깨뜨리지 않음 (graceful fallback)

    def wait_completion(self, timeout_sec: float = 300) -> bool:
        """
        L3 완료 대기 (테스트/블로킹 호출용)
        
        Args:
            timeout_sec: 대기 시간초 (기본 5분)
            
        Returns:
            bool: 완료 여부
        """
        if self._thread is None:
            return True

        self._thread.join(timeout=timeout_sec)
        return not self._thread.is_alive()

    def shutdown(self, timeout_sec: float = 10):
        """
        우아한 종료
        
        Args:
            timeout_sec: 종료 대기 시간 (기본 10초)
        """
        if self._thread and self._thread.is_alive():
            logger.info("Waiting for L3 pipeline to complete...")
            self._thread.join(timeout=timeout_sec)
            
            if self._thread.is_alive():
                logger.warning("⚠️  L3 pipeline did not complete within timeout")
            else:
                logger.info("✅ L3 pipeline stopped")


# 전역 인스턴스 (API/CLI에서 사용)
_l3_runner: Optional[L3BackgroundRunner] = None


def get_l3_runner(shared_db=None) -> L3BackgroundRunner:
    """싱글톤 L3Runner 획득"""
    global _l3_runner
    if _l3_runner is None:
        _l3_runner = L3BackgroundRunner(shared_db)
    return _l3_runner


def initialize_l3(shared_db=None) -> bool:
    """L3 초기화"""
    runner = get_l3_runner(shared_db)
    return runner.initialize()
