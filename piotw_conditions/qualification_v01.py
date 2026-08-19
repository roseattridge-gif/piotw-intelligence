from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from pipelines.procurement.find_a_tender import ProcurementRecord

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config/conditions/qualification_policy_v0_1.json"

CandidateFamily = Literal[
    "hiring_expansion",
    "hiring_contraction",
    "workforce_functional_mix_shift",
    "procurement_activity_acceleration",
    "procurement_category_concentration_change",
]
QualificationStatus = Literal["QUALIFIED", "INSUFFICIENT_EVIDENCE", "WITHHELD"]
TestStatus = Literal["PASS", "FAIL", "UNAVAILABLE", "NOT_REQUIRED"]
ContextStatus = Literal["AVAILABLE", "UNAVAILABLE", "INSUFFICIENT_EVIDENCE"]


class FactualObservation(BaseModel):
    observation_id: str
    company_id: str
    entity_scope: str
    source_family: str
    observed_at: datetime
    value: float | None
    unit: str | None
    factual_statement: str
    evidence_ids: list[str] = Field(min_length=1)
    source_record_ids: list[str] = Field(min_length=1)
    collection_health: str
    derivative_group: str | None = None


class HistoryContext(BaseModel):
    snapshot_count: int = Field(ge=0)
    observation_period_days: float | None = Field(default=None, ge=0)
    interval_days: list[float] = Field(default_factory=list)
    interval_consistency: Literal["CONSISTENT", "IRREGULAR", "NOT_ASSESSED"]
    missing_periods: int | None = Field(default=None, ge=0)
    history_depth: Literal["NONE", "SINGLE", "SHALLOW", "SUFFICIENT_FOR_POLICY"]


class DenominatorContext(BaseModel):
    available: bool
    value: float | None = None
    unit: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    quality: Literal["HIGH", "MEDIUM", "LOW", "UNAVAILABLE"]


class MagnitudeContext(BaseModel):
    absolute_change: float | None = None
    relative_change: float | None = None
    unit: str | None = None


class PersistenceContext(BaseModel):
    status: Literal["ONE_OFF", "PERSISTENT", "ACCELERATING", "REVERSED", "STABLE", "NOT_ASSESSED"]
    consistent_intervals: int = Field(ge=0)
    total_intervals: int = Field(ge=0)


class CorroborationContext(BaseModel):
    status: Literal["INDEPENDENT", "SAME_SOURCE_ONLY", "REPEATED_WITHIN_SOURCE",
                    "MULTIPLE_OBSERVATIONS_ONE_FAMILY", "DUPLICATE_ONLY", "CONTRADICTORY", "NONE"]
    independent_source_families: list[str]
    related_observation_count: int = Field(ge=0)
    duplicate_observation_count: int = Field(ge=0)
    supporting_observation_ids: list[str] = Field(default_factory=list)
    contradicting_observation_ids: list[str] = Field(default_factory=list)
    duplicate_derivative_groups: list[str] = Field(default_factory=list)


class DataQualityContext(BaseModel):
    status: Literal["GOOD", "DEGRADED", "FAILED", "UNKNOWN"]
    source_health: list[str]
    stale: bool
    coverage_limitations: list[str]


class QualificationTest(BaseModel):
    test_id: str
    status: TestStatus
    required: bool
    observed: str
    requirement: str
    explanation: str


class ConditionCandidate(BaseModel):
    candidate_id: str
    company_id: str
    entity_scope: str
    analysis_cutoff: datetime
    candidate_type: CandidateFamily
    dimensions: list[str] = Field(min_length=1)
    observation_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    evidence_families: list[str] = Field(min_length=1)
    factual_summary: str
    proposed_mechanism: str | None
    history: HistoryContext
    denominator: DenominatorContext
    magnitude: MagnitudeContext
    persistence: PersistenceContext
    corroboration: CorroborationContext
    data_quality: DataQualityContext
    historical_context_status: ContextStatus
    peer_context_status: ContextStatus = "UNAVAILABLE"
    entity_scope_consistent: bool
    contradiction_present: bool = False
    factual_features: dict[str, object] = Field(default_factory=dict)
    adapter_version: str


