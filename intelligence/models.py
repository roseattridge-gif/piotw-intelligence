from datetime import date, datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

class Relationship(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    neutral = "neutral"

class Document(BaseModel):
    document_id: UUID
    company_id: UUID
    source_id: UUID
    source_url: str
    title: str
    period_start: date | None = None
    period_end: date | None = None
    published_at: datetime
    available_at: datetime
    retrieved_at: datetime
    content_hash: str
    mime_type: str
    parser_version: str

    @model_validator(mode="after")
    def availability_is_not_retrieval(self):
        if self.available_at > self.retrieved_at:
            raise ValueError("available_at cannot be after retrieved_at")
        return self

class ScoreComponent(BaseModel):
    signal_id: UUID
    strength: float = Field(ge=0, le=1)
    source_reliability: float = Field(ge=0, le=1)
    materiality: float = Field(ge=0, le=1)
    recency: float = Field(ge=0, le=1)
    independence: float = Field(ge=0, le=1)
    relevance: float = Field(ge=-1, le=1)

    @property
    def contribution(self) -> float:
        return round(self.strength * self.source_reliability * self.materiality * self.recency * self.independence * self.relevance, 12)

class ScoreResult(BaseModel):
    score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    components: list[ScoreComponent]
    model_version: str


class EvidenceObservation(BaseModel):
    """A point-in-time, model-ready observation with a complete audit trail."""

    observation_id: str
    company_id: str
    family: str
    feature: str
    event_date: date
    available_at: datetime
    source_type: str
    source_url: str
    source_name: str
    source_is_company_controlled: bool = False
    event_cluster_id: str
    direction_pressure: float = Field(ge=-1, le=1)
    direction_expansion: float = Field(ge=-1, le=1)
    strength: float = Field(ge=0, le=1)
    source_reliability: float = Field(ge=0, le=1)
    measurement_quality: float = Field(ge=0, le=1)
    materiality: float = Field(ge=0, le=1)
    independence: float = Field(ge=0, le=1)
    relevance_pressure: float = Field(default=1, ge=0, le=1)
    relevance_expansion: float = Field(default=1, ge=0, le=1)
    raw_value: float | str | None = None
    unit: str | None = None
    explanation: str
    extraction_method: str
    validation_status: str = "unreviewed"


class SourceCoverage(BaseModel):
    company_id: str
    family: str
    as_of_date: date
    coverage: float = Field(ge=0, le=1)
    note: str


class EvidenceContribution(BaseModel):
    observation_id: str
    event_cluster_id: str
    family: str
    feature: str
    contribution: float
    explanation: str
    source_url: str


class ModelPrediction(BaseModel):
    company_id: str
    model: str
    horizon_months: int
    as_of_date: date
    probability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    prior_probability: float = Field(ge=0, le=1)
    evidence_sum: float
    coverage: float = Field(ge=0, le=1)
    contributions: list[EvidenceContribution]
    missing_families: list[str]
    model_version: str
