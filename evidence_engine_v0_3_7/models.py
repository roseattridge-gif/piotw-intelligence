from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Timing = Literal["CURRENT", "ONGOING", "PLANNED_COMMITTED", "COMPLETED_RECENT", "HISTORICAL", "HYPOTHETICAL", "UNCLEAR"]
Polarity = Literal["INCREASE", "DECREASE", "POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "NOT_APPLICABLE", "UNCLEAR"]
EntityRelationship = Literal["ISSUER", "SUBSIDIARY", "CUSTOMER", "SUPPLIER", "COMPETITOR", "INDUSTRY", "OTHER", "UNCLEAR"]


class EvidenceZone(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zone_id: str
    company_id: str
    source_id: str
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    publication_date: date
    text: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    selection_reasons: list[str]


class SemanticObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["FACT", "NO_FACT", "AMBIGUOUS"]
    subject: str = ""
    action_or_state: str = ""
    object: str = ""
    timing: Timing = "UNCLEAR"
    polarity: Polarity = "UNCLEAR"
    scope: str = ""
    entity_relationship: EntityRelationship = "UNCLEAR"
    exact_evidence_span: str = ""
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    reason_code: str
    model_version: str


class AtomicObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observation_id: str
    company_id: str
    source_id: str
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_span: str
    evidence_start: int | None
    evidence_end: int | None
    subject: str
    action_or_state: str
    object: str
    timing: Timing
    polarity: Polarity
    scope: str
    entity_relationship: EntityRelationship
    publication_date: date
    effective_date: date | None
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    decision: Literal["ACCEPT", "REJECT", "AMBIGUOUS"]
    reason_code: str
    extractor_version: Literal["evidence-engine-v0.3.7-development"]
    model_version: str
    created_at: datetime
