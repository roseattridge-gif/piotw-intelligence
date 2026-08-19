"""Typed contracts for PIOTW Index methodology artefacts.

These definitions describe configuration and registries only. They deliberately
contain no scoring implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

DimensionId = Literal[
    "cost_efficiency", "capacity_footprint", "people_organisation",
    "supply_chain_delivery", "technology_execution", "growth_investment",
]
Polarity = Literal["positive", "negative", "neutral/context", "bidirectional"]
FeatureStatus = Literal["candidate", "provisional", "excluded", "needs-validation"]


@dataclass(frozen=True)
class FeatureDefinition:
    feature_id: str
    name: str
    dimension: DimensionId
    description: str
    source_observation_types: tuple[str, ...]
    unit: str
    polarity: Polarity
    health_index_eligible: bool
    pressure_index_eligible: bool
    context_dependent: bool
    recency_required: bool
    persistence_required: bool
    evidence_confidence_required: bool
    minimum_evidence_count: int
    normalisation_method_candidate: str
    missing_data_policy: str
    candidate_financial_linkages: tuple[str, ...]
    candidate_predictive_outcomes: tuple[str, ...]
    status: FeatureStatus
    notes: str = ""


@dataclass(frozen=True)
class DimensionDefinition:
    dimension_id: DimensionId
    name: str
    purpose: str
    operational_phenomena: tuple[str, ...]
    positive_evidence_examples: tuple[str, ...]
    negative_evidence_examples: tuple[str, ...]
    ambiguous_evidence_examples: tuple[str, ...]
    candidate_financial_linkages: tuple[str, ...]
    candidate_predictive_outcomes: tuple[str, ...]
    status: FeatureStatus


@dataclass(frozen=True)
class PeerCohortDefinition:
    cohort_id: str
    filters: tuple[str, ...]
    priority: int
    minimum_n_for_precise_percentile: int
    disclosure_template: str


@dataclass(frozen=True)
class FinancialLinkageDefinition:
    linkage_id: str
    dimensions: tuple[DimensionId, ...]
    features: tuple[str, ...]
    financial_statement_areas: tuple[str, ...]
    hypothesis: str
    confidence: Literal["low", "medium", "high"]
    status: FeatureStatus


@dataclass(frozen=True)
class InterventionClassDefinition:
    intervention_id: str
    name: str
    related_dimensions: tuple[DimensionId, ...]
    related_signals: tuple[str, ...]
    potential_financial_areas: tuple[str, ...]
    evidence_prerequisites: tuple[str, ...]
    limitations: tuple[str, ...]
    status: FeatureStatus


@dataclass(frozen=True)
class IndexMethodologyConfig:
    methodology_id: str
    index_methodology_version: str
    status: Literal["development-only", "validated"]
    dimension_weights: dict[DimensionId, float]
    feature_weighting: str
    normalisation_candidates: tuple[str, ...]
    peer_thresholds: dict[str, int]
    rating_bands: tuple[dict[str, object], ...] = field(default_factory=tuple)

