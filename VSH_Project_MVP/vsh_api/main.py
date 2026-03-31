from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import time
import logging
import threading

from dotenv import load_dotenv

from config import CHROMA_DB_DIR, SQLITE_DB_PATH
from repository.shared_db_adapter import get_shared_db
from shared.runtime_settings import (
    CONFIG_PATH,
    apply_runtime_env,
    detect_semgrep,
    detect_syft,
    get_effective_l3_status,
    get_effective_llm_status,
    load_config,
    save_config,
)
from vsh_runtime.engine import VshRuntimeEngine
from vsh_runtime.l3_integration import get_l3_runner, initialize_l3
from vsh_runtime.watcher import ProjectWatcher

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VSH API", version="1.0.0")

apply_runtime_env(load_config())
engine = VshRuntimeEngine()
watchers: dict[str, ProjectWatcher] = {}

shared_db = get_shared_db()
l3_runner = get_l3_runner(shared_db)
l3_enabled = False


def refresh_l3_state() -> bool:
    global l3_enabled
    l3_enabled = initialize_l3(shared_db)
    if l3_enabled:
        logger.info("L3 pipeline enabled")
    else:
        logger.warning("L3 disabled. L1/L2 analysis remains available.")
    return l3_enabled


refresh_l3_state()


class ScanRequest(BaseModel):
    path: str


class WatchRequest(BaseModel):
    path: str


class AnnotateRequest(BaseModel):
    path: str
    in_place: bool = False


def save_diagnostics(target_path: str, diagnostics: dict):
    if Path(target_path).is_file():
        vsh_dir = Path(target_path).parent / ".vsh"
    else:
        vsh_dir = Path(target_path) / ".vsh"
    vsh_dir.mkdir(exist_ok=True)
    diag_file = vsh_dir / "diagnostics.json"
    with open(diag_file, "w", encoding="utf-8") as handle:
        json.dump(diagnostics, handle, ensure_ascii=False, indent=2)