class QualificationResult(BaseModel):
    schema_version: Literal["piotw-operational-condition-qualification-v0.1"]
    qualification_id: str
    policy_version: str
    scientifically_validated: Literal[False] = False
    company_id: str
    entity_scope: str
    analysis_cutoff: datetime
    condition_candidate_type: CandidateFamily
    supporting_observation_ids: list[str]
    supporting_evidence_ids: list[str]
    dimensions: list[str]
    evidence_families: list[str]
    history: HistoryContext
    denominator: DenominatorContext
    magnitude: MagnitudeContext
    persistence: PersistenceContext
    corroboration: CorroborationContext
    data_quality: DataQualityContext
    entity_scope_valid: bool
    historical_context_status: ContextStatus
    peer_context_status: ContextStatus
    materiality_status: Literal["SUPPORTED_BY_DEVELOPMENT_POLICY", "UNSUPPORTED", "NOT_ASSESSED"]
    operational_mechanism_status: Literal["SUPPORTED", "UNSUPPORTED", "AMBIGUOUS"]
    qualification_status: QualificationStatus
    direction: Literal["INCREASING", "DECREASING", "STABLE", "MIXED", "UNKNOWN"]
    materiality: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    confidence: Literal["HIGH", "MEDIUM", "LOW", "NOT_ASSESSED"]
    tests: list[QualificationTest]
    failed_tests: list[str]
    missing_information: list[str]
    observed_explanation: str
    why_it_might_matter: str
    evidence_strength_explanation: str
    what_is_unknown: str
    what_would_change_view: str
    human_readable_explanation: str

    @model_validator(mode="after")
    def fail_closed(self) -> QualificationResult:
        if self.qualification_status == "QUALIFIED":
            if self.failed_tests or self.direction == "UNKNOWN" or self.materiality == "UNKNOWN":
                raise ValueError("qualified condition requires no failed tests, direction and materiality")
        elif self.direction != "UNKNOWN" or self.materiality != "UNKNOWN":
            raise ValueError("unqualified candidate cannot expose condition direction or materiality")
        return self

    def canonical_condition(self) -> dict[str, object] | None:
        if self.qualification_status != "QUALIFIED":
            return None
        title = self.condition_candidate_type.replace("_", " ").title()
        return {
            "condition_id": f"condition-{self.qualification_id}",
            "title": title,
            "statement": self.human_readable_explanation,
            "dimension": self.dimensions[0],
            "direction": self.direction,
            "materiality": self.materiality,
            "evidence_confidence": self.confidence,
            "state": self.observed_explanation,
            "change": self.evidence_strength_explanation,
            "evidence_ids": self.supporting_evidence_ids,
            "caveats": [self.what_is_unknown, "Development qualification policy; not scientifically validated."],
        }


class FeatureAdapterResult(BaseModel):
    observations: list[FactualObservation]
    candidates: list[ConditionCandidate]
    unsupported_features: list[str] = Field(default_factory=list)
    factual_features: dict[str, object] = Field(default_factory=dict)


def assess_corroboration(observations: list[FactualObservation], *,
                         contradicting_observation_ids: list[str] | None = None) -> CorroborationContext:
    """Describe evidence relationships without treating raw counts as independent support."""
    contradicting = set(contradicting_observation_ids or [])
    groups: dict[str, list[str]] = defaultdict(list)
    families = sorted({item.source_family for item in observations})
    for item in observations:
        groups[item.derivative_group or item.observation_id].append(item.observation_id)
    duplicate_groups = sorted(key for key, values in groups.items() if len(values) > 1)
    duplicates = sum(len(groups[key]) - 1 for key in duplicate_groups)
    supporting = [item.observation_id for item in observations if item.observation_id not in contradicting]
    if contradicting:
        status = "CONTRADICTORY"
    elif observations and duplicates == len(observations) - 1:
        status = "DUPLICATE_ONLY"
    elif len(families) > 1:
        status = "INDEPENDENT"
    elif len(observations) > 1:
        status = "MULTIPLE_OBSERVATIONS_ONE_FAMILY"
    elif observations:
        status = "REPEATED_WITHIN_SOURCE"
    else:
        status = "NONE"
    return CorroborationContext(status=status, independent_source_families=families,
        related_observation_count=len(observations), duplicate_observation_count=duplicates,
        supporting_observation_ids=supporting, contradicting_observation_ids=sorted(contradicting),
        duplicate_derivative_groups=duplicate_groups)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _id(prefix: str, payload: object) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}-{hashlib.sha256(material.encode()).hexdigest()[:16]}"


