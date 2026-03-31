from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, List

from models.scan_result import ScanResult
from models.vulnerability import Vulnerability
from repository.base_repository import BaseReadRepository
from shared.contracts import BaseScanner
from shared.runtime_settings import detect_semgrep


def _language_for_semgrep(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".js", ".jsx", ".mjs"}:
        return "javascript"
    if suffix in {".ts", ".tsx"}:
        return "typescript"
    return "generic"


def _base_rule_configs() -> list[dict[str, Any]]:
    return [
        {
            "id": "vsh.python.eval",
            "message": "Direct eval() use can lead to code injection.",
            "severity": "ERROR",
            "languages": ["python"],
            "metadata": {
                "cwe_id": "CWE-95",
                "severity": "CRITICAL",
                "references": ["OWASP Code Injection Prevention"],
                "engine": "semgrep_cli",
                "title": "eval() use",
            },
            "pattern": "eval(...)",
        },
        {
            "id": "vsh.python.os-system",
            "message": "os.system() may allow command injection.",
            "severity": "ERROR",
            "languages": ["python"],
            "metadata": {
                "cwe_id": "CWE-78",
                "severity": "HIGH",
                "references": ["OWASP Command Injection Prevention"],
                "engine": "semgrep_cli",
                "title": "os.system() use",
            },
            "pattern": "os.system(...)",
        },
        {
            "id": "vsh.python.subprocess-shell-true",
            "message": "subprocess with shell=True may allow command injection.",
            "severity": "ERROR",
            "languages": ["python"],
            "metadata": {
                "cwe_id": "CWE-78",
                "severity": "HIGH",
                "references": ["OWASP Command Injection Prevention"],
                "engine": "semgrep_cli",
                "title": "subprocess shell=True",
            },
            "pattern-either": [{"pattern": "subprocess.run(..., shell=True, ...)"}, {"pattern": "subprocess.Popen(..., shell=True, ...)"}],
        },
        {
            "id": "vsh.python.pickle-loads",
            "message": "pickle.loads() may deserialize untrusted input.",
            "severity": "ERROR",
            "languages": ["python"],
            "metadata": {
                "cwe_id": "CWE-502",
                "severity": "CRITICAL",
                "references": ["OWASP Deserialization Cheat Sheet"],
                "engine": "semgrep_cli",
                "title": "pickle.loads() use",
            },
            "pattern": "pickle.loads(...)",
        },
        {
            "id": "vsh.javascript.innerhtml",
            "message": "innerHTML assignment may lead to XSS.",
            "severity": "WARNING",
            "languages": ["javascript", "typescript"],
            "metadata": {
                "cwe_id": "CWE-79",
                "severity": "HIGH",
                "references": ["OWASP XSS Prevention Cheat Sheet"],
                "engine": "semgrep_cli",
                "title": "innerHTML assignment",
            },
            "pattern": "$EL.innerHTML = $VALUE",
        },
        {
            "id": "vsh.javascript.document-write",
            "message": "document.write() may lead to XSS.",
            "severity": "WARNING",
            "languages": ["javascript", "typescript"],
            "metadata": {
                "cwe_id": "CWE-79",
                "severity": "HIGH",
                "references": ["OWASP XSS Prevention Cheat Sheet"],
                "engine": "semgrep_cli",
                "title": "document.write() use",
            },
            "pattern": "document.write(...)",
        },
    ]


