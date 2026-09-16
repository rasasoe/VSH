from __future__ import annotations

from pathlib import Path

from layer1.common import detect_project_languages
from layer1.common.schema_normalizer import normalize_scan_result
from layer1.scanner.sbom_scanner import SBOMScanner
from layer1.scanner.vsh_l1_scanner import VSHL1Scanner
from layer2.verifier.osv_verifier import OsvVerifier
from layer2.verifier.providers import MockOsvProvider, OfflineRegistryProvider
from layer2.verifier.registry_verifier import RegistryVerifier
from models.scan_result import ScanResult
from models.vulnerability import Vulnerability
from reporting.report_engine import ReportEngine
from vsh_runtime.engine import VshRuntimeEngine
from shared.finding_dedup import deduplicate_findings


def test_reachability_propagates_to_vulnrecord(tmp_path: Path):
    target = tmp_path / "app.py"
    target.write_text("user = input('x')\nprint(eval(user))\n", encoding="utf-8")
    scanner = VSHL1Scanner()
    result = scanner.scan(str(target))
    rec = next(r for r in result.vuln_records if r.cwe_id == "CWE-95")
    assert rec.reachability_status in {"reachable", "unknown", "unreachable"}
    assert rec.reachability_confidence in {"high", "medium", "low"}


def test_cwe95_has_mapping():
    finding = Vulnerability(file_path="a.py", cwe_id="CWE-95", severity="CRITICAL", line_number=2, code_snippet="eval(x)")
    result = normalize_scan_result(ScanResult(file_path="a.py", language="python", findings=[finding]))
    assert result.vuln_records[0].owasp_ref == "A03:2021"
    assert result.vuln_records[0].kisa_ref != "미매핑-추후보강"


def test_sbom_scanner_uses_target_root(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "requirements.txt").write_text("requests==2.0.0\n", encoding="utf-8")
    (root / "src.py").write_text("print('ok')", encoding="utf-8")
    findings = SBOMScanner().scan(str(root / "src.py")).findings
    assert all(str(root) in (f.file_path or "") for f in findings)


def test_mixed_language_detection(tmp_path: Path):
    (tmp_path / "a.py").write_text("print('x')", encoding="utf-8")
    (tmp_path / "b.ts").write_text("console.log('x')", encoding="utf-8")
    langs = detect_project_languages(str(tmp_path))
    assert langs == {"python", "typescript"}


def test_duplicate_location_retains_both_rule_ids():
    f1 = Vulnerability(file_path="a.py", cwe_id="CWE-78", severity="HIGH", line_number=1, code_snippet="os.system(x)", rule_id="R1")
    f2 = Vulnerability(file_path="a.py", cwe_id="CWE-78", severity="HIGH", line_number=1, code_snippet="os.system(x)", rule_id="R2")
    dedup = deduplicate_findings([f1, f2])
    assert len(dedup) == 1
    assert set(dedup[0].metadata['merged_rule_ids']) == {'R1', 'R2'}


def test_typosquatting_evidence(tmp_path: Path):
    target = tmp_path / "a.py"
    target.write_text("import reqquests\n", encoding="utf-8")
    findings = VSHL1Scanner().scan(str(target)).findings
    typo = [f for f in findings if f.cwe_id == "CWE-1104"]
    assert typo
    assert "why_detected" in typo[0].metadata


def test_provider_interfaces_smoke():
    reg = RegistryVerifier(provider=OfflineRegistryProvider())
    osv = OsvVerifier(provider=MockOsvProvider())
    finding = Vulnerability(file_path="requirements.txt", cwe_id="CWE-829", severity="HIGH", line_number=1, code_snippet="requests==2.0.0")
    assert "registry_status" in reg.verify(finding)
    assert "osv_status" in osv.verify(finding)


def test_e2e_l1_l2_l3_like_flow(tmp_path: Path):
    target = tmp_path / "app.py"
    target.write_text("import reqquests\nuser=input()\nprint(eval(user))\n", encoding="utf-8")
    payload = VshRuntimeEngine().analyze_file(str(target))
    assert len(payload['vuln_records']) >= 1
    assert payload['l2_reasoning_results']
    assert payload['l3_validation_results'] == []
    assert all(v['l3_validated'] is None for v in payload['vuln_records'])


def test_report_snapshot_like(tmp_path: Path):
    finding = Vulnerability(file_path="a.py", cwe_id="CWE-95", severity="CRITICAL", line_number=1, code_snippet="eval(x)", reachability_status="reachable", metadata={"reachability_confidence":"high"})
    result = normalize_scan_result(ScanResult(file_path="a.py", language="python", findings=[finding]))
    engine = ReportEngine()
    payload = {'vuln_records': [v.model_dump() for v in result.vuln_records]}
    out = tmp_path / "summary.md"
    engine.write_markdown(str(out), payload)
    text = out.read_text(encoding="utf-8")
    assert "Reachable issues" in text
    assert 'CWE-95 @ a.py:1' in text


def test_static_scan_does_not_execute_or_modify_target(tmp_path):
    marker = tmp_path / 'executed.txt'
    source = tmp_path / 'untrusted.py'
    content = f'from pathlib import Path\nPath({str(marker)!r}).write_text("executed")\nuser=input()\neval(user)\n'
    source.write_text(content, encoding='utf-8')
    result = VSHL1Scanner().scan(str(source))
    assert result.findings
    assert not marker.exists()
    assert source.read_text(encoding='utf-8') == content