def _history(times: list[datetime], minimum: int) -> HistoryContext:
    ordered = sorted(_utc(value) for value in times)
    intervals = [(right - left).total_seconds() / 86400 for left, right in pairwise(ordered)]
    consistent = "NOT_ASSESSED"
    if len(intervals) >= 2:
        mean = sum(intervals) / len(intervals)
        consistent = "CONSISTENT" if mean and max(abs(item - mean) for item in intervals) / mean <= 0.25 else "IRREGULAR"
    depth = "NONE" if not ordered else "SINGLE" if len(ordered) == 1 else "SUFFICIENT_FOR_POLICY" if len(ordered) >= minimum else "SHALLOW"
    return HistoryContext(snapshot_count=len(ordered),
        observation_period_days=(ordered[-1] - ordered[0]).total_seconds() / 86400 if len(ordered) > 1 else None,
        interval_days=intervals, interval_consistency=consistent, missing_periods=None, history_depth=depth)


def _persistence(values: list[float]) -> tuple[PersistenceContext, bool]:
    changes = [right - left for left, right in pairwise(values)]
    nonzero = [1 if item > 0 else -1 for item in changes if item]
    contradiction = len(set(nonzero)) > 1
    if not changes:
        status = "NOT_ASSESSED"
    elif all(item == 0 for item in changes):
        status = "STABLE"
    elif contradiction:
        status = "REVERSED"
    elif len(nonzero) >= 2:
        magnitudes = [abs(item) for item in changes if item]
        status = "ACCELERATING" if len(magnitudes) >= 2 and all(b > a for a, b in pairwise(magnitudes)) else "PERSISTENT"
    else:
        status = "ONE_OFF"
    consistent = len(nonzero) if nonzero and not contradiction else 0
    return PersistenceContext(status=status, consistent_intervals=consistent, total_intervals=len(changes)), contradiction


