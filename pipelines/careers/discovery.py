from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ProviderMatch:
    provider: str
    identifier: str | None
    public_api: bool
    note: str


def detect_provider(url: str) -> ProviderMatch:
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]
    parts = [part for part in parsed.path.split("/") if part]

    if host in {"boards.greenhouse.io", "job-boards.greenhouse.io"}:
        return ProviderMatch("greenhouse", parts[0] if parts else None, True, "Documented public GET API")
    if host in {"jobs.lever.co", "jobs.eu.lever.co"}:
        return ProviderMatch("lever-eu" if ".eu." in host else "lever", parts[0] if parts else None, True, "Documented public postings API")
    if host == "jobs.ashbyhq.com":
        return ProviderMatch("ashby", parts[0] if parts else None, True, "Documented public job-board API")
    if host == "jobs.smartrecruiters.com":
        return ProviderMatch("smartrecruiters", parts[0] if parts else None, True, "Public Posting API")
    if host.endswith(".recruitee.com"):
        return ProviderMatch("recruitee", host.removesuffix(".recruitee.com"), True, "Public careers-site feed")
    if "myworkdayjobs.com" in host:
        return ProviderMatch("workday", host.split(".")[0], False, "No general documented public job-board API")
    if host == "apply.workable.com" or host.endswith(".workable.com"):
        return ProviderMatch("workable", parts[0] if host == "apply.workable.com" and parts else None, False, "Formal API requires customer credentials")
    if host.endswith(".teamtailor.com"):
        return ProviderMatch("teamtailor", host.removesuffix(".teamtailor.com"), False, "Public API requires an API key")
    if "icims.com" in host:
        return ProviderMatch("icims", None, False, "Use public-page structured data where permitted")
    if "personio." in host:
        return ProviderMatch("personio", host.split(".")[0], False, "Use public XML/page feed only when exposed by the employer")
    if "successfactors" in host:
        return ProviderMatch("successfactors", None, False, "Enterprise API is authenticated")
    if "taleo.net" in host:
        return ProviderMatch("taleo", None, False, "Use public-page structured data where permitted")
    return ProviderMatch("unknown", None, False, "Inspect for schema.org JobPosting data")
