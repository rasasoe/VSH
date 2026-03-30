"""Background wrapper for the optional L3 pipeline."""

import asyncio
import logging
import os
import subprocess
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)


class L3BackgroundRunner:
    """Initializes and runs the L3 pipeline in a background thread."""

    def __init__(self, shared_db: Optional[Any] = None):
        self.shared_db = shared_db
        self.pipeline = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        try:
            try:
                result = subprocess.run(
                    ["docker", "--version"],
                    capture_output=True,
                    timeout=2,
                    text=True,
                )
                if result.returncode != 0:
                    logger.warning("Docker is unavailable. L3 is disabled.")
                    return False
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("Docker is not installed. L3 is disabled.")
                return False

            from l3.mock_shared_db import MockSharedDB
            from l3.normalizer import L3Normalizer
            from l3.pipeline import L3Pipeline
            from l3.providers.poc.real import RealPoCProvider
            from l3.providers.sbom.real import RealSBOMProvider
            from l3.providers.sonarqube.real import RealSonarQubeProvider

            try:
                from l3.llm.gemini_adapter import GeminiAdapter
                llm = GeminiAdapter()
            except ImportError:
                logger.warning("Gemini adapter not available, continuing without it.")
                llm = None

            sonar_token = os.getenv("SONAR_TOKEN") or os.getenv("SONARQUBE_TOKEN")
            if not sonar_token:
                logger.warning("SONAR_TOKEN is not configured. L3 is disabled.")
                return False

            if os.getenv("SONAR_TOKEN") is None:
                os.environ["SONAR_TOKEN"] = sonar_token

            normalizer = L3Normalizer(self.shared_db or MockSharedDB())
            self.pipeline = L3Pipeline(
                sonarqube=RealSonarQubeProvider(llm=llm),
                sbom=RealSBOMProvider(),
                poc=RealPoCProvider(llm=llm),
                normalizer=normalizer,
            )
            logger.info("L3 pipeline initialized successfully")
            return True
        except ImportError as exc:
            logger.warning(f"L3 modules are unavailable: {exc}")
            return False
        except Exception as exc:
            logger.error(f"L3 initialization failed: {exc}", exc_info=True)
            return False

    def run_async(self, project_path: str) -> bool:
        if self.pipeline is None:
            logger.debug("L3 pipeline is not initialized. Skipping background run.")
            return False

        with self._lock:
            if self._thread and self._thread.is_alive():
                logger.debug("L3 pipeline is already running. Skipping duplicate run.")
                return False

            self._thread = threading.Thread(
                target=self._run_l3_thread,
                args=(project_path,),
                daemon=False,
            )
            self._thread.start()
            logger.info(f"L3 pipeline started in background for {project_path}")
            return True

    def _run_l3_thread(self, project_path: str):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.pipeline.run(project_path))
            loop.close()
            logger.info(f"L3 pipeline completed for {project_path}")
        except Exception as exc:
            logger.error(f"L3 pipeline failed for {project_path}: {exc}", exc_info=True)

    def wait_completion(self, timeout_sec: float = 300) -> bool:
        if self._thread is None:
            return True

        self._thread.join(timeout=timeout_sec)
        return not self._thread.is_alive()

    def shutdown(self, timeout_sec: float = 10):
        if self._thread and self._thread.is_alive():
            logger.info("Waiting for the L3 pipeline to complete...")
            self._thread.join(timeout=timeout_sec)
            if self._thread.is_alive():
                logger.warning("L3 pipeline did not complete within the timeout.")
            else:
                logger.info("L3 pipeline stopped")


_l3_runner: Optional["L3BackgroundRunner"] = None


def get_l3_runner(shared_db: Optional[Any] = None) -> L3BackgroundRunner:
    global _l3_runner
    if _l3_runner is None:
        _l3_runner = L3BackgroundRunner(shared_db)
    return _l3_runner


def initialize_l3(shared_db: Optional[Any] = None) -> bool:
    runner = get_l3_runner(shared_db)
    return runner.initialize()
