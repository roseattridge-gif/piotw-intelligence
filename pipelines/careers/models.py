from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class AccessMode(str, Enum):
    public_api = "public_api"
    structured_page = "structured_page"
    authenticated_api = "authenticated_api"


class CareerSource(BaseModel):
    company_id: str
    company_name: str
    provider: str
    identifier: str
    careers_url: str | None = None
    access_mode: AccessMode = AccessMode.public_api
    enabled: bool = True


class JobPosting(BaseModel):
    company_id: str
    company_name: str
    provider: str
    external_id: str
    title: str
    location: str | None = None
    department: str | None = None
    employment_type: str | None = None
    workplace_type: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    source_url: str
    apply_url: str | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def identity(self) -> str:
        return f"{self.company_id}:{self.provider}:{self.external_id}"
