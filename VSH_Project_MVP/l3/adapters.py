import dataclasses

from l3.models.package_record import PackageRecord as L3PackageRecord
from l3.models.vuln_record import VulnRecord as L3VulnRecord
from models.common_schema import PackageRecord as PydanticPackageRecord
from models.common_schema import VulnRecord as PydanticVulnRecord


def l3_vuln_to_pydantic(record: L3VulnRecord) -> PydanticVulnRecord:
    data = dataclasses.asdict(record)
    data["evidence"] = data.pop("code_snippet")
    for field in ("line_number", "end_line_number", "column_number", "end_column_number"):
        if data[field] < 1:
            data[field] = 1
    return PydanticVulnRecord(**data)


def l3_package_to_pydantic(record: L3PackageRecord) -> PydanticPackageRecord:
    data = dataclasses.asdict(record)
    data["evidence"] = data.pop("code_snippet")
    return PydanticPackageRecord(**data)


def pydantic_vuln_to_l3(record: PydanticVulnRecord) -> L3VulnRecord:
    return L3VulnRecord(
        vuln_id=record.vuln_id,
        rule_id=record.rule_id,
        source=record.source,
        detected_at=record.detected_at,
        file_path=record.file_path,
        line_number=record.line_number,
        end_line_number=record.end_line_number,
        column_number=record.column_number,
        end_column_number=record.end_column_number,
        language=record.language,
        code_snippet=record.evidence,
        vuln_type=record.vuln_type,
        cwe_id=record.cwe_id,
        cve_id=record.cve_id,
        cvss_score=record.cvss_score,
        severity=record.severity,
        reachability_status=record.reachability_status,
        reachability_confidence=record.reachability_confidence,
        kisa_ref=record.kisa_ref,
        fss_ref=record.fss_ref,
        owasp_ref=record.owasp_ref,
        fix_suggestion=record.fix_suggestion,
        status=record.status,
        action_at=record.action_at,
    )
