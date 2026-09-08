from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "1.0"
SEVERITY_SCORE = {"CRITICAL": 95.0, "HIGH": 78.0, "MEDIUM": 55.0, "LOW": 30.0}
REACHABILITY_CONFIDENCE = {"high": 0.85, "medium": 0.65, "low": 0.45}


def _clamp(value: Any, minimum: float, maximum: float) -> float:
    try:
        return max(minimum, min(maximum, float(value)))
    except (TypeError, ValueError):
        return minimum


def _score(record: dict[str, Any]) -> float:
    if record.get("risk_score") is not None:
        return _clamp(record["risk_score"], 0.0, 100.0)
    if record.get("cvss_score") is not None:
        return _clamp(float(record["cvss_score"]) * 10.0, 0.0, 100.0)
    return SEVERITY_SCORE.get(str(record.get("severity", "")).upper(), 0.0)


def _references(*values: Any) -> list[str]:
    refs: list[str] = []
    for value in values:
        if not value:
            continue
        if isinstance(value, list):
            candidates = value
        else:
            candidates = [value]
        for candidate in candidates:
            normalized = str(candidate).strip()
            if normalized and normalized not in refs:
                refs.append(normalized)
    return refs


def _vulnerability_finding(
    record: dict[str, Any],
    reasoning: dict[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    reachability = str(record.get("reachability_status") or "unknown")
    reachability_band = str(record.get("reachability_confidence") or "low").lower()
    if reasoning:
        confidence = _clamp(reasoning.get("confidence"), 0.0, 1.0)
        provider = str(reasoning.get("provider_name") or "unknown")
        verdict = str(reasoning.get("verdict") or "needs_review")
        confidence_basis = (
            f"L2 {provider} verdict={verdict}; "
            f"reachability={reachability}/{reachability_band}"
        )
    else:
        confidence = REACHABILITY_CONFIDENCE.get(reachability_band, 0.45)
        confidence_basis = (
            f"L1 reachability signal={reachability}/{reachability_band}; "
            "no L2 reasoning result"
        )

    cwe_id = str(record.get("cwe_id") or "unclassified")
    vuln_type = str(record.get("vuln_type") or record.get("rule_id") or "code finding")
    evidence = {
        "vuln_id": record.get("vuln_id"),
        "rule_id": record.get("rule_id"),
        "cwe_id": record.get("cwe_id"),
        "cve_id": record.get("cve_id"),
        "location": {
            "file": record.get("file_path"),
            "start_line": record.get("line_number"),
            "end_line": record.get("end_line_number"),
            "start_column": record.get("column_number"),
            "end_column": record.get("end_column_number"),
        },
        "reachability": {
            "status": reachability,
            "confidence": reachability_band,
        },
        "detection_evidence": record.get("evidence"),
        "fix_suggestion": record.get("fix_suggestion"),
        "final_priority": record.get("final_priority"),
    }
    if reasoning:
        evidence["reasoning"] = {
            "verdict": reasoning.get("verdict"),
            "summary": reasoning.get("reasoning"),
            "attack_scenario": reasoning.get("attack_scenario"),
            "secure_fix_guidance": reasoning.get("secure_fix_guidance"),
            "provider": reasoning.get("provider_name"),
            "model": reasoning.get("model_name"),
        }

    return {
        "source": "VSH",
        "asset": {
            "type": "source_file",
            "value": str(record.get("file_path") or "unknown"),
            "language": record.get("language"),
        },
        "finding_type": "application_security.code_finding",
        "title": f"{cwe_id}: {vuln_type}",
        "severity": str(record.get("severity") or "LOW").lower(),
        "score": _score(record),
        "confidence": confidence,
        "confidence_basis": confidence_basis,
        "evidence": evidence,
        "references": _references(
            record.get("cve_id"),
            record.get("owasp_ref"),
            record.get("kisa_ref"),
            record.get("fss_ref"),
        ),
        "detected_at": str(record.get("detected_at") or generated_at),
    }


def _package_finding(record: dict[str, Any], generated_at: str) -> dict[str, Any]:
    usage_status = str(record.get("usage_status") or "needs_manual_review")
    confidence = {
        "reachable_package_risk": 0.9,
        "vulnerable_api_referenced": 0.85,
        "package_imported": 0.7,
        "package_present": 0.55,
    }.get(usage_status, 0.45)
    name = str(record.get("name") or "unknown")
    version = str(record.get("version") or "unknown")
    return {
        "source": "VSH",
        "asset": {
            "type": "package",
            "value": f"{name}@{version}",
            "ecosystem": record.get("ecosystem"),
        },
        "finding_type": "application_security.package_risk",
        "title": f"{name} {version} dependency risk",
        "severity": str(record.get("severity") or "LOW").lower(),
        "score": _score(record),
        "confidence": confidence,
        "confidence_basis": f"dependency usage signal={usage_status}",
        "evidence": {
            "package_id": record.get("package_id"),
            "cve_id": record.get("cve_id"),
            "license": record.get("license"),
            "license_risk": bool(record.get("license_risk")),
            "usage_status": usage_status,
            "affected_module": record.get("affected_module"),
            "affected_symbol": record.get("affected_symbol"),
            "affected_api_patterns": record.get("affected_api_patterns") or [],
            "exploitability_hint": record.get("exploitability_hint"),
            "detection_evidence": record.get("evidence"),
            "fix_suggestion": record.get("fix_suggestion"),
            "final_priority": record.get("final_priority"),
        },
        "references": _references(
            record.get("cve_id"),
            record.get("advisory_id"),
            record.get("advisory_source"),
        ),
        "detected_at": str(record.get("detected_at") or generated_at),
    }


def build_findings_export(
    payload: dict[str, Any], generated_at: str | None = None
) -> dict[str, Any]:
    """Convert VSH results to the shared portfolio Finding contract."""

    timestamp = generated_at or datetime.now(timezone.utc).isoformat()
    reasoning_by_id = {
        item.get("linked_vuln_id"): item
        for item in payload.get("l2_reasoning_results", [])
        if item.get("linked_vuln_id")
    }
    findings = [
        _vulnerability_finding(
            record,
            reasoning_by_id.get(record.get("vuln_id")),
            timestamp,
        )
        for record in payload.get("vuln_records", [])
    ]
    findings.extend(
        _package_finding(record, timestamp)
        for record in payload.get("package_records", [])
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": timestamp,
        "findings": findings,
    }
