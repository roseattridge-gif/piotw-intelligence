from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

StageStatus = Literal["AVAILABLE", "WITHHELD", "NOT_BUILT", "INSUFFICIENT_EVIDENCE"]
Confidence = Literal["HIGH", "MEDIUM", "LOW", "NOT_ASSESSED"]
Direction = Literal["INCREASING", "DECREASING", "STABLE", "MIXED", "UNKNOWN"]


class CompanyIdentity(BaseModel):
    company_id: str
    display_name: str
    legal_name: str | None = None
    ticker: str | None = None
    geography: str | None = None
    activity: str | None = None


class EvidenceReference(BaseModel):
    evidence_id: str
    source_id: str
    title: str
    source_family: str
    source_url: str | None
    source_hash: str
    publication_date: str
    information_available_at: datetime
    entity_scope: str
    evidence_span: str
    collector_or_parser_version: str


class CoverageSummary(BaseModel):
    status: Literal["HIGH", "MEDIUM", "LOW", "INSUFFICIENT"]
    source_families_present: list[str]
    source_families_missing: list[str]
    evidence_count: int = Field(ge=0)
    provenance_complete: bool
    caveats: list[str] = Field(default_factory=list)


class OperationalCondition(BaseModel):
    condition_id: str
    title: str
    statement: str
    dimension: str
    direction: Direction
    materiality: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    evidence_confidence: Confidence
    state: str | None = None
    change: str | None = None
    evidence_ids: list[str] = Field(min_length=1)
    caveats: list[str] = Field(default_factory=list)


class ConditionQualificationView(BaseModel):
    qualification_id: str
    candidate_type: str
    status: Literal["QUALIFIED", "INSUFFICIENT_EVIDENCE", "WITHHELD"]
    dimension: str
    observation_ids: list[str]
    evidence_ids: list[str]
    what_observed: str
    why_it_might_matter: str
    evidence_strength: str
    failed_tests: list[str]
    missing_information: list[str]
    what_would_change_view: str
    policy_version: str
    scientifically_validated: Literal[False] = False


class Comparison(BaseModel):
    comparison_id: str
    condition_id: str
    status: StageStatus
    basis: Literal["PEER", "HISTORY", "PEER_AND_HISTORY"]
    metric: str
    target_value: float | None = None
    comparator_value: float | None = None
    gap: float | None = None
    unit: str | None = None
    percentile: float | None = Field(default=None, ge=0, le=100)
    sample_size: int | None = Field(default=None, ge=1)
    peer_set_or_history: str | None = None
    method: str | None = None
    confidence: Confidence = "NOT_ASSESSED"
    evidence_ids: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    withheld_reason: str | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> Comparison:
        if self.status == "AVAILABLE":
            required = (self.target_value, self.comparator_value, self.unit, self.sample_size, self.method)
            if any(value is None for value in required) or not self.evidence_ids:
                raise ValueError("available comparison requires values, method, sample and evidence")
        elif any(value is not None for value in (self.target_value, self.comparator_value, self.gap, self.percentile)):
            raise ValueError("unavailable comparison cannot expose numerical results")
        if self.status != "AVAILABLE" and not self.withheld_reason:
            raise ValueError("unavailable comparison requires withheld_reason")
        return self


class PredictiveHypothesis(BaseModel):
    prediction_id: str
    status: StageStatus
    target_event: str | None = None
    horizon: str | None = None
    probability: float | None = Field(default=None, ge=0, le=1)
    confidence: Confidence = "NOT_ASSESSED"
    model_version: str | None = None
    historical_pattern: str | None = None
    supporting_condition_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    withheld_reason: str | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> PredictiveHypothesis:
        if self.status == "AVAILABLE":
            required = (self.target_event, self.horizon, self.probability, self.model_version)
            if any(value is None for value in required) or not self.supporting_condition_ids:
                raise ValueError("available prediction requires target, horizon, probability, model and conditions")
        elif self.probability is not None:
            raise ValueError("unavailable prediction cannot expose a probability")
        if self.status != "AVAILABLE" and not self.withheld_reason:
            raise ValueError("unavailable prediction requires withheld_reason")
        return self


class Intervention(BaseModel):
    intervention_id: str
    status: StageStatus
    title: str | None = None
    mechanism: str | None = None
    investigation_steps: list[str] = Field(default_factory=list)
    supporting_condition_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_strength: Confidence = "NOT_ASSESSED"
    falsifiers: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    withheld_reason: str | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> Intervention:
        if self.status == "AVAILABLE":
            if not self.title or not self.mechanism or not self.supporting_condition_ids or not self.evidence_ids:
                raise ValueError("available intervention requires a mechanism, conditions and evidence")
        elif self.title or self.mechanism:
            raise ValueError("unavailable intervention cannot contain a recommendation")
        if self.status != "AVAILABLE" and not self.withheld_reason:
            raise ValueError("unavailable intervention requires withheld_reason")
        return self


