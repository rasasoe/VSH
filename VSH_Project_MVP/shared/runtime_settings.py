from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".vsh"
CONFIG_PATH = CONFIG_DIR / "config.json"


DEFAULT_CONFIG: dict[str, Any] = {
    "llm": {
        "provider": "auto",
        "gemini_api_key": "",
        "openai_api_key": "",
        "model": "gemini-1.5-pro",
        "enable_l2": True,
        "enable_l3": True,
    },
    "tools": {
        "syft_path": "",
        "syft_auto_detect": True,
        "semgrep_path": "",
        "semgrep_auto_detect": True,
    },
    "l3": {
        "sonar_url": "https://sonarcloud.io",
        "sonar_token": "",
        "sonar_org": "",
        "sonar_project_key": "vsh-local",
    },
    "scan": {
        "watch_on_save": True,
        "auto_scan_on_select": False,
        "enable_sbom": True,
        "max_files_per_scan": 200,
        "exclude_dirs": [".git", "node_modules", "venv", "__pycache__", "dist", "build"],
        "include_extensions": [".py", ".js", ".ts", ".jsx", ".tsx"],
    },
    "output": {
        "export_path": "./exports",
        "save_json": True,
        "save_markdown": True,
        "save_diagnostics": True,
        "auto_open_report_after_scan": False,
    },
    "ui": {
        "theme": "dark",
        "show_code_preview": True,
        "show_attack_scenario": True,
        "show_validation_panel": True,
    },
    "system": {
        "api_base_url": "http://localhost:3000",
        "config_version": 2,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def ensure_config_path() -> None:
    CONFIG_DIR.mkdir(exist_ok=True, parents=True)
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)


def normalize_config(config: dict[str, Any] | None) -> dict[str, Any]:
    raw_config = config or {}
    merged = _deep_merge(DEFAULT_CONFIG, raw_config)
    config_version = int((raw_config.get("system") or {}).get("config_version", 0) or 0)

    llm = merged.setdefault("llm", {})
    if llm.get("provider") not in {"auto", "mock", "gemini", "openai"}:
        llm["provider"] = "auto"
    elif config_version < 2 and llm.get("provider") == "mock":
        if llm.get("gemini_api_key") or llm.get("openai_api_key"):
            llm["provider"] = "auto"

    tools = merged.setdefault("tools", {})
    tools["syft_path"] = str(tools.get("syft_path", "") or "").strip()
    tools["syft_auto_detect"] = bool(tools.get("syft_auto_detect", True))
    tools["semgrep_path"] = str(tools.get("semgrep_path", "") or "").strip()
    tools["semgrep_auto_detect"] = bool(tools.get("semgrep_auto_detect", True))

    scan = merged.setdefault("scan", {})
    scan["exclude_dirs"] = list(scan.get("exclude_dirs") or [])
    scan["include_extensions"] = list(scan.get("include_extensions") or [])

    l3 = merged.setdefault("l3", {})
    l3["sonar_url"] = str(l3.get("sonar_url") or "https://sonarcloud.io").strip() or "https://sonarcloud.io"
    l3["sonar_token"] = str(l3.get("sonar_token") or "").strip()
    l3["sonar_org"] = str(l3.get("sonar_org") or "").strip()
    l3["sonar_project_key"] = str(l3.get("sonar_project_key") or "vsh-local").strip() or "vsh-local"

    merged.setdefault("system", {})["config_version"] = DEFAULT_CONFIG["system"]["config_version"]
    return merged


def load_config() -> dict[str, Any]:
    ensure_config_path()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except Exception:
        raw = {}
    normalized = normalize_config(raw)
    if raw != normalized:
        save_config(normalized)
    return normalized


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_config(config)
    CONFIG_DIR.mkdir(exist_ok=True, parents=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, ensure_ascii=False, indent=2)
    return normalized


def _env_gemini_key() -> str:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")


def _env_openai_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "")


def _env_sonar_token() -> str:
    return os.environ.get("SONAR_TOKEN") or os.environ.get("SONARQUBE_TOKEN", "")


def _env_sonar_url() -> str:
    return os.environ.get("SONAR_URL") or os.environ.get("SONARQUBE_URL", "https://sonarcloud.io")


def _env_sonar_org() -> str:
    return os.environ.get("SONAR_ORG") or os.environ.get("SONARQUBE_ORG", "")


def _env_sonar_project_key() -> str:
    return os.environ.get("SONAR_PROJECT_KEY") or os.environ.get("SONARQUBE_PROJECT_KEY", "vsh-local")


