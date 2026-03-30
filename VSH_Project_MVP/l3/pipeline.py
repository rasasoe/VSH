from l3.normalizer import L3Normalizer
from l3.providers.base import (
    AbstractPoCProvider,
    AbstractSBOMProvider,
    AbstractSonarQubeProvider,
)


class L3Pipeline:
    """M1 -> M2 -> M2.5 -> M3 -> M4 orchestration."""

    def __init__(
        self,
        sonarqube: AbstractSonarQubeProvider,
        sbom: AbstractSBOMProvider,
        poc: AbstractPoCProvider,
        normalizer: L3Normalizer,
    ):
        self.sonarqube = sonarqube
        self.sbom = sbom
        self.poc = poc
        self.normalizer = normalizer

    async def run(self, project_path: str) -> None:
        vuln_records = await self.sonarqube.scan(project_path)
        print(f"[L3 Pipeline] M1 scan complete: {len(vuln_records)} records")

        package_records = await self.sbom.scan(project_path)
        for package in package_records:
            await self.normalizer.save(package)
        print(f"[L3 Pipeline] M2 scan complete: {len(package_records)} records")

        from types import SimpleNamespace

        from l3.adapters import pydantic_vuln_to_l3

        shared_l2 = [record for record in getattr(self.normalizer.db, '_vulns', []) if record.get('source') == 'L2']
        l2_records = []
        for record in shared_l2:
            try:
                l2_records.append(pydantic_vuln_to_l3(SimpleNamespace(**record)))
            except Exception:
                continue
        vuln_records.extend(l2_records)
        print(f"[L3 Pipeline] M2.5 imported {len(l2_records)} L2 records")

        for record in vuln_records:
            print(f"[L3 Pipeline] M3 PoC running: {record.vuln_id}")
            try:
                record = await self.poc.verify(record)
            except Exception as exc:
                record.status = 'poc_skipped'
                print(f"[L3 Pipeline] poc_skipped: {record.vuln_id} - {exc}")
            await self.normalizer.save(record)

        print(f"[L3 Pipeline] M3 complete: {len(vuln_records)} records processed")
        print(f"[L3 Pipeline] Finished: {project_path}")