class FinancialAssumption(BaseModel):
    assumption_id: str
    statement: str
    value: float
    unit: str
    basis: str
    evidence_ids: list[str] = Field(default_factory=list)


class FinancialImpact(BaseModel):
    impact_id: str
    intervention_id: str
    status: StageStatus
    mechanism: str | None = None
    measure: str | None = None
    low: float | None = None
    base: float | None = None
    high: float | None = None
    currency: str | None = None
    unit: str | None = None
    period: str | None = None
    incremental: bool | None = None
    assumptions: list[FinancialAssumption] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    withheld_reason: str | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> FinancialImpact:
        values = (self.low, self.base, self.high)
        if self.status == "AVAILABLE":
            required = (self.mechanism, self.measure, self.currency, self.unit, self.incremental)
            if any(value is None for value in required) or any(value is None for value in values):
                raise ValueError("available financial impact requires range, unit, mechanism and incrementality")
            if not self.assumptions or not self.evidence_ids:
                raise ValueError("available financial impact requires assumptions and evidence")
            if not self.low <= self.base <= self.high:  # type: ignore[operator]
                raise ValueError("financial range must be ordered low <= base <= high")
        elif any(value is not None for value in values):
            raise ValueError("unavailable financial impact cannot expose a value range")
        if self.status != "AVAILABLE" and not self.withheld_reason:
            raise ValueError("unavailable financial impact requires withheld_reason")
        return self


class CapabilityStatus(BaseModel):
    detect: StageStatus
    compare: StageStatus
    predict: StageStatus
    prescribe: StageStatus
    quantify: StageStatus


class CompanyIntelligenceV01(BaseModel):
    schema_version: Literal["piotw-company-intelligence-v0.1"]
    company: CompanyIdentity
    as_of: datetime
    generated_at: datetime
    methodology_version: str
    scientific_gate_run: Literal[False] = False
    coverage: CoverageSummary
    evidence: list[EvidenceReference]
    condition_qualifications: list[ConditionQualificationView] = Field(default_factory=list)
    conditions: list[OperationalCondition]
    comparisons: list[Comparison]
    predictions: list[PredictiveHypothesis]
    interventions: list[Intervention]
    financial_impacts: list[FinancialImpact]
    capabilities: CapabilityStatus
    missing_capabilities: list[str]
    overall_confidence: Confidence

    @model_validator(mode="after")
    def validate_lineage_and_status(self) -> CompanyIntelligenceV01:
        evidence_ids = {item.evidence_id for item in self.evidence}
        condition_ids = {item.condition_id for item in self.conditions}
        intervention_ids = {item.intervention_id for item in self.interventions}
        references: list[str] = []
        for item in self.condition_qualifications:
            references.extend(item.evidence_ids)
        for item in self.conditions:
            references.extend(item.evidence_ids)
        for item in self.comparisons:
            references.extend(item.evidence_ids)
            if item.condition_id not in condition_ids:
                raise ValueError(f"unknown condition reference: {item.condition_id}")
        for item in self.predictions:
            references.extend(item.evidence_ids)
            if not set(item.supporting_condition_ids).issubset(condition_ids):
                raise ValueError("prediction references unknown condition")
        for item in self.interventions:
            references.extend(item.evidence_ids)
            if not set(item.supporting_condition_ids).issubset(condition_ids):
                raise ValueError("intervention references unknown condition")
        for item in self.financial_impacts:
            references.extend(item.evidence_ids)
            references.extend(ref for assumption in item.assumptions for ref in assumption.evidence_ids)
            if item.intervention_id not in intervention_ids:
                raise ValueError(f"unknown intervention reference: {item.intervention_id}")
        unknown = sorted(set(references) - evidence_ids)
        if unknown:
            raise ValueError(f"unknown evidence references: {', '.join(unknown)}")
        if self.coverage.provenance_complete and any(not item.source_hash for item in self.evidence):
            raise ValueError("provenance_complete requires every evidence record to have a hash")
        return self


def assemble_company_intelligence(payload: dict) -> CompanyIntelligenceV01:
    """Validate and assemble one company object without inventing missing stages."""
    return CompanyIntelligenceV01.model_validate(payload)


def load_company_intelligence(directory: str | Path, company_id: str) -> CompanyIntelligenceV01:
    if not company_id.replace("-", "").isalnum():
        raise KeyError("invalid company identifier")
    path = Path(directory) / f"{company_id}.json"
    if not path.is_file():
        raise KeyError(f"unknown company intelligence object: {company_id}")
    return assemble_company_intelligence(json.loads(path.read_text()))