def get_effective_llm_status(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = normalize_config(config)
    llm = cfg.get("llm", {})

    requested = (llm.get("provider") or "auto").lower()
    gemini_key = str(llm.get("gemini_api_key") or _env_gemini_key()).strip()
    openai_key = str(llm.get("openai_api_key") or _env_openai_key()).strip()

    if requested == "gemini":
        effective = "gemini" if gemini_key else "mock"
        reason = "Gemini key configured." if gemini_key else "Gemini selected but no API key is configured. Falling back to mock."
    elif requested == "openai":
        effective = "openai" if openai_key else "mock"
        reason = "OpenAI key configured." if openai_key else "OpenAI selected but no API key is configured. Falling back to mock."
    elif requested == "mock":
        effective = "mock"
        reason = "Mock mode selected explicitly."
    else:
        if openai_key:
            effective = "openai"
            reason = "Auto mode selected OpenAI because an OpenAI API key is configured."
        elif gemini_key:
            effective = "gemini"
            reason = "Auto mode selected Gemini because a Gemini API key is configured."
        else:
            effective = "mock"
            reason = "Auto mode found no LLM API key, so VSH will use mock reasoning."

    configured = bool(gemini_key or openai_key)
    connected = effective == "mock" or configured
    return {
        "requested_provider": requested,
        "provider": effective,
        "configured": configured,
        "connected": connected,
        "reason": reason,
        "has_gemini_key": bool(gemini_key),
        "has_openai_key": bool(openai_key),
        "model": llm.get("model") or DEFAULT_CONFIG["llm"]["model"],
        "enable_l2": bool(llm.get("enable_l2", True)),
        "enable_l3": bool(llm.get("enable_l3", True)),
    }


def apply_runtime_env(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = normalize_config(config)
    llm_status = get_effective_llm_status(cfg)
    llm = cfg.get("llm", {})
    tools = cfg.get("tools", {})
    l3 = cfg.get("l3", {})

    gemini_key = str(llm.get("gemini_api_key") or "").strip()
    openai_key = str(llm.get("openai_api_key") or "").strip()
    sonar_token = str(l3.get("sonar_token") or _env_sonar_token()).strip()
    sonar_url = str(l3.get("sonar_url") or _env_sonar_url()).strip()
    sonar_org = str(l3.get("sonar_org") or _env_sonar_org()).strip()
    sonar_project_key = str(l3.get("sonar_project_key") or _env_sonar_project_key()).strip()
    syft_path = str(tools.get("syft_path") or "").strip()
    semgrep_path = str(tools.get("semgrep_path") or "").strip()

    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        os.environ["GOOGLE_API_KEY"] = gemini_key
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if llm.get("model"):
        os.environ["GEMINI_MODEL"] = str(llm["model"])
    if sonar_token:
        os.environ["SONAR_TOKEN"] = sonar_token
        os.environ["SONARQUBE_TOKEN"] = sonar_token
    if sonar_url:
        os.environ["SONAR_URL"] = sonar_url
        os.environ["SONARQUBE_URL"] = sonar_url
    if sonar_org:
        os.environ["SONAR_ORG"] = sonar_org
        os.environ["SONARQUBE_ORG"] = sonar_org
    if sonar_project_key:
        os.environ["SONAR_PROJECT_KEY"] = sonar_project_key
        os.environ["SONARQUBE_PROJECT_KEY"] = sonar_project_key
    if syft_path:
        os.environ["SYFT_PATH"] = syft_path
    if semgrep_path:
        os.environ["SEMGREP_PATH"] = semgrep_path

    os.environ["LLM_PROVIDER"] = llm_status["provider"]
    return llm_status


def _detect_cli_tool(
    config: dict[str, Any] | None,
    manual_key: str,
    auto_key: str,
    env_key: str,
    binary_name: str,
) -> dict[str, Any]:
    cfg = normalize_config(config)
    tools = cfg.get("tools", {})

    manual_path = str(tools.get(manual_key) or os.environ.get(env_key, "")).strip()
    auto_detect = bool(tools.get(auto_key, True))
    found_path = ""
    source = "missing"

    if manual_path and Path(manual_path).exists():
        found_path = manual_path
        source = "manual"
    elif auto_detect:
        detected = shutil.which(binary_name)
        if detected:
            found_path = detected
            source = "auto"

    return {
        "installed": bool(found_path),
        "path": found_path,
        "source": source,
        "auto_detect": auto_detect,
    }


def detect_syft(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return _detect_cli_tool(config, "syft_path", "syft_auto_detect", "SYFT_PATH", "syft")


def detect_semgrep(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return _detect_cli_tool(config, "semgrep_path", "semgrep_auto_detect", "SEMGREP_PATH", "semgrep")


def _docker_status() -> dict[str, Any]:
    docker_path = shutil.which("docker")
    if not docker_path:
        return {"installed": False, "path": "", "reason": "docker not found in PATH"}

    try:
        result = subprocess.run(
            [docker_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception as exc:
        return {"installed": False, "path": docker_path, "reason": f"docker check failed: {exc}"}

    if result.returncode != 0:
        return {"installed": False, "path": docker_path, "reason": "docker command returned a non-zero exit code"}

    return {"installed": True, "path": docker_path, "reason": (result.stdout or result.stderr).strip()}


def get_effective_l3_status(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = normalize_config(config)
    llm = cfg.get("llm", {})
    l3 = cfg.get("l3", {})
    docker = _docker_status()

    enabled_by_user = bool(llm.get("enable_l3", True))
    sonar_token = str(l3.get("sonar_token") or _env_sonar_token()).strip()
    sonar_url = str(l3.get("sonar_url") or _env_sonar_url()).strip()
    sonar_org = str(l3.get("sonar_org") or _env_sonar_org()).strip()
    sonar_project_key = str(l3.get("sonar_project_key") or _env_sonar_project_key()).strip()

    reasons: list[str] = []
    if not enabled_by_user:
        reasons.append("L3 is disabled in settings.")
    if not docker["installed"]:
        reasons.append("Docker is required for Sonar scanner and PoC execution.")
    if not sonar_token:
        reasons.append("SONAR_TOKEN is not configured.")
    if not sonar_project_key:
        reasons.append("SONAR project key is not configured.")

    ready = enabled_by_user and docker["installed"] and bool(sonar_token) and bool(sonar_project_key)
    if ready:
        reason = "L3 is ready: Docker and Sonar credentials are available."
    else:
        reason = " ".join(reasons) if reasons else "L3 is not ready."

    return {
        "enabled": ready,
        "enabled_by_user": enabled_by_user,
        "reason": reason,
        "docker": docker,
        "sonar": {
            "configured": bool(sonar_token),
            "has_token": bool(sonar_token),
            "url": sonar_url,
            "org": sonar_org,
            "project_key": sonar_project_key,
        },
    }
