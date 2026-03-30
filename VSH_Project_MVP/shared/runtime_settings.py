from __future__ import annotations

import copy
import json
import os
import shutil
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

    scan = merged.setdefault("scan", {})
    scan["exclude_dirs"] = list(scan.get("exclude_dirs") or [])
    scan["include_extensions"] = list(scan.get("include_extensions") or [])

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

    gemini_key = str(llm.get("gemini_api_key") or "").strip()
    openai_key = str(llm.get("openai_api_key") or "").strip()

    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        os.environ["GOOGLE_API_KEY"] = gemini_key
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    if llm.get("model"):
        os.environ["GEMINI_MODEL"] = str(llm["model"])

    os.environ["LLM_PROVIDER"] = llm_status["provider"]
    return llm_status


def detect_syft(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = normalize_config(config)
    tools = cfg.get("tools", {})

    manual_path = str(tools.get("syft_path") or "").strip()
    auto_detect = bool(tools.get("syft_auto_detect", True))
    found_path = ""
    source = "missing"

    if manual_path and Path(manual_path).exists():
        found_path = manual_path
        source = "manual"
    elif auto_detect:
        detected = shutil.which("syft")
        if detected:
            found_path = detected
            source = "auto"

    return {
        "installed": bool(found_path),
        "path": found_path,
        "source": source,
        "auto_detect": auto_detect,
    }
