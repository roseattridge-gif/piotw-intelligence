from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime
from html import unescape
from urllib.parse import quote

from pipelines.careers.models import CareerSource, JobPosting
from pipelines.common.http import PublicHttpClient


def _text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(str(value)))).strip()
    return cleaned or None


def _date(value: object) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


class CareersAdapter(ABC):
    provider: str

    def __init__(self, client: PublicHttpClient | None = None):
        self.client = client or PublicHttpClient()

    @abstractmethod
    def collect(self, source: CareerSource) -> list[JobPosting]: ...


class GreenhouseAdapter(CareersAdapter):
    provider = "greenhouse"

    def collect(self, source: CareerSource) -> list[JobPosting]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{quote(source.identifier)}/jobs?content=true"
        payload = self.client.get_json(url)
        return [JobPosting(company_id=source.company_id, company_name=source.company_name,
            provider=self.provider, external_id=str(row["id"]), title=row["title"],
            location=(row.get("location") or {}).get("name"),
            department=", ".join(x["name"] for x in row.get("departments", [])) or None,
            description=_text(row.get("content")), published_at=_date(row.get("updated_at")),
            source_url=row["absolute_url"], apply_url=row["absolute_url"])
            for row in payload.get("jobs", [])]


class LeverAdapter(CareersAdapter):
    provider = "lever"

    def collect(self, source: CareerSource) -> list[JobPosting]:
        eu = source.provider == "lever-eu"
        host = "api.eu.lever.co" if eu else "api.lever.co"
        url = f"https://{host}/v0/postings/{quote(source.identifier)}?mode=json"
        payload = self.client.get_json(url)
        return [JobPosting(company_id=source.company_id, company_name=source.company_name,
            provider=source.provider, external_id=str(row["id"]), title=row["text"],
            location=(row.get("categories") or {}).get("location"),
            department=(row.get("categories") or {}).get("department"),
            employment_type=(row.get("categories") or {}).get("commitment"),
            workplace_type=row.get("workplaceType"), description=_text(row.get("descriptionPlain") or row.get("description")),
            source_url=row["hostedUrl"], apply_url=row.get("applyUrl")) for row in payload]


class AshbyAdapter(CareersAdapter):
    provider = "ashby"

    def collect(self, source: CareerSource) -> list[JobPosting]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{quote(source.identifier)}?includeCompensation=true"
        payload = self.client.get_json(url)
        return [JobPosting(company_id=source.company_id, company_name=source.company_name,
            provider=self.provider, external_id=str(row.get("id") or row["jobUrl"].rstrip("/").split("/")[-1]),
            title=row["title"], location=row.get("location"), department=row.get("department"),
            employment_type=row.get("employmentType"), workplace_type=row.get("workplaceType"),
            description=_text(row.get("descriptionPlain") or row.get("descriptionHtml")),
            published_at=_date(row.get("publishedAt")), source_url=row["jobUrl"], apply_url=row.get("applyUrl"))
            for row in payload.get("jobs", [])]


class SmartRecruitersAdapter(CareersAdapter):
    provider = "smartrecruiters"

    def collect(self, source: CareerSource) -> list[JobPosting]:
        url = f"https://api.smartrecruiters.com/v1/companies/{quote(source.identifier)}/postings?limit=100"
        payload = self.client.get_json(url)
        return [JobPosting(company_id=source.company_id, company_name=source.company_name,
            provider=self.provider, external_id=str(row["id"]), title=row["name"],
            location=(row.get("location") or {}).get("fullLocation"),
            department=(row.get("department") or {}).get("label"),
            employment_type=(row.get("typeOfEmployment") or {}).get("label"),
            published_at=_date(row.get("releasedDate")), source_url=row.get("ref") or row.get("jobAd", {}).get("sections", {}).get("companyDescription", {}).get("title", ""),
            apply_url=row.get("ref")) for row in payload.get("content", [])]


class RecruiteeAdapter(CareersAdapter):
    provider = "recruitee"

    def collect(self, source: CareerSource) -> list[JobPosting]:
        url = f"https://{quote(source.identifier)}.recruitee.com/api/offers/"
        payload = self.client.get_json(url)
        return [JobPosting(company_id=source.company_id, company_name=source.company_name,
            provider=self.provider, external_id=str(row["id"]), title=row["title"],
            location=row.get("location"), department=row.get("department"),
            employment_type=row.get("employment_type"), description=_text(row.get("description")),
            published_at=_date(row.get("published_at")), source_url=row.get("careers_url") or row.get("url"),
            apply_url=row.get("careers_apply_url")) for row in payload.get("offers", [])]


ADAPTERS = {
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "lever-eu": LeverAdapter,
    "ashby": AshbyAdapter,
    "smartrecruiters": SmartRecruitersAdapter,
    "recruitee": RecruiteeAdapter,
}


def adapter_for(provider: str, client: PublicHttpClient | None = None) -> CareersAdapter:
    try:
        return ADAPTERS[provider](client)
    except KeyError as exc:
        raise ValueError(f"No documented public API adapter for {provider}") from exc