class CareersConditionAdapter:
    adapter_version = "careers-condition-feature-adapter-v0.2"

    def adapt(self, *, company_id: str, entity_scope: str, analysis_cutoff: datetime,
              snapshots: list[dict[str, object]]) -> FeatureAdapterResult:
        eligible = sorted(
            [row for row in snapshots if bool(row.get("included")) and
             _utc(row["observed_at"]) <= _utc(analysis_cutoff)],
            key=lambda row: str(row["observed_at"]),
        )
        observations = [FactualObservation(
            observation_id=f"obs-{row['source_record_id']}", company_id=company_id,
            entity_scope=str(row["entity_scope"]), source_family="careers_ats",
            observed_at=_utc(row["observed_at"]), value=float(row["value"]), unit="open_postings",
            factual_statement=f"The approved careers collector observed {int(row['value'])} open postings.",
            evidence_ids=[str(row["evidence_id"])], source_record_ids=[str(row["source_record_id"])],
            collection_health=str(row["health"]), derivative_group=str(row["source_record_id"]),
        ) for row in eligible]
        if len(observations) < 2:
            return FeatureAdapterResult(observations=observations, candidates=[],
                unsupported_features=["longitudinal vacancy movement requires at least two healthy snapshots"])
        values = [float(item.value) for item in observations if item.value is not None]
        factual_features = self._longitudinal_features(eligible, values)
        absolute = values[-1] - values[0]
        if absolute == 0:
            return FeatureAdapterResult(observations=observations, candidates=[],
                unsupported_features=["no hiring expansion or contraction candidate is supported by unchanged counts"],
                factual_features=factual_features)
        family: CandidateFamily = "hiring_expansion" if absolute > 0 else "hiring_contraction"
        denominator = values[0] if values[0] > 0 else None
        persistence, contradiction = _persistence(values)
        evidence_ids = [value for item in observations for value in item.evidence_ids]
        scopes = {item.entity_scope for item in observations}
        health = sorted({item.collection_health for item in observations})
        history = _history([item.observed_at for item in observations], 4)
        pct = absolute / denominator if denominator else None
        relative_text = f"{pct:+.2%}" if pct is not None else "relative change unavailable"
        candidate = ConditionCandidate(
            candidate_id=_id("candidate", [company_id, family, evidence_ids, analysis_cutoff]),
            company_id=company_id, entity_scope=entity_scope, analysis_cutoff=_utc(analysis_cutoff),
            candidate_type=family, dimensions=["Workforce & Capability"],
            observation_ids=[item.observation_id for item in observations], evidence_ids=evidence_ids,
            evidence_families=["careers_ats"],
            factual_summary=f"Open postings moved from {int(values[0])} to {int(values[-1])} across {len(values)} stored snapshots ({absolute:+.0f}; {relative_text}).",
            proposed_mechanism="Published open-role inventory expansion" if absolute > 0 else "Published open-role inventory contraction",
            history=history,
            denominator=DenominatorContext(available=denominator is not None, value=denominator,
                unit="open_postings", evidence_ids=observations[0].evidence_ids if denominator else [],
                quality="HIGH" if denominator else "UNAVAILABLE"),
            magnitude=MagnitudeContext(absolute_change=absolute, relative_change=pct, unit="open_postings"),
            persistence=persistence,
            corroboration=assess_corroboration(observations),
            data_quality=DataQualityContext(status="GOOD" if health == ["healthy"] else "DEGRADED",
                source_health=health, stale=False,
                coverage_limitations=["Careers postings are one source family and do not prove workforce headcount or hiring intent."]),
            historical_context_status="AVAILABLE" if history.history_depth == "SUFFICIENT_FOR_POLICY" else "INSUFFICIENT_EVIDENCE",
            peer_context_status="UNAVAILABLE", entity_scope_consistent=scopes == {entity_scope},
            contradiction_present=contradiction, factual_features=factual_features,
            adapter_version=self.adapter_version,
        )
        return FeatureAdapterResult(observations=observations, candidates=[candidate],
            unsupported_features=self._unsupported_mix_features(eligible), factual_features=factual_features)

    @staticmethod
    def _unsupported_mix_features(snapshots: list[dict[str, object]]) -> list[str]:
        available = [row for row in snapshots if row.get("derived_origin") != "LEGACY_SUMMARY_ONLY"]
        if len(available) < 2:
            return ["mix trajectories require at least two snapshots with preserved role-level evidence"]
        return []

    @staticmethod
    def _longitudinal_features(snapshots: list[dict[str, object]], values: list[float]) -> dict[str, object]:
        def trajectory(field: str) -> dict[str, list[int | None]]:
            keys = sorted({key for row in snapshots for key in (row.get(field) or {})})
            return {key: [((row.get(field) or {}).get(key) if row.get("derived_origin") != "LEGACY_SUMMARY_ONLY" else None)
                          for row in snapshots] for key in keys}
        changes = [right - left for left, right in pairwise(values)]
        return {
            "total_role_trajectory": values,
            "interval_absolute_changes": changes,
            "overall_absolute_change": values[-1] - values[0],
            "overall_relative_change": (values[-1] - values[0]) / values[0] if values and values[0] else None,
            "multi_period_direction": "MIXED" if changes and len({item > 0 for item in changes if item}) > 1
                                      else "INCREASING" if changes and any(item > 0 for item in changes)
                                      else "DECREASING" if changes and any(item < 0 for item in changes) else "STABLE",
            "function_mix_trajectory": trajectory("function_mix"),
            "seniority_mix_trajectory": trajectory("seniority_mix"),
            "geography_mix_trajectory": trajectory("geography_mix"),
            "technology_mix_trajectory": trajectory("technology_mix"),
            "lifecycle": {field: [row.get(field) for row in snapshots] for field in
                ("new_count", "persistent_count", "absent_once_count", "confirmed_closed_count", "reopened_count")},
            "derived_origins": [row.get("derived_origin") for row in snapshots],
            "missing_period_flags": [row.get("derived_origin") == "LEGACY_SUMMARY_ONLY" for row in snapshots],
        }


