from __future__ import annotations

import hashlib
import itertools
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FEATURES = ROOT / "config/comparison/comparable_features_v0_1.json"
DEFAULT_ESTATE_COHORT = ROOT / "config/comparison/estate_peer_cohort_v0_1.json"


class CohortMember(BaseModel):
    company_id: str
    display_name: str
    entity_scope: str
    included: bool
    exclusion_reason: str | None = None
    raw_value: float | None = None
    denominator: float | None = None
    normalised_value: float | None = None
    evidence_id: str | None = None


class ComparisonResult(BaseModel):
    contract_version: Literal["piotw-comparison-v0.1"] = "piotw-comparison-v0.1"
    comparison_id: str
    company_id: str
    entity_scope: str
    analysis_cutoff: datetime
    qualified_condition_id: str
    feature_id: str
    source_family: str
    comparison_type: Literal["OWN_HISTORY", "PEER_COHORT"]
    comparison_window: str
    feature_definition: str
    feature_unit: str
    directionality: str
    company_value: float | None = None
    raw_value: float | None = None
    denominator: float | None = None
    historical_reference_values: list[float] = Field(default_factory=list)
    peer_values: list[float] = Field(default_factory=list)
    cohort_definition: str | None = None
    cohort_members: list[CohortMember] = Field(default_factory=list)
    coverage: str
    missingness: list[str] = Field(default_factory=list)
    normalisation_method: str
    rank: int | None = None
    percentile: float | None = Field(default=None, ge=0, le=100)
    anomaly_strength: str
    evidence_ids: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    status: Literal["AVAILABLE", "INSUFFICIENT_EVIDENCE", "NOT_COMPARABLE", "WITHHELD"]
    reference_value: float | None = None
    gap: float | None = None
    sample_size: int | None = None
    method: str | None = None

    @model_validator(mode="after")
    def fail_closed(self) -> ComparisonResult:
        if self.status == "AVAILABLE":
            if self.company_value is None or self.reference_value is None or not self.evidence_ids:
                raise ValueError("available comparison requires company/reference values and evidence")
        elif any(value is not None for value in (self.company_value, self.reference_value, self.gap, self.rank, self.percentile)):
            raise ValueError("unavailable comparison cannot expose numerical results")
        return self


class FeatureRegistry:
    def __init__(self, path: str | Path = DEFAULT_FEATURES) -> None:
        self.path = Path(path)
        self.payload = json.loads(self.path.read_text())
        self.features = {item["feature_id"]: item for item in self.payload["features"]}

    def require(self, feature_id: str) -> dict:
        if feature_id not in self.features:
            raise KeyError(f"feature is not comparison-eligible: {feature_id}")
        return self.features[feature_id]


