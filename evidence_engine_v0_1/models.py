from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class RawEvidence(BaseModel):
    evidence_id: str
    company_id: str
    source_type: str
    source_title: str
    source_url: str
    reporting_period: str
    publication_date: date
    observation_date: date | None = None
    collected_at: datetime
    information_available_at: datetime
    content_hash: str
    raw_text: str
    raw_storage_path: str
    collector_version: str
    mime_type: str = "text/plain"

    @model_validator(mode="after")
    def availability_not_after_collection(self):
        if self.information_available_at > self.collected_at:
            raise ValueError("information_available_at cannot be after collected_at")
        return self


class Observation(BaseModel):
    observation_id: str
    company_id: str
    observation_type: str
    reporting_period: str
    value: float | str | bool | None
    unit: str | None
    currency: str | None = None
    source_evidence_id: str
    evidence_span: str
    page_or_section: str
    publication_date: date
    observation_date: date | None = None
    information_available_at: datetime
    extraction_confidence: float = Field(ge=0, le=1)
    parser_version: str
    extraction_method: Literal["deterministic", "llm_assisted", "human"]
    llm_model: str | None = None
    prompt_version: str | None = None
    extracted_at: datetime
    validation_status: Literal["pending", "accepted", "corrected", "rejected"] = "pending"
    quantified: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def llm_provenance(self):
        if self.extraction_method == "llm_assisted" and not (self.llm_model and self.prompt_version):
            raise ValueError("LLM-assisted observations require model and prompt version")
        if not self.evidence_span.strip():
            raise ValueError("observation requires an exact evidence span")
        return self


class Event(BaseModel):
    event_id: str
    company_id: str
    event_type: str
    taxonomy_group: str
    reporting_period: str
    event_date: date
    information_available_at: datetime
    evidence_span: str
    quantified: bool
    severity: float | None = Field(default=None, ge=0, le=1)
    novelty: Literal["new", "persistent", "unknown"] = "unknown"
    extraction_confidence: float = Field(ge=0, le=1)
    taxonomy_version: str
    source_observation_ids: list[str]


class FeatureDefinition(BaseModel):
    feature_id: str
    name: str
    version: str
    definition: str
    required_observation_types: list[str]
    calculation: str
    unit: str
    missing_data: Literal["null", "zero", "error"] = "null"
    lookback_periods: int = 2
    effective_from: date


class FeatureSnapshot(BaseModel):
    feature_snapshot_id: str
    company_id: str
    feature_id: str
    feature_version: str
    as_of_date: date
    value: float | int | bool | None
    unit: str
    calculation: str
    input_observation_ids: list[str] = Field(default_factory=list)
    input_event_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    quality: float = Field(ge=0, le=1)
    created_at: datetime


class ReviewDecision(BaseModel):
    decision_id: str
    observation_id: str
    decision: Literal["accept", "correct", "reject"]
    reviewer: str
    decided_at: datetime
    corrected_value: float | str | bool | None = None
    corrected_unit: str | None = None
    note: str = ""

    @model_validator(mode="after")
    def correction_has_value(self):
        if self.decision == "correct" and self.corrected_value is None:
            raise ValueError("correction requires corrected_value")
        return self


class JobRecord(BaseModel):
    company_id: str
    posting_id: str
    title: str
    function: str | None = None
    seniority: str | None = None
    location: str | None = None
    source_url: str
    collected_at: datetime
    first_seen: datetime
    last_seen: datetime
    status: Literal["open", "closed"] = "open"

    @property
    def identity(self) -> str:
        return f"{self.company_id}:{self.posting_id}"