class ProcurementConditionAdapter:
    """Fixture-ready second adapter; runtime use requires approved supplier entity resolution."""

    adapter_version = "procurement-condition-feature-adapter-v0.1"

    def adapt(self, *, company_id: str, entity_scope: str, analysis_cutoff: datetime,
              records: list[ProcurementRecord], approved_entity: bool) -> FeatureAdapterResult:
        if not approved_entity:
            return FeatureAdapterResult(observations=[], candidates=[],
                unsupported_features=["approved supplier-to-company entity resolution is required"])
        cutoff = _utc(analysis_cutoff)
        eligible = [record for record in records if record.publication_date and
                    _utc(datetime.fromisoformat(record.publication_date)) <= cutoff]
        grouped: dict[str, list[ProcurementRecord]] = defaultdict(list)
        for record in eligible:
            grouped[record.publication_date[:7]].append(record)  # type: ignore[index]
        observations = []
        for period, period_records in sorted(grouped.items()):
            evidence_ids = [f"ev-{item.source_record_id}" for item in period_records]
            observations.append(FactualObservation(
                observation_id=_id("obs-procurement", [company_id, period, evidence_ids]),
                company_id=company_id, entity_scope=entity_scope, source_family="contracts_procurement",
                observed_at=datetime.fromisoformat(f"{period}-01T00:00:00+00:00"), value=float(len(period_records)),
                unit="published_award_records", factual_statement=f"{len(period_records)} resolved procurement award record(s) were published in {period}.",
                evidence_ids=evidence_ids, source_record_ids=[item.source_record_id for item in period_records],
                collection_health="healthy", derivative_group=f"procurement-{period}"))
        if len(observations) < 2:
            return FeatureAdapterResult(observations=observations, candidates=[],
                unsupported_features=["procurement activity comparison requires at least two periods"])
        values = [float(item.value) for item in observations if item.value is not None]
        absolute = values[-1] - values[0]
        if absolute <= 0:
            return FeatureAdapterResult(observations=observations, candidates=[],
                unsupported_features=["v0.1 procurement adapter only proposes activity acceleration"])
        denominator = values[0] if values[0] else None
        persistence, contradiction = _persistence(values)
        evidence_ids = [value for item in observations for value in item.evidence_ids]
        candidate = ConditionCandidate(
            candidate_id=_id("candidate", [company_id, "procurement_activity_acceleration", evidence_ids]),
            company_id=company_id, entity_scope=entity_scope, analysis_cutoff=cutoff,
            candidate_type="procurement_activity_acceleration", dimensions=["Demand & Growth", "Change & Execution"],
            observation_ids=[item.observation_id for item in observations], evidence_ids=evidence_ids,
            evidence_families=["contracts_procurement"],
            factual_summary=f"Resolved published award records moved from {int(values[0])} to {int(values[-1])} across {len(values)} periods.",
            proposed_mechanism="Resolved public procurement award activity acceleration",
            history=_history([item.observed_at for item in observations], 4),
            denominator=DenominatorContext(available=denominator is not None, value=denominator,
                unit="published_award_records", evidence_ids=observations[0].evidence_ids if denominator else [],
                quality="MEDIUM" if denominator else "UNAVAILABLE"),
            magnitude=MagnitudeContext(absolute_change=absolute,
                relative_change=absolute / denominator if denominator else None, unit="published_award_records"),
            persistence=persistence,
            corroboration=assess_corroboration(observations),
            data_quality=DataQualityContext(status="GOOD", source_health=["healthy"], stale=False,
                coverage_limitations=["Published public awards do not represent all company contracts or revenue."]),
            historical_context_status="AVAILABLE" if len(observations) >= 4 else "INSUFFICIENT_EVIDENCE",
            peer_context_status="UNAVAILABLE", entity_scope_consistent=True,
            contradiction_present=contradiction, adapter_version=self.adapter_version)
        return FeatureAdapterResult(observations=observations, candidates=[candidate])