def save_report(target_path: str, report: dict):
    if Path(target_path).is_file():
        vsh_dir = Path(target_path).parent / ".vsh"
    else:
        vsh_dir = Path(target_path) / ".vsh"
    vsh_dir.mkdir(exist_ok=True)
    json_file = vsh_dir / "report.json"
    md_file = vsh_dir / "report.md"
    with open(json_file, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    if "previews" in report and "markdown" in report["previews"]:
        with open(md_file, "w", encoding="utf-8") as handle:
            handle.write(report["previews"]["markdown"])


@app.post("/scan/file")
def scan_file(req: ScanRequest):
    if not Path(req.path).is_file():
        raise HTTPException(status_code=400, detail="Invalid file path")

    result = engine.analyze_file(req.path)
    save_diagnostics(req.path, result["diagnostics"])
    save_report(req.path, result)

    if l3_enabled:
        l3_runner.run_async(req.path)

    return normalize_response(result, "file", req.path)


@app.post("/scan/project")
def scan_project(req: ScanRequest):
    if not Path(req.path).is_dir():
        raise HTTPException(status_code=400, detail="Invalid project path")

    result = engine.analyze_project(req.path)
    save_diagnostics(req.path, result["diagnostics"])
    save_report(req.path, result)

    if l3_enabled:
        l3_runner.run_async(req.path)

    return normalize_response(result, "project", req.path)


@app.post("/annotate/file")
def annotate_file(req: AnnotateRequest):
    try:
        if not Path(req.path).is_file():
            raise HTTPException(status_code=400, detail="Invalid file path")

        result = engine.annotate_file(req.path, in_place=req.in_place)
        return {
            "status": "success",
            "file": req.path,
            "in_place": req.in_place,
            "annotated_files": result.get("annotated_files", {}),
            "total_issues": result.get("total_issues", 0),
            "message": f"Generated annotated version with {result.get('total_issues', 0)} issue(s) marked",
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Annotation failed: {exc}") from exc


@app.post("/annotate/project")
def annotate_project(req: AnnotateRequest):
    try:
        if not Path(req.path).is_dir():
            raise HTTPException(status_code=400, detail="Invalid project path")

        result = engine.annotate_project(req.path, in_place=req.in_place)
        return {
            "status": "success",
            "project": req.path,
            "in_place": req.in_place,
            "files_annotated": result.get("files_annotated", 0),
            "annotated_files": result.get("annotated_files", {}),
            "total_issues": result.get("total_issues", 0),
            "message": f"Annotated {result.get('files_annotated', 0)} file(s) with {result.get('total_issues', 0)} issue(s) total",
        }
    except NotADirectoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Annotation failed: {exc}") from exc


@app.get("/diagnostics")
def get_diagnostics(path: str):
    if Path(path).is_file():
        vsh_dir = Path(path).parent / ".vsh"
    else:
        vsh_dir = Path(path) / ".vsh"
    diag_file = vsh_dir / "diagnostics.json"
    if not diag_file.exists():
        raise HTTPException(status_code=404, detail="Diagnostics not found")
    with open(diag_file, "r", encoding="utf-8") as handle:
        return json.load(handle)


@app.get("/settings")
def get_settings():
    return load_config()


@app.post("/settings")
def post_settings(config: dict):
    saved = save_config(config)
    apply_runtime_env(saved)
    refresh_l3_state()
    return {"status": "ok", "settings": saved}


@app.post("/settings/test-llm")
def test_llm(settings: dict):
    llm_status = get_effective_llm_status({"llm": settings})
    return {
        "provider": llm_status["provider"],
        "requested_provider": llm_status["requested_provider"],
        "connected": llm_status["connected"],
        "reason": llm_status["reason"],
    }


@app.post("/settings/check-syft")
def check_syft(settings: dict):
    return {"syft": detect_syft({"tools": settings})}


@app.post("/settings/check-semgrep")
def check_semgrep(settings: dict):
    return {"semgrep": detect_semgrep({"tools": settings})}


@app.get("/system/status")
def system_status():
    config = load_config()
    llm_status = get_effective_llm_status(config)
    syft_info = detect_syft(config)
    semgrep_info = detect_semgrep(config)
    l3_status = get_effective_l3_status(config)
    shared_db_path = getattr(shared_db, "db_file", None)
    chroma_path = Path(CHROMA_DB_DIR)
    sqlite_path = Path(SQLITE_DB_PATH)
    chroma_ready = chroma_path.exists() and any(chroma_path.iterdir())

    return {
        "api_server": "running",
        "python_core": "ready",
        "semgrep": semgrep_info,
        "syft": syft_info,
        "llm": llm_status,
        "l2": {
            "enabled": llm_status["enable_l2"],
            "provider": llm_status["provider"],
            "requested_provider": llm_status["requested_provider"],
            "rag_mode": "automatic",
            "reason": "VSH uses the local Chroma runtime database automatically when it is available.",
        },
        "l3": l3_status,
        "shared_db": {
            "path": str(shared_db_path) if shared_db_path else None,
            "exists": bool(shared_db_path and Path(shared_db_path).exists()),
        },
        "sqlite": {
            "path": str(sqlite_path),
            "exists": sqlite_path.exists(),
        },
        "chroma": {
            "path": str(chroma_path),
            "exists": chroma_path.exists(),
            "status": "ready" if chroma_ready else "empty",
            "rag_enabled": chroma_ready,
        },
        "config_path": str(CONFIG_PATH),
    }


@app.post("/watch/start")
def watch_start(req: WatchRequest):
    if not Path(req.path).exists():
        raise HTTPException(status_code=400, detail="Path does not exist")

    if req.path in watchers:
        raise HTTPException(status_code=400, detail="Watcher already running for this path")

    watcher = ProjectWatcher(req.path, debounce_sec=1.0)
    if not watcher.start():
        raise HTTPException(status_code=500, detail="Failed to start watcher")

    watchers[req.path] = watcher

    def process_watch_results():
        while watcher.is_running():
            results = watcher.get_last_results()
            for result in results:
                try:
                    if result.get("type") == "modified":
                        analysis = result.get("analysis")
                        if analysis:
                            file_path = result.get("path")
                            save_diagnostics(file_path, analysis.get("diagnostics", {}))
                            save_report(file_path, analysis)
                            print(f"[WATCH] Saved analysis for {file_path}")
                    elif result.get("type") == "error":
                        print(f"[WATCH] Error analyzing {result.get('path')}: {result.get('error')}")
                except Exception as exc:
                    print(f"[WATCH] Failed to save results: {exc}")
            time.sleep(0.1)

    result_processor = threading.Thread(target=process_watch_results, daemon=True)
    result_processor.start()

    return {
        "status": "started",
        "path": req.path,
        "message": "Watch mode enabled. File changes will trigger automatic analysis.",
    }


@app.post("/watch/stop")
def watch_stop(req: WatchRequest):
    if req.path not in watchers:
        raise HTTPException(status_code=400, detail="No active watcher for this path")

    watcher = watchers[req.path]
    if not watcher.stop():
        raise HTTPException(status_code=500, detail="Failed to stop watcher")

    del watchers[req.path]
    return {
        "status": "stopped",
        "path": req.path,
        "message": "Watch mode disabled.",
    }


@app.get("/watch/status")
def watch_status():
    return {
        "active_watchers": len(watchers),
        "watched_paths": list(watchers.keys()),
    }


@app.get("/file/content")
def get_file_content(path: str):
    file_path = Path(path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        return {"content": content}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading file: {exc}") from exc


@app.get("/health")
def health():
    return {"status": "ok"}


def normalize_response(result: dict, mode: str, target: str) -> dict:
    findings = []
    for v in result.get("vuln_records", []):
        finding = {
            "id": v.get("vuln_id"),
            "file": v.get("file_path"),
            "line": v.get("line_number"),
            "end_line": v.get("end_line_number", v.get("line_number")),
            "severity": v.get("severity"),
            "rule_id": v.get("rule_id"),
            "message": v.get("evidence"),
            "evidence": v.get("evidence"),
            "reachability_status": v.get("reachability_status"),
            "reachability_confidence": v.get("reachability_confidence", 0.0),
            "l2_reasoning": {
                "is_vulnerable": v.get("is_vulnerable", False),
                "confidence": v.get("l2_confidence", 0.0),
                "reasoning": v.get("reasoning_verdict", ""),
                "attack_scenario": v.get("l3_attack_scenario", ""),
                "fix_suggestion": v.get("fix_suggestion", ""),
            },
            "l3_validation": {
                "validated": v.get("l3_validated", False),
                "exploit_possible": v.get("exploit_possible", False),
                "confidence": v.get("l3_confidence", 0.0),
                "evidence": v.get("evidence", ""),
                "recommended_fix": v.get("fix_suggestion", ""),
            },
        }
        findings.append(finding)

    summary = result.get("aggregate_summary", {})
    top_risky_files = sorted(
        [
            (
                file_path,
                len([v for v in result.get("vuln_records", []) if v.get("file_path") == file_path]),
            )
            for file_path in set(v.get("file_path") for v in result.get("vuln_records", []))
        ],
        key=lambda item: item[1],
        reverse=True,
    )[:5]

    return {
        "target": target,
        "mode": mode,
        "findings": findings,
        "summary": {
            "total": len(findings),
            "critical": summary.get("risk_distribution", {}).get("P1", 0),
            "high": summary.get("risk_distribution", {}).get("P2", 0),
            "medium": summary.get("risk_distribution", {}).get("P3", 0),
            "low": summary.get("risk_distribution", {}).get("P4", 0)
            + summary.get("risk_distribution", {}).get("INFO", 0),
            "top_risky_files": top_risky_files,
        },
    }
