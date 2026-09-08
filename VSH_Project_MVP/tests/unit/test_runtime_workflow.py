from __future__ import annotations

import json
import time
from pathlib import Path

from layer2.reasoning import L2ReasoningPipeline
from layer2.reasoning.models import validate_reasoning_result
from vsh_runtime.diagnostics import build_markdown_preview, vuln_to_diagnostic
from vsh_runtime.engine import VshRuntimeEngine
from vsh_runtime.findings_export import build_findings_export
from vsh_runtime.risk import compute_vuln_risk
from vsh_runtime.sca_usage import build_package_usage_index
from vsh_runtime.watcher import ProjectWatcher


def test_watcher_save_event(tmp_path: Path):
    file = tmp_path / "app.py"
    file.write_text("print('x')\n", encoding="utf-8")
    watcher = ProjectWatcher(str(tmp_path), debounce_sec=0.0, interval=0.1)
    watcher.poll_once()
    time.sleep(0.01)
    file.write_text("print(eval(input()))\n", encoding="utf-8")
    events = watcher.poll_once()
    assert isinstance(events, list)


def test_diagnostics_json_schema(tmp_path: Path):
    engine = VshRuntimeEngine()
    file = tmp_path / "a.py"
    file.write_text("print(eval(input()))\n", encoding="utf-8")
    result = engine.get_diagnostics(str(file))
    diag = result["diagnostics"][0]
    for key in ["file", "line", "severity", "source", "rule_id", "message", "suggestion"]:
        assert key in diag


def test_non_destructive_preview(tmp_path: Path):
    file = tmp_path / "a.py"
    original = "print(eval(input()))\n"
    file.write_text(original, encoding="utf-8")
    engine = VshRuntimeEngine()
    payload = engine.analyze_file(str(file))
    md = build_markdown_preview(payload["diagnostics"])
    assert "Diagnostics Preview" in md
    assert file.read_text(encoding="utf-8") == original


def test_project_level_package_usage_index(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("requests==2.0.0\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("import requests\nrequests.get('http://x')\n", encoding="utf-8")
    index = build_package_usage_index(str(tmp_path))
    assert "requests" in index


def test_vulnerable_api_referenced_status(tmp_path: Path):
    (tmp_path / "app.py").write_text("import requests\nrequests.get('http://x')\n", encoding="utf-8")
    idx = build_package_usage_index(str(tmp_path))
    assert idx["requests"]["usage_status"] in {"vulnerable_api_referenced", "needs_manual_review", "package_imported"}


def test_l2_reasoning_schema_validation():
    payload = validate_reasoning_result({"linked_vuln_id": "V1", "verdict": "bad", "confidence": 2})
    assert payload.verdict == "needs_review"
    assert 0.0 <= payload.confidence <= 1.0


def test_mock_reasoning_provider(tmp_path: Path):
    file = tmp_path / "a.py"
    file.write_text("print(eval(input()))\n", encoding="utf-8")
    engine = VshRuntimeEngine()
    out = engine.analyze_file(str(file))
    assert out["l2_reasoning_results"]


def test_aggregate_priority_risk_score():
    score, pri = compute_vuln_risk({"severity": "HIGH", "reachability_status": "reachable"}, {"verdict": "likely_vulnerable", "confidence": 0.9})
    assert score > 0
    assert pri in {"P1", "P2", "P3", "P4", "INFO"}


def test_l1_l2_l3_handoff_shape(tmp_path: Path):
    file = tmp_path / "a.py"
    file.write_text("print(eval(input()))\n", encoding="utf-8")
    payload = VshRuntimeEngine().analyze_file(str(file))
    assert "vuln_records" in payload and "l2_reasoning_results" in payload and "l3_validation_results" in payload
    assert all("l3_validated" in v for v in payload["vuln_records"])
    assert all("l3_confidence" in v for v in payload["vuln_records"])
    assert all(v["l3_validated"] is None for v in payload["vuln_records"])
    assert all(v["l3_confidence"] is None for v in payload["vuln_records"])


def test_cli_snapshot_shape(tmp_path: Path):
    file = tmp_path / "a.py"
    file.write_text("print(eval(input()))\n", encoding="utf-8")
    payload = VshRuntimeEngine().analyze_file(str(file))
    dumped = json.dumps(payload, ensure_ascii=False)
    assert "diagnostics" in dumped and "aggregate_summary" in dumped


def test_shared_findings_export_preserves_vsh_evidence():
    payload = {
        "vuln_records": [
            {
                "vuln_id": "V-1",
                "rule_id": "python.lang.security.audit.eval-detected",
                "detected_at": "2026-09-08T00:00:00+00:00",
                "file_path": "src/app.py",
                "line_number": 12,
                "end_line_number": 12,
                "column_number": 5,
                "end_column_number": 18,
                "language": "python",
                "vuln_type": "code execution",
                "cwe_id": "CWE-95",
                "cve_id": None,
                "severity": "HIGH",
                "reachability_status": "reachable",
                "reachability_confidence": "high",
                "kisa_ref": "KISA-SW-SECURE-CODING",
                "fss_ref": None,
                "owasp_ref": "OWASP A03:2021",
                "evidence": "eval(user_input)",
                "fix_suggestion": "Use an allowlisted parser.",
                "risk_score": 93.0,
                "final_priority": "P1",
            }
        ],
        "package_records": [],
        "l2_reasoning_results": [
            {
                "linked_vuln_id": "V-1",
                "verdict": "likely_vulnerable",
                "confidence": 0.85,
                "reasoning": "User input reaches eval.",
                "attack_scenario": "An attacker supplies Python code.",
                "secure_fix_guidance": "Replace eval.",
                "provider_name": "mock",
                "model_name": None,
            }
        ],
    }

    exported = build_findings_export(
        payload, generated_at="2026-09-08T01:00:00+00:00"
    )

    assert exported["schema_version"] == "1.0"
    finding = exported["findings"][0]
    assert finding["source"] == "VSH"
    assert finding["finding_type"] == "application_security.code_finding"
    assert finding["asset"]["value"] == "src/app.py"
    assert finding["score"] == 93.0
    assert finding["confidence"] == 0.85
    assert finding["evidence"]["cwe_id"] == "CWE-95"
    assert finding["evidence"]["reasoning"]["provider"] == "mock"


def test_write_outputs_adds_shared_findings_file(tmp_path: Path):
    payload = {
        "vuln_records": [],
        "package_records": [
            {
                "package_id": "P-1",
                "detected_at": "2026-09-08T00:00:00+00:00",
                "name": "requests",
                "version": "2.19.0",
                "ecosystem": "pypi",
                "severity": "HIGH",
                "usage_status": "vulnerable_api_referenced",
                "risk_score": 88.0,
                "evidence": "requests.get is referenced",
                "fix_suggestion": "Upgrade requests.",
            }
        ],
        "l2_reasoning_results": [],
        "diagnostics": [],
    }

    outputs = VshRuntimeEngine().write_outputs(payload, str(tmp_path))
    findings_path = Path(outputs["findings"])
    exported = json.loads(findings_path.read_text(encoding="utf-8"))

    assert findings_path.name == "findings.json"
    assert exported["findings"][0]["asset"]["value"] == "requests@2.19.0"
    assert (
        exported["findings"][0]["finding_type"]
        == "application_security.package_risk"
    )