def _id(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class ComparisonEngine:
    version = "piotw-general-comparison-engine-v0.1-development"

    def __init__(self, *, registry: FeatureRegistry | None = None,
                 estate_cohort: str | Path = DEFAULT_ESTATE_COHORT) -> None:
        self.registry = registry or FeatureRegistry()
        self.estate_cohort_path = Path(estate_cohort)
        self.estate_cohort = json.loads(self.estate_cohort_path.read_text())

    @staticmethod
    def _period_rows(records: list[dict], entity_scope: str, cutoff: datetime) -> list[dict]:
        cutoff = cutoff if cutoff.tzinfo else cutoff.replace(tzinfo=UTC)
        rows = []
        for row in records:
            ts = row["publication_or_effective_at"]
            ts = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
            values = row.get("values", row.get("derived_snapshot_features", {})) or {}
            if (row.get("family_id", row.get("source_family")) == "estate_footprint_capacity"
                    and row.get("entity_scope") == entity_scope and ts <= cutoff
                    and values.get("site_count") is not None):
                rows.append({**row, "values": values, "timestamp": ts})
        return sorted(rows, key=lambda row: (row["values"].get("period", ""), row["timestamp"]))

    def own_history(self, *, company_id: str, entity_scope: str, condition_id: str,
                    condition_type: str, cutoff: datetime, records: list[dict]) -> ComparisonResult:
        feature = self.registry.require("estate_net_change_pct")
        rows = self._period_rows(records, entity_scope, cutoff)
        common = {"company_id": company_id, "entity_scope": entity_scope, "analysis_cutoff": cutoff,
                      "qualified_condition_id": condition_id, "feature_id": feature["feature_id"],
                      "source_family": feature["source_family"], "comparison_type": "OWN_HISTORY",
                      "comparison_window": "available annual reporting history",
                      "feature_definition": feature["operational_meaning"], "feature_unit": feature["unit"],
                      "directionality": feature["directionality"], "normalisation_method": feature["allowed_normalisation"]}
        if condition_type not in feature["condition_types"]:
            return ComparisonResult(comparison_id=f"cmp-{_id(common)}", coverage=f"{len(rows)} periods",
                missingness=["Condition has no registered comparable estate feature."], anomaly_strength="NOT_COMPARABLE",
                status="NOT_COMPARABLE", caveats=["Only qualified, registered condition-feature pairs can be compared."], **common)
        if len(rows) < feature["minimum_history"]:
            return ComparisonResult(comparison_id=f"cmp-{_id(common)}", coverage=f"{len(rows)} periods",
                missingness=[f"At least {feature['minimum_history']} comparable periods are required."],
                anomaly_strength="INSUFFICIENT_EVIDENCE", status="INSUFFICIENT_EVIDENCE",
                caveats=["A two-point movement is not described as an anomaly."], **common)
        counts = [float(row["values"]["site_count"]) for row in rows]
        movements = [100 * (end - start) / start for start, end in itertools.pairwise(counts) if start]
        if len(movements) < 2:
            return ComparisonResult(comparison_id=f"cmp-{_id(common)}", coverage=f"{len(rows)} periods",
                missingness=["Fewer than two comparable historical movements."], anomaly_strength="INSUFFICIENT_EVIDENCE",
                status="INSUFFICIENT_EVIDENCE", **common)
        current, prior = movements[-1], movements[:-1]
        median = statistics.median(prior)
        if current > max(prior) or current < min(prior): anomaly = "HISTORICALLY_UNUSUAL"
        else: anomaly = "HISTORICALLY_NORMAL"
        evidence_ids = [f"ev-{row['source_record_id']}" for row in rows]
        return ComparisonResult(comparison_id=f"cmp-{_id(common)}", company_value=round(current, 4),
            raw_value=counts[-1] - counts[-2], denominator=counts[-2], historical_reference_values=prior,
            coverage=f"{len(rows)} comparable periods; {len(movements)} movements", missingness=[],
            anomaly_strength=anomaly, evidence_ids=evidence_ids,
            caveats=["Available history is short; this is a range comparison, not a statistical model."],
            status="AVAILABLE", reference_value=round(median, 4), gap=round(current-median, 4),
            sample_size=len(movements), method="Current annual net estate change versus median of prior observed annual movements.", **common)

    def peer(self, *, company_id: str, entity_scope: str, condition_id: str,
             condition_type: str, cutoff: datetime) -> ComparisonResult:
        feature = self.registry.require("estate_net_change_pct")
        cohort = self.estate_cohort
        common = {"company_id": company_id, "entity_scope": entity_scope, "analysis_cutoff": cutoff,
                      "qualified_condition_id": condition_id, "feature_id": feature["feature_id"],
                      "source_family": feature["source_family"], "comparison_type": "PEER_COHORT",
                      "comparison_window": cohort["period"], "feature_definition": feature["operational_meaning"],
                      "feature_unit": feature["unit"], "directionality": feature["directionality"],
                      "normalisation_method": feature["allowed_normalisation"], "cohort_definition": cohort["definition"]}
        if company_id != cohort["target_company_id"] or entity_scope != cohort["target_entity_scope"]:
            return ComparisonResult(comparison_id=f"cmp-{_id(common)}", coverage="No approved feature-specific cohort",
                missingness=["No versioned peer cohort covers this company/entity/feature."],
                anomaly_strength="NOT_COMPARABLE", status="NOT_COMPARABLE", **common)
        members=[]
        for row in cohort["candidate_peers"]:
            value = None if row["start"] in (None, 0) or row["end"] is None else 100*(row["end"]-row["start"])/row["start"]
            members.append(CohortMember(**{k:row.get(k) for k in ("company_id","display_name","entity_scope","included","exclusion_reason","evidence_id")},
                raw_value=None if row["start"] is None or row["end"] is None else row["end"]-row["start"],
                denominator=row["start"], normalised_value=None if value is None else round(value, 4)))
        included=[m for m in members if m.included and m.normalised_value is not None]
        if len(included) < feature["minimum_peer_count"]:
            return ComparisonResult(comparison_id=f"cmp-{_id(common)}", cohort_members=members,
                coverage=f"{len(included)} included of {len(members)} candidates",
                missingness=[f"Minimum cohort is {feature['minimum_peer_count']}."], anomaly_strength="INSUFFICIENT_EVIDENCE",
                status="INSUFFICIENT_EVIDENCE", **common)
        target=next(m for m in included if m.company_id == company_id)
        peer_values=[m.normalised_value for m in included if m.company_id != company_id and m.normalised_value is not None]
        reference=statistics.median(peer_values)
        ordered=sorted(m.normalised_value for m in included if m.normalised_value is not None)
        rank=ordered.index(target.normalised_value)+1
        percentile=100*(rank-1)/(len(ordered)-1)
        anomaly="ABOVE_PEERS" if target.normalised_value > reference else "BELOW_PEERS" if target.normalised_value < reference else "AROUND_PEERS"
        evidence_ids=[m.evidence_id for m in included if m.evidence_id]
        return ComparisonResult(comparison_id=f"cmp-{_id(common)}", company_value=target.normalised_value,
            raw_value=target.raw_value, denominator=target.denominator, peer_values=peer_values,
            cohort_members=members, coverage=f"{len(included)} included of {len(members)} candidates",
            missingness=[], rank=rank, percentile=round(percentile, 1), anomaly_strength=anomaly,
            evidence_ids=evidence_ids, caveats=["DEVELOPMENT_SMALL_COHORT", "Rank is descriptive, not a robust population percentile.",
                "Different merchant and depot formats remain a comparability limitation."], status="AVAILABLE",
            reference_value=round(reference,4), gap=round(target.normalised_value-reference,4),
            sample_size=len(included), method="Median peer annual net estate change; rank uses (rank-1)/(N-1).", **common)

    def compare_condition(self, *, company_id: str, entity_scope: str, condition_id: str,
                          condition_type: str, cutoff: datetime, records: list[dict]) -> list[ComparisonResult]:
        if condition_type.startswith("estate_"):
            return [self.own_history(company_id=company_id, entity_scope=entity_scope,
                    condition_id=condition_id, condition_type=condition_type, cutoff=cutoff, records=records),
                    self.peer(company_id=company_id, entity_scope=entity_scope, condition_id=condition_id,
                    condition_type=condition_type, cutoff=cutoff)]
        feature_id = "procurement_raw_award_count" if condition_type.startswith("procurement_") else "no_registered_feature"
        common = {"company_id": company_id, "entity_scope": entity_scope, "analysis_cutoff": cutoff,
                      "qualified_condition_id": condition_id, "feature_id": feature_id, "source_family": "unsupported",
                      "comparison_window": "not available", "feature_definition": "No comparison-eligible feature is registered.",
                      "feature_unit": "not available", "directionality": "NOT_APPLICABLE", "normalisation_method": "none"}
        return [ComparisonResult(comparison_id=f"cmp-{_id(common)}", comparison_type="OWN_HISTORY",
                coverage="No eligible feature", missingness=["The qualified condition has no approved comparable feature."],
                anomaly_strength="NOT_COMPARABLE", status="NOT_COMPARABLE",
                caveats=["Procurement role restrictions and non-standardised leadership events are preserved."], **common)]

    def peer_evidence(self, cutoff: datetime) -> list[dict]:
        cutoff = cutoff if cutoff.tzinfo else cutoff.replace(tzinfo=UTC)
        return [row for row in self.estate_cohort.get("evidence", [])
                if datetime.fromisoformat(row["information_available_at"]) <= cutoff]
