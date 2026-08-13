from __future__ import annotations

from datetime import datetime

from pipelines.careers.adapters import _date, _text
from pipelines.careers.jsonld import extract_job_postings
from pipelines.careers.models import CareerSource, JobPosting
from pipelines.common.pages import RobotsAwarePageClient


def _location(value: object) -> str | None:
    if isinstance(value, list):
        return ", ".join(filter(None, (_location(item) for item in value))) or None
    if not isinstance(value, dict):
        return _text(value)
    address = value.get("address", value)
    if isinstance(address, dict):
        return ", ".join(str(address[key]) for key in
                         ("addressLocality", "addressRegion", "addressCountry") if address.get(key)) or None
    return _text(address)


def collect_structured_page(source: CareerSource,
                            page_client: RobotsAwarePageClient | None = None) -> list[JobPosting]:
    if not source.careers_url:
        raise ValueError("A careers URL is required for structured-page collection")
    snapshot = (page_client or RobotsAwarePageClient()).retrieve(source.careers_url)
    jobs = []
    for index, row in enumerate(extract_job_postings(snapshot.html)):
        identifier = row.get("identifier")
        if isinstance(identifier, dict):
            identifier = identifier.get("value") or identifier.get("name")
        source_url = row.get("url") or source.careers_url
        jobs.append(JobPosting(
            company_id=source.company_id, company_name=source.company_name, provider=source.provider,
            external_id=str(identifier or f"jsonld-{index}-{snapshot.content_hash[:12]}"),
            title=str(row.get("title") or "Untitled vacancy"), location=_location(row.get("jobLocation")),
            employment_type=_text(row.get("employmentType")), description=_text(row.get("description")),
            published_at=_date(row.get("datePosted")), source_url=source_url, apply_url=source_url,
            observed_at=snapshot.observed_at,
        ))
    return jobs
