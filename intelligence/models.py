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