class ConditionQualificationEngine:
    engine_version = "piotw-operational-condition-qualification-engine-v0.1"

    def __init__(self, policy_path: str | Path = DEFAULT_POLICY) -> None:
        self.policy_path = Path(policy_path)
        self.policy = json.loads(self.policy_path.read_text())
        self.policy_hash = hashlib.sha256(self.policy_path.read_bytes()).hexdigest()

    def qualify(self, candidate: ConditionCandidate, *, observations: list[FactualObservation],
                valid_evidence_ids: set[str]) -> QualificationResult:
        policy = self.policy["families"].get(candidate.candidate_type)
        if policy is None:
            return self._withheld(candidate, "No versioned qualification policy exists for this candidate family.")
        by_id = {item.observation_id: item for item in observations}
        unknown_obs = sorted(set(candidate.observation_ids) - set(by_id))
        unknown_evidence = sorted(set(candidate.evidence_ids) - valid_evidence_ids)
        duplicate_evidence = len(candidate.evidence_ids) - len(set(candidate.evidence_ids))
        tests = [
            self._test("references", not unknown_obs and not unknown_evidence, True,
                f"unknown observations={unknown_obs}; unknown evidence={unknown_evidence}", "all references resolve",
                "Every candidate reference must resolve to a supplied factual observation and canonical evidence record."),
            self._test("duplicate_evidence", duplicate_evidence == 0 and
                candidate.corroboration.status != "DUPLICATE_ONLY", True,
                f"{duplicate_evidence} duplicate evidence reference(s); corroboration={candidate.corroboration.status}",
                "no duplicate-only corroboration",
                "Duplicate or derivative evidence cannot be counted as independent support."),
            self._test("entity_scope", candidate.entity_scope_consistent, True,
                str(candidate.entity_scope_consistent), "one legitimate entity scope",
                "Supporting observations must apply to the same operational entity scope."),
            self._test("source_health", candidate.data_quality.status == "GOOD", bool(policy["healthy_source_required"]),
                candidate.data_quality.status, "GOOD", "Failed or degraded collection cannot establish an operational condition."),
            self._test("history_depth", candidate.history.snapshot_count >= int(policy["minimum_snapshots"]), True,
                f"{candidate.history.snapshot_count} snapshots", f">={policy['minimum_snapshots']} snapshots",
                "The source-specific policy requires enough longitudinal history to distinguish a movement from one interval."),
            self._test("denominator", candidate.denominator.available, bool(policy["denominator_required"]),
                str(candidate.denominator.value), "available denominator", "Quantitative materiality requires an evidenced scale denominator."),
            self._test("magnitude", candidate.magnitude.relative_change is not None and
                abs(candidate.magnitude.relative_change) >= float(policy["minimum_relative_change"]), True,
                str(candidate.magnitude.relative_change), f">={policy['minimum_relative_change']} absolute relative change",
                "The development policy requires a minimum relative movement; this is not a scientifically validated threshold."),
            self._test("persistence", candidate.persistence.consistent_intervals >= int(policy["minimum_consistent_intervals"]), True,
                f"{candidate.persistence.consistent_intervals} consistent intervals",
                f">={policy['minimum_consistent_intervals']} consistent intervals",
                "A one-period movement is not a persistent operational condition."),
            self._test("contradiction", not candidate.contradiction_present, True,
                str(candidate.contradiction_present), "no contradictory direction",
                "Reversing observations cannot support a single directional condition."),
            self._test("operational_mechanism", bool(candidate.proposed_mechanism), True,
                candidate.proposed_mechanism or "missing", "traceable factual mechanism",
                "The condition must describe an operational state without narrative invention."),
            self._test("peer_context", False, False, "UNAVAILABLE", "future strengthening evidence",
                "The generic peer engine is not built and peer-relative materiality is not inferred."),
        ]
        failed = [item.test_id for item in tests if item.required and item.status != "PASS"]
        status: QualificationStatus = "QUALIFIED" if not failed else "INSUFFICIENT_EVIDENCE"
        missing = [item.explanation for item in tests if item.status in {"FAIL", "UNAVAILABLE"}]
        if candidate.corroboration.status != "INDEPENDENT":
            missing.append("No independent source-family corroboration is available; same-source observations are not treated as independent.")
        direction = "UNKNOWN"
        materiality = "UNKNOWN"
        confidence = "NOT_ASSESSED"
        if status == "QUALIFIED":
            direction = "INCREASING" if (candidate.magnitude.relative_change or 0) > 0 else "DECREASING"
            materiality = policy["materiality_when_qualified"]
            confidence = "MEDIUM" if candidate.corroboration.status == "INDEPENDENT" else "LOW"
        observed = candidate.factual_summary
        why = (f"If the movement is persistent and material, it could support the operational state: {candidate.proposed_mechanism.lower()}."
               if candidate.proposed_mechanism else "No factual operational mechanism is supportable.")
        strength = "; ".join(f"{item.test_id}={item.status}" for item in tests)
        unknown = " ".join(missing) if missing else "Peer context remains unavailable and the policy remains development-only."
        change_view = "Add the missing history, denominator, healthy collection, consistent scope, persistence or independent corroboration identified by the failed tests."
        explanation = (f"{status}: {observed} " +
            (f"The evidence supports {candidate.proposed_mechanism.lower()} under the development policy."
             if status == "QUALIFIED" and candidate.proposed_mechanism else
             f"{why} Failed required tests: {', '.join(failed)}."))
        return QualificationResult(
            schema_version="piotw-operational-condition-qualification-v0.1",
            qualification_id=_id("qualification", [candidate.candidate_id, self.policy_hash]),
            policy_version=self.policy["policy_version"], scientifically_validated=False,
            company_id=candidate.company_id, entity_scope=candidate.entity_scope,
            analysis_cutoff=candidate.analysis_cutoff, condition_candidate_type=candidate.candidate_type,
            supporting_observation_ids=candidate.observation_ids, supporting_evidence_ids=candidate.evidence_ids,
            dimensions=candidate.dimensions, evidence_families=candidate.evidence_families,
            history=candidate.history, denominator=candidate.denominator, magnitude=candidate.magnitude,
            persistence=candidate.persistence, corroboration=candidate.corroboration,
            data_quality=candidate.data_quality, entity_scope_valid=candidate.entity_scope_consistent,
            historical_context_status=candidate.historical_context_status,
            peer_context_status=candidate.peer_context_status,
            materiality_status="SUPPORTED_BY_DEVELOPMENT_POLICY" if status == "QUALIFIED" else "UNSUPPORTED",
            operational_mechanism_status="SUPPORTED" if candidate.proposed_mechanism else "UNSUPPORTED",
            qualification_status=status, direction=direction, materiality=materiality, confidence=confidence,
            tests=tests, failed_tests=failed, missing_information=missing,
            observed_explanation=observed, why_it_might_matter=why,
            evidence_strength_explanation=strength, what_is_unknown=unknown,
            what_would_change_view=change_view, human_readable_explanation=explanation)

    @staticmethod
    def _test(test_id: str, passed: bool, required: bool, observed: str, requirement: str,
              explanation: str) -> QualificationTest:
        status: TestStatus = "PASS" if passed else "FAIL" if required else "UNAVAILABLE"
        return QualificationTest(test_id=test_id, status=status, required=required,
            observed=observed, requirement=requirement, explanation=explanation)

    def _withheld(self, candidate: ConditionCandidate, reason: str) -> QualificationResult:
        test = QualificationTest(test_id="policy_available", status="FAIL", required=True,
            observed="missing", requirement="versioned policy", explanation=reason)
        return QualificationResult(
            schema_version="piotw-operational-condition-qualification-v0.1",
            qualification_id=_id("qualification", [candidate.candidate_id, "withheld"]),
            policy_version=self.policy["policy_version"], scientifically_validated=False,
            company_id=candidate.company_id, entity_scope=candidate.entity_scope,
            analysis_cutoff=candidate.analysis_cutoff, condition_candidate_type=candidate.candidate_type,
            supporting_observation_ids=candidate.observation_ids, supporting_evidence_ids=candidate.evidence_ids,
            dimensions=candidate.dimensions, evidence_families=candidate.evidence_families,
            history=candidate.history, denominator=candidate.denominator, magnitude=candidate.magnitude,
            persistence=candidate.persistence, corroboration=candidate.corroboration,
            data_quality=candidate.data_quality, entity_scope_valid=candidate.entity_scope_consistent,
            historical_context_status=candidate.historical_context_status,
            peer_context_status=candidate.peer_context_status, materiality_status="NOT_ASSESSED",
            operational_mechanism_status="AMBIGUOUS", qualification_status="WITHHELD",
            direction="UNKNOWN", materiality="UNKNOWN", confidence="NOT_ASSESSED",
            tests=[test], failed_tests=[test.test_id], missing_information=[reason],
            observed_explanation=candidate.factual_summary, why_it_might_matter="Withheld.",
            evidence_strength_explanation=reason, what_is_unknown=reason,
            what_would_change_view="Add a reviewed, versioned source-specific policy.",
            human_readable_explanation=f"WITHHELD: {reason}")
