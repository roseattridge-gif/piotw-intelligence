from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import ClassVar

from pypdf import PdfReader

from evidence_engine_v0_1.models import JobRecord, RawEvidence


class Collector(ABC):
    """Common evidence contract for report, jobs, and future collectors."""

    version: str

    @abstractmethod
    def collect(self, company_id: str, as_of_date: date) -> list[RawEvidence]: ...


class FixtureReportCollector(Collector):
    version = "fixture-report-collector-0.1.0"

    def __init__(self, records: list[dict], raw_root: str | Path):
        self.records = records
        self.raw_root = Path(raw_root)

    def collect(self, company_id: str, as_of_date: date) -> list[RawEvidence]:
        output = []
        for row in self.records:
            published = date.fromisoformat(row["publication_date"])
            if row["company_id"] != company_id or published > as_of_date:
                continue
            text = row["text"]
            digest = hashlib.sha256(text.encode()).hexdigest()
            path = self.raw_root / company_id / f'{row["reporting_period"]}.txt'
            output.append(RawEvidence(
                evidence_id=f"ee01-{company_id}-{row['reporting_period']}",
                company_id=company_id, source_type=row["source_type"],
                source_title=row["source_title"], source_url=row["source_url"],
                reporting_period=row["reporting_period"], publication_date=published,
                observation_date=date.fromisoformat(row["period_end"]),
                collected_at=datetime.fromisoformat(row["collected_at"]),
                information_available_at=datetime.fromisoformat(row["information_available_at"]),
                content_hash=digest, raw_text=text, raw_storage_path=str(path),
                collector_version=self.version,
            ))
        return output


class LocalReportCollector(Collector):
    """Collect already-acquired PDF/HTML/text issuer reports without network access."""

    version = "local-report-collector-0.1.0"
    supported_source_types: ClassVar[set[str]] = {
        "annual_report", "annual_accounts", "interim_report", "full_year_results",
        "regulatory_results_announcement",
    }

    def __init__(self, manifest: list[dict]):
        self.manifest = manifest

    @staticmethod
    def extract_text(path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            return "\n".join(f"[PAGE {index}]\n{page.extract_text() or ''}"
                             for index, page in enumerate(PdfReader(path).pages, 1))
        text = path.read_text(errors="replace")
        if path.suffix.lower() in {".html", ".htm"}:
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text)
        return text

    def collect(self, company_id: str, as_of_date: date) -> list[RawEvidence]:
        output = []
        for row in self.manifest:
            publication = date.fromisoformat(row["publication_date"])
            if row["company_id"] != company_id or publication > as_of_date:
                continue
            if row["source_type"] not in self.supported_source_types:
                raise ValueError(f"unsupported report source type: {row['source_type']}")
            path = Path(row["path"])
            text = self.extract_text(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            output.append(RawEvidence(
                evidence_id=row["evidence_id"], company_id=company_id,
                source_type=row["source_type"], source_title=row["source_title"],
                source_url=row["source_url"], reporting_period=row["reporting_period"],
                publication_date=publication,
                observation_date=date.fromisoformat(row["period_end"]),
                collected_at=datetime.fromisoformat(row["collected_at"]),
                information_available_at=datetime.fromisoformat(row["information_available_at"]),
                content_hash=digest, raw_text=text, raw_storage_path=str(path),
                collector_version=self.version, mime_type=row.get("mime_type", "application/pdf")))
        return output


class FixtureJobsCollector(Collector):
    """Offline jobs collector using the same RawEvidence contract as reports."""

    version = "fixture-jobs-collector-0.1.0"

    def __init__(self, snapshots: list[tuple[datetime, list[JobRecord]]], raw_root: str | Path):
        self.snapshots = snapshots
        self.raw_root = Path(raw_root)

    def collect(self, company_id: str, as_of_date: date) -> list[RawEvidence]:
        output = []
        for observed_at, jobs in self.snapshots:
            if observed_at.date() > as_of_date:
                continue
            selected = [job for job in jobs if job.company_id == company_id]
            text = json.dumps([job.model_dump(mode="json") for job in selected], sort_keys=True)
            digest = hashlib.sha256(text.encode()).hexdigest()
            evidence_id = f"ee01-jobs-{company_id}-{observed_at.date()}"
            output.append(RawEvidence(
                evidence_id=evidence_id, company_id=company_id, source_type="careers_jobs",
                source_title=f"Careers snapshot {observed_at.date()}",
                source_url=f"fixture://jobs/{company_id}/{observed_at.date()}",
                reporting_period=observed_at.date().isoformat(), publication_date=observed_at.date(),
                observation_date=observed_at.date(), collected_at=observed_at,
                information_available_at=observed_at, content_hash=digest, raw_text=text,
                raw_storage_path=str(self.raw_root / company_id / f"{evidence_id}.json"),
                collector_version=self.version, mime_type="application/json"))
        return output


def jobs_from_raw(evidence: RawEvidence) -> list[JobRecord]:
    if evidence.source_type != "careers_jobs":
        raise ValueError("not careers evidence")
    return [JobRecord.model_validate(row) for row in json.loads(evidence.raw_text)]