class SemgrepCLIScanner(BaseScanner):
    def __init__(self, knowledge_repo: BaseReadRepository | None = None, config: dict[str, Any] | None = None):
        self.knowledge_repo = knowledge_repo
        self.config = config

    def is_available(self) -> bool:
        return detect_semgrep(self.config)["installed"]

    def scan(self, file_path: str) -> ScanResult:
        path = Path(file_path)
        if not path.exists():
            return ScanResult(file_path=file_path, language=_language_for_semgrep(file_path), findings=[])

        tool = detect_semgrep(self.config)
        semgrep_path = tool.get("path")
        if not semgrep_path:
            return ScanResult(file_path=str(path), language=_language_for_semgrep(str(path)), findings=[])

        rules = self._build_rules(str(path))
        if not rules:
            return ScanResult(file_path=str(path), language=_language_for_semgrep(str(path)), findings=[])

        findings, note = self._run_semgrep(semgrep_path, str(path), rules)
        result = ScanResult(
            file_path=str(path),
            language="multi" if path.is_dir() else _language_for_semgrep(str(path)),
            findings=findings,
        )
        if note:
            result.notes.append(note)
        return result

    def _build_rules(self, target_path: str) -> list[dict[str, Any]]:
        rules = list(_base_rule_configs())
        language = _language_for_semgrep(target_path)

        if self.knowledge_repo is None:
            return rules

        for item in self.knowledge_repo.find_all():
            pattern = str(item.get("pattern") or "").strip()
            if not pattern:
                continue
            rule_language = "python" if language == "generic" else language
            metadata = {
                "cwe_id": item.get("id", "UNKNOWN"),
                "severity": item.get("severity", "MEDIUM"),
                "references": [item.get("reference")] if item.get("reference") else [],
                "engine": "semgrep_cli",
                "title": item.get("name") or item.get("id") or "Knowledge rule",
                "source": "knowledge_repo",
            }
            rules.append(
                {
                    "id": f"vsh.knowledge.{item.get('id', 'unknown').lower()}",
                    "message": item.get("description") or item.get("name") or item.get("id") or "Knowledge rule match",
                    "severity": "WARNING",
                    "languages": [rule_language],
                    "metadata": metadata,
                    "pattern-regex": pattern,
                }
            )
        return rules

    def _run_semgrep(self, semgrep_path: str, target_path: str, rules: list[dict[str, Any]]) -> tuple[list[Vulnerability], str]:
        config_payload = {"rules": rules}
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
            config_path = handle.name
            json.dump(config_payload, handle, ensure_ascii=False, indent=2)

        cmd = [
            semgrep_path,
            "scan",
            "--config",
            config_path,
            "--json",
            "--quiet",
            "--disable-version-check",
            target_path,
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            if proc.returncode not in {0, 1}:
                message = (proc.stderr or proc.stdout or "").strip()
                return [], f"semgrep_cli_error={message[:300]}"
            payload = json.loads(proc.stdout or "{}")
            return self._parse_results(payload), "engine=semgrep_cli"
        except Exception as exc:
            return [], f"semgrep_cli_error={exc}"
        finally:
            Path(config_path).unlink(missing_ok=True)

    def _parse_results(self, payload: dict[str, Any]) -> list[Vulnerability]:
        findings: list[Vulnerability] = []
        for result in payload.get("results", []):
            start = result.get("start", {}) or {}
            extra = result.get("extra", {}) or {}
            metadata = extra.get("metadata", {}) or {}
            references = metadata.get("references") or []
            if isinstance(references, str):
                references = [references]
            findings.append(
                Vulnerability(
                    file_path=result.get("path"),
                    rule_id=result.get("check_id"),
                    cwe_id=metadata.get("cwe_id", "UNKNOWN"),
                    severity=metadata.get("severity", "MEDIUM"),
                    line_number=int(start.get("line", 1) or 1),
                    code_snippet=(extra.get("lines") or "").strip() or extra.get("message") or "",
                    references=[str(ref) for ref in references if ref],
                    metadata={
                        "engine": metadata.get("engine", "semgrep_cli"),
                        "title": metadata.get("title") or extra.get("message") or result.get("check_id"),
                        "source": metadata.get("source", "semgrep_cli"),
                        "semgrep_message": extra.get("message"),
                    },
                )
            )
        return findings

    def supported_languages(self) -> List[str]:
        return ["python", "javascript", "typescript", "multi"]
