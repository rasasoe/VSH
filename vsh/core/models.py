from dataclasses import dataclass, field
from typing import Literal, Optional, Any

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

@dataclass
class Finding:
    id: str
    title: str
    severity: Severity
    cwe: Optional[str] = None
    cvss: Optional[float] = None
    cve: Optional[str] = None
    file: str = ""
    line: int = 1
    column: int = 1
    message: str = ""
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    reachability: Optional[Literal["YES","NO","UNKNOWN"]] = "UNKNOWN"
    references: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

@dataclass
class DependencyVuln:
    ecosystem: str  # PyPI, npm
    name: str
    version: Optional[str] = None
    vuln_id: Optional[str] = None
    summary: Optional[str] = None
    severity: Severity = "MEDIUM"
    references: list[str] = field(default_factory=list)

@dataclass
class ScanResult:
    project: str
    findings: list[Finding] = field(default_factory=list)
    dep_vulns: list[DependencyVuln] = field(default_factory=list)
    hallucinated_packages: list[str] = field(default_factory=list)
    score: int = 100
    notes: list[str] = field(default_factory=list)
