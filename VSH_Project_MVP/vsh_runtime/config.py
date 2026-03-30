"""
VSH 전체 환경 설정 관리
- .env 로딩
- 기본값 설정
- L1/L2/L3 활성화 제어
"""

import os
import json
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

# 기본 설정 (환경변수 기반)
DEFAULT_CONFIG: dict[str, Any] = {
    "app": {
        "version": "1.0.0",
        "name": "VSH",
        "description": "SAST + LLM + Evidence-based Verification"
    },
    
    "llm": {
        "provider": os.getenv("LLM_PROVIDER", "gemini"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": "gemini-1.5-pro",
        "enable_l1": True,
        "enable_l2": os.getenv("LLM_PROVIDER") != "mock",  # 기본값: 활성화
        "enable_l3": True
    },
    
    "l3": {
        "enabled": True,
        "sonarqube": {
            "enabled": bool(os.getenv("SONARQUBE_TOKEN")),
            "url": os.getenv("SONARQUBE_URL", "https://sonarcloud.io"),
            "token": os.getenv("SONARQUBE_TOKEN", ""),
            "org": os.getenv("SONARQUBE_ORG", ""),
            "project_key": os.getenv("SONARQUBE_PROJECT_KEY", "")
        },
        "sbom": {
            "enabled": True,
            "tool": "syft",
            "include_dev_deps": False
        },
        "poc": {
            "enabled": True,
            "timeout_sec": 30,
            "docker_required": True
        }
    },
    
    "watch": {
        "enabled": True,
        "debounce_sec": 1.0,
        "poll_interval_sec": 0.5,
        "watch_extensions": [".py", ".js", ".ts", ".jsx", ".tsx"],
        "exclude_dirs": [".git", "node_modules", ".venv", "__pycache__", ".vscode"]
    },
    
    "output": {
        "export_dir": "./exports",
        "save_json": True,
        "save_markdown": True,
        "save_html": False,
        "save_diagnostics": True,
        "auto_open_report": False
    },
    
    "cache": {
        "enabled": True,
        "dir": ".vsh/cache",
        "ttl_hours": 24
    },
    
    "logging": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "file": ".vsh/vsh.log"
    }
}


def load_env_config() -> dict[str, Any]:
    """환경변수 기반 설정 반환"""
    return DEFAULT_CONFIG.copy()


def load_file_config(config_file: str = ".vsh/config.json") -> dict[str, Any]:
    """파일에서 설정 로드 (없으면 기본값)"""
    if Path(config_file).exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                logger.info(f"Loaded config from {config_file}")
                return file_config
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}. Using default.")
            return load_env_config()
    else:
        return load_env_config()


def save_config(config: dict[str, Any], config_file: str = ".vsh/config.json") -> bool:
    """설정 저장"""
    try:
        config_path = Path(config_file)
        config_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved config to {config_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def get_config() -> dict[str, Any]:
    """현재 설정 반환"""
    return load_file_config()


def is_l1_enabled() -> bool:
    """L1 활성화 여부"""
    return get_config().get("llm", {}).get("enable_l1", True)


def is_l2_enabled() -> bool:
    """L2 활성화 여부"""
    return get_config().get("llm", {}).get("enable_l2", True)


def is_l3_enabled() -> bool:
    """L3 활성화 여부"""
    return get_config().get("l3", {}).get("enabled", True)


def is_sonarqube_enabled() -> bool:
    """SonarQube 활성화 여부"""
    return get_config().get("l3", {}).get("sonarqube", {}).get("enabled", False)


def is_poc_enabled() -> bool:
    """PoC 검증 활성화 여부"""
    return get_config().get("l3", {}).get("poc", {}).get("enabled", True)


def validate_config(config: dict[str, Any]) -> tuple[bool, str]:
    """
    설정 검증
    
    Returns:
        (valid: bool, message: str)
    """
    errors: list[str] = []
    
    # L2 활성화 시 LLM 키 확인
    if config.get("llm", {}).get("enable_l2"):
        provider = config.get("llm", {}).get("provider", "")
        
        if provider == "gemini":
            if not config.get("llm", {}).get("gemini_api_key"):
                errors.append("gemini_api_key is required when L2 is enabled with Gemini")
        elif provider == "openai":
            if not config.get("llm", {}).get("openai_api_key"):
                errors.append("openai_api_key is required when L2 is enabled with OpenAI")
    
    # SonarQube 활성화 시 토큰 확인
    if config.get("l3", {}).get("sonarqube", {}).get("enabled"):
        if not config.get("l3", {}).get("sonarqube", {}).get("token"):
            errors.append("SONARQUBE_TOKEN is required when SonarQube is enabled")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "Config is valid"


def print_config_summary():
    """설정 요약 출력 (디버깅용)"""
    config = get_config()
    
    print("\n" + "="*60)
    print("VSH Configuration Summary")
    print("="*60)
    
    print(f"\n[L1/L2] Reasoning:")
    print(f"  L1 Enabled: {config.get('llm', {}).get('enable_l1', True)}")
    print(f"  L2 Enabled: {config.get('llm', {}).get('enable_l2', True)}")
    print(f"  LLM Provider: {config.get('llm', {}).get('provider', 'unknown')}")
    
    print(f"\n[L3] Validation:")
    print(f"  L3 Enabled: {config.get('l3', {}).get('enabled', True)}")
    print(f"  SonarQube: {config.get('l3', {}).get('sonarqube', {}).get('enabled', False)}")
    print(f"  SBOM: {config.get('l3', {}).get('sbom', {}).get('enabled', True)}")
    print(f"  PoC: {config.get('l3', {}).get('poc', {}).get('enabled', True)}")
    
    print(f"\n[Watch]")
    print(f"  Enabled: {config.get('watch', {}).get('enabled', True)}")
    print(f"  Debounce: {config.get('watch', {}).get('debounce_sec', 1.0)}s")
    
    print(f"\n[Output]")
    print(f"  Export Dir: {config.get('output', {}).get('export_dir', './exports')}")
    print(f"  Save JSON: {config.get('output', {}).get('save_json', True)}")
    print(f"  Save Markdown: {config.get('output', {}).get('save_markdown', True)}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print_config_summary()
