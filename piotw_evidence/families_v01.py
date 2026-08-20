from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from collections import Counter
from datetime import UTC, datetime
from itertools import pairwise
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from piotw_conditions.qualification_v01 import (
    CareersConditionAdapter,
    ConditionCandidate,
    DataQualityContext,
    DenominatorContext,
    FactualObservation,
    HistoryContext,
    MagnitudeContext,
    PersistenceContext,
    assess_corroboration,
)

AvailabilityState = Literal["AVAILABLE", "UNAVAILABLE", "FAILED", "NO_HISTORY", "STALE"]
RelationshipType = Literal["INDEPENDENT_SUPPORT", "SAME_SOURCE_REPETITION", "DERIVATIVE_DUPLICATE", "CONTRADICTS"]


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _id(prefix: str, payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return f"{prefix}-{hashlib.sha256(encoded).hexdigest()[:16]}"


class EvidenceFamilyRecord(BaseModel):
    source_record_id: str
    family_id: str
    company_id: str
    entity_scope: str
    publication_or_effective_at: datetime
    source_published_at: datetime | None = None
    retrieved_at: datetime
    source_url: str
    source_hash: str
    evidence_span: str
    collector_or_parser_version: str
    source_health: Literal["healthy", "degraded", "failed"] = "healthy"
    derivative_group: str | None = None
    record_type: str
    values: dict[str, object] = Field(default_factory=dict)
    scope_kind: Literal["GROUP", "SUBSIDIARY", "BUSINESS_UNIT", "SITE", "SUPPLIER", "GEOGRAPHY"] = "GROUP"
    legal_entity_identifier: str | None = None
    entity_resolution_method: str | None = None
    entity_resolution_confidence: Literal["HIGH", "MEDIUM", "LOW", "UNRESOLVED"] | None = None


class CorroborationLink(BaseModel):
    candidate_type: str
    relationship: RelationshipType
    family_id: str
    observation_ids: list[str]
    evidence_ids: list[str]
    reason: str


class EvidenceFamilyCoverage(BaseModel):
    family_id: str
    availability: AvailabilityState
    source_health: str
    history_depth: int = Field(ge=0)
    latest_evidence_at: datetime | None = None
    entity_resolution_quality: Literal["HIGH", "MEDIUM", "LOW", "UNRESOLVED"]
    longitudinal_feature_ready: bool
    qualification_ready: bool
    limitations: list[str] = Field(default_factory=list)


class EvidenceFamilyEnvelope(BaseModel):
    schema_version: Literal["piotw-evidence-family-envelope-v0.1"] = "piotw-evidence-family-envelope-v0.1"
    family_id: str
    adapter_version: str
    company_id: str
    entity_scope: str
    cutoff: datetime
    availability: AvailabilityState
    source_health: str
    raw_evidence_references: list[str]
    observations: list[FactualObservation]
    longitudinal_features: dict[str, object]
    candidates: list[ConditionCandidate]
    corroboration_links: list[CorroborationLink] = Field(default_factory=list)
    missingness: list[str] = Field(default_factory=list)
    provenance_complete: bool
    coverage: EvidenceFamilyCoverage

    @model_validator(mode="after")
    def fail_closed(self) -> EvidenceFamilyEnvelope:
        if self.availability != "AVAILABLE" and (self.observations or self.candidates):
            raise ValueError("unavailable family cannot emit observations or candidates")
        if self.candidates and not self.provenance_complete:
            raise ValueError("condition candidates require complete provenance")
        return self


class EvidenceFamilyAdapter(ABC):
    family_id: str
    adapter_version: str

    @abstractmethod
    def adapt(self, *, company_id: str, entity_scope: str, analysis_cutoff: datetime,
              records: list[EvidenceFamilyRecord]) -> EvidenceFamilyEnvelope: ...

    def _eligible(self, records: list[EvidenceFamilyRecord], cutoff: datetime) -> list[EvidenceFamilyRecord]:
        return sorted(
            [row for row in records if row.family_id == self.family_id and row.source_health != "failed"
             and _utc(row.source_published_at or row.publication_or_effective_at) <= _utc(cutoff)],
            key=lambda row: row.publication_or_effective_at,
        )

    def _coverage(self, eligible: list[EvidenceFamilyRecord], *, limitations: list[str],
                  qualification_ready: bool) -> EvidenceFamilyCoverage:
        return EvidenceFamilyCoverage(
            family_id=self.family_id,
            availability="AVAILABLE" if eligible else "NO_HISTORY",
            source_health="healthy" if eligible and all(row.source_health == "healthy" for row in eligible) else "degraded",
            history_depth=len({row.publication_or_effective_at.date() for row in eligible}),
            latest_evidence_at=max((row.publication_or_effective_at for row in eligible), default=None),
            entity_resolution_quality="HIGH" if eligible else "UNRESOLVED",
            longitudinal_feature_ready=len(eligible) >= 2,
            qualification_ready=qualification_ready,
            limitations=limitations,
        )


class CareersEvidenceFamilyAdapter(EvidenceFamilyAdapter):
    family_id = "careers_ats"
    adapter_version = "careers-evidence-family-adapter-v0.1"

    def __init__(self) -> None:
        self.condition_adapter = CareersConditionAdapter()

    def adapt(self, *, company_id: str, entity_scope: str, analysis_cutoff: datetime,
              records: list[EvidenceFamilyRecord]) -> EvidenceFamilyEnvelope:
        eligible = self._eligible(records, analysis_cutoff)
        snapshots = [{"source_record_id": row.source_record_id, "evidence_id": f"ev-{row.source_record_id}",
                      "entity_scope": row.entity_scope, "observed_at": row.publication_or_effective_at,
                      "value": row.values.get("open_count"), "health": row.source_health, "included": True,
                      **dict(row.values.get("derived_snapshot_features") or {})} for row in eligible
                     if row.values.get("open_count") is not None]
        result = self.condition_adapter.adapt(company_id=company_id, entity_scope=entity_scope,
            analysis_cutoff=analysis_cutoff, snapshots=snapshots)
        limits=list(result.unsupported_features)
        coverage=self._coverage(eligible,limitations=limits,qualification_ready=bool(result.candidates))
        return EvidenceFamilyEnvelope(family_id=self.family_id,adapter_version=self.adapter_version,
            company_id=company_id,entity_scope=entity_scope,cutoff=_utc(analysis_cutoff),availability=coverage.availability,
            source_health=coverage.source_health,raw_evidence_references=[r.source_record_id for r in eligible],
            observations=result.observations,longitudinal_features=result.factual_features,candidates=result.candidates,
            missingness=limits,provenance_complete=all(r.source_hash and r.evidence_span for r in eligible),coverage=coverage)

    def _coverage(self, eligible: list[EvidenceFamilyRecord], *, limitations: list[str],
                  qualification_ready: bool) -> EvidenceFamilyCoverage:
        return EvidenceFamilyCoverage(
            family_id=self.family_id,
            availability="AVAILABLE" if eligible else "NO_HISTORY",
            source_health="healthy" if eligible and all(row.source_health == "healthy" for row in eligible) else "degraded",
            history_depth=len({row.publication_or_effective_at.date() for row in eligible}),
            latest_evidence_at=max((row.publication_or_effective_at for row in eligible), default=None),
            entity_resolution_quality="HIGH" if eligible else "UNRESOLVED",
            longitudinal_feature_ready=len(eligible) >= 2,
            qualification_ready=qualification_ready,
            limitations=limitations,
        )


def _observation(record: EvidenceFamilyRecord, *, value: float | None, unit: str | None,
                 statement: str) -> FactualObservation:
    return FactualObservation(
        observation_id=f"obs-{record.source_record_id}", company_id=record.company_id,
        entity_scope=record.entity_scope, source_family=record.family_id,
        observed_at=_utc(record.publication_or_effective_at), value=value, unit=unit,
        factual_statement=statement, evidence_ids=[f"ev-{record.source_record_id}"],
        source_record_ids=[record.source_record_id], collection_health=record.source_health,
        derivative_group=record.derivative_group or record.source_record_id,
    )


def _candidate_relationships(records: list[EvidenceFamilyRecord]) -> list[dict[str, object]]:
    return [{"observation_id": f"obs-{row.source_record_id}",
             "supports": list(row.values.get("supports_candidates") or []),
             "contradicts": list(row.values.get("contradicts_candidates") or [])}
            for row in records if row.values.get("supports_candidates") or row.values.get("contradicts_candidates")]


def _history(observations: list[FactualObservation], minimum: int) -> HistoryContext:
    times = sorted(item.observed_at for item in observations)
    intervals = [(right - left).total_seconds() / 86400 for left, right in pairwise(times)]
    consistency = "NOT_ASSESSED"
    if len(intervals) >= 2:
        mean = sum(intervals) / len(intervals)
        consistency = "CONSISTENT" if mean and max(abs(x - mean) for x in intervals) / mean <= .35 else "IRREGULAR"
    depth = "NONE" if not times else "SINGLE" if len(times) == 1 else "SUFFICIENT_FOR_POLICY" if len(times) >= minimum else "SHALLOW"
    return HistoryContext(snapshot_count=len(times), observation_period_days=(times[-1]-times[0]).total_seconds()/86400 if len(times)>1 else None,
                          interval_days=intervals, interval_consistency=consistency, missing_periods=None, history_depth=depth)


class EstateConditionAdapter(EvidenceFamilyAdapter):
    family_id = "estate_footprint_capacity"
    adapter_version = "estate-condition-feature-adapter-v0.1"

    def adapt(self, *, company_id: str, entity_scope: str, analysis_cutoff: datetime,
              records: list[EvidenceFamilyRecord]) -> EvidenceFamilyEnvelope:
        eligible = self._eligible(records, analysis_cutoff)
        count_records = [row for row in eligible if row.record_type == "estate_period"]
        observations = [_observation(row, value=float(row.values["site_count"]), unit="sites",
            statement=f"The source reported {int(row.values['site_count'])} sites for {row.values.get('period')}.") for row in count_records]
        openings = sum(int(row.values.get("openings") or 0) for row in count_records)
        closures = sum(int(row.values.get("closures") or 0) for row in count_records)
        features = {"site_count_trajectory":[item.value for item in observations], "openings":openings,
                    "closures":closures, "net_footprint_movement":openings-closures,
                    "relocation_events":sum(row.record_type == "site_relocation" for row in eligible),
                    "candidate_relationships":_candidate_relationships(eligible)}
        candidates: list[ConditionCandidate] = []
        if len(observations) >= 2:
            values = [float(item.value or 0) for item in observations]
            change = values[-1] - values[0]
            candidate_type = "estate_reshaping" if openings and closures else "estate_expansion" if change > 0 else "estate_contraction"
            evidence_ids = [eid for item in observations for eid in item.evidence_ids]
            candidates.append(ConditionCandidate(
                candidate_id=_id("candidate", [company_id,candidate_type,evidence_ids]), company_id=company_id,
                entity_scope=entity_scope, analysis_cutoff=_utc(analysis_cutoff), candidate_type=candidate_type,
                dimensions=["Delivery & Capacity","Change & Execution"],
                observation_ids=[item.observation_id for item in observations], evidence_ids=evidence_ids,
                evidence_families=[self.family_id], factual_summary=f"Reported site count moved from {int(values[0])} to {int(values[-1])}; disclosed movements include {openings} opening(s) and {closures} closure(s).",
                proposed_mechanism="Evidenced estate reshaping" if candidate_type == "estate_reshaping" else f"Evidenced {candidate_type.replace('_',' ')}",
                history=_history(observations,3), denominator=DenominatorContext(available=values[0]>0,value=values[0],unit="sites",evidence_ids=observations[0].evidence_ids,quality="HIGH"),
                magnitude=MagnitudeContext(absolute_change=change,relative_change=change/values[0] if values[0] else None,unit="sites"),
                persistence=PersistenceContext(status="PERSISTENT" if len(values)>=3 else "ONE_OFF",consistent_intervals=max(0,len(values)-1),total_intervals=max(0,len(values)-1)),
                corroboration=assess_corroboration(observations), data_quality=DataQualityContext(status="GOOD",source_health=["healthy"],stale=False,coverage_limitations=["Site definitions and portfolio scope can change between disclosures."]),
                historical_context_status="AVAILABLE", peer_context_status="UNAVAILABLE",
                entity_scope_consistent=all(item.entity_scope==entity_scope for item in observations),
                contradiction_present=False, factual_features=features, adapter_version=self.adapter_version))
            # Portfolio churn and net footprint direction are distinct factual candidates.
            # Preserve both when the source reports openings and closures rather than
            # allowing a mixed-movement label to hide a material net change.
            if candidate_type == "estate_reshaping" and change:
                directional_type = "estate_expansion" if change > 0 else "estate_contraction"
                candidates.append(candidates[-1].model_copy(update={
                    "candidate_id": _id("candidate", [company_id, directional_type, evidence_ids]),
                    "candidate_type": directional_type,
                    "factual_summary": f"Reported site count moved from {int(values[0])} to {int(values[-1])} across {len(values)} disclosed periods.",
                    "proposed_mechanism": f"Evidenced {directional_type.replace('_',' ')}",
                }))
        limits=["No complete site-level register; openings, closures and relocations are disclosure-dependent."]
        coverage=self._coverage(eligible,limitations=limits,qualification_ready=bool(candidates))
        return EvidenceFamilyEnvelope(family_id=self.family_id,adapter_version=self.adapter_version,company_id=company_id,
            entity_scope=entity_scope,cutoff=_utc(analysis_cutoff),availability=coverage.availability,source_health=coverage.source_health,
            raw_evidence_references=[row.source_record_id for row in eligible],observations=observations,longitudinal_features=features,
            candidates=candidates,missingness=limits,provenance_complete=all(row.source_hash and row.evidence_span for row in eligible),coverage=coverage)


class ProcurementFamilyAdapter(EvidenceFamilyAdapter):
    family_id = "contracts_procurement"
    adapter_version = "procurement-family-adapter-v0.2"

    def adapt(self, *, company_id: str, entity_scope: str, analysis_cutoff: datetime,
              records: list[EvidenceFamilyRecord]) -> EvidenceFamilyEnvelope:
        eligible=self._eligible(records,analysis_cutoff)
        approved=[row for row in eligible if row.values.get("entity_resolution") == "APPROVED"]
        observations=[_observation(row,value=float(row.values["award_value"]) if row.values.get("award_value") is not None else None,
            unit=str(row.values.get("currency") or "unknown"),statement=f"A public award notice named the resolved company entity for {row.values.get('category','an unspecified category')}.") for row in approved]
        periods=Counter(str(row.values.get("comparison_period") or row.publication_or_effective_at.strftime("%Y-%m")) for row in approved)
        categories=Counter(str(row.values.get("category") or "unknown") for row in approved)
        comparable=[row for row in approved if row.values.get("award_value") is not None and row.values.get("currency")]
        features={"award_count_by_period":dict(sorted(periods.items())),"category_mix":dict(categories),
                  "disclosed_value_by_currency":dict(Counter()),"new_supplier_appearances":None,"repeat_supplier_count":None,
                  "history_depth_periods":len(periods),"candidate_relationships":_candidate_relationships(approved)}
        for row in comparable:
            currency=str(row.values["currency"]); features["disclosed_value_by_currency"][currency]=features["disclosed_value_by_currency"].get(currency,0)+float(row.values["award_value"])
        candidates=[]
        if len(periods)>=2:
            ordered=sorted(periods.items()); values=[float(value) for _,value in ordered]; change=values[-1]-values[0]
            if change:
                changes=[right-left for left,right in pairwise(values)]
                signs={1 if item>0 else -1 for item in changes if item}
                consistent_intervals=len([item for item in changes if item]) if len(signs)==1 else 0
                ctype="procurement_activity_acceleration" if change>0 else "procurement_activity_deceleration"
                evidence_ids=[eid for item in observations for eid in item.evidence_ids]
                candidates.append(ConditionCandidate(candidate_id=_id("candidate",[company_id,ctype,evidence_ids]),company_id=company_id,
                    entity_scope=entity_scope,analysis_cutoff=_utc(analysis_cutoff),candidate_type=ctype,
                    dimensions=["Supply Chain & Resilience","Change & Execution"],observation_ids=[o.observation_id for o in observations],
                    evidence_ids=evidence_ids,evidence_families=[self.family_id],factual_summary=f"Resolved public award records moved from {int(values[0])} to {int(values[-1])} across {len(values)} publication periods.",
                    proposed_mechanism="Published public procurement activity change",history=_history([
                        _observation(next(row for row in approved if str(row.values.get("comparison_period") or row.publication_or_effective_at.strftime("%Y-%m")) == period),
                            value=float(value), unit="award_records", statement=f"{value} resolved award record(s) were published in {period}.")
                        for period, value in ordered
                    ],4),
                    denominator=DenominatorContext(available=values[0]>0,value=values[0],unit="award_records",evidence_ids=observations[0].evidence_ids,quality="MEDIUM"),
                    magnitude=MagnitudeContext(absolute_change=change,relative_change=change/values[0] if values[0] else None,unit="award_records"),
                    persistence=PersistenceContext(
                        status="PERSISTENT" if consistent_intervals >= 2 else "REVERSED" if len(signs)>1 else "ONE_OFF",
                        consistent_intervals=consistent_intervals, total_intervals=len(changes)),corroboration=assess_corroboration(observations),
                    data_quality=DataQualityContext(status="GOOD",source_health=["healthy"],stale=False,coverage_limitations=["Public awards are a partial view of company commercial activity."]),
                    historical_context_status="INSUFFICIENT_EVIDENCE",peer_context_status="UNAVAILABLE",entity_scope_consistent=all(o.entity_scope==entity_scope for o in observations),
                    contradiction_present=False,factual_features=features,adapter_version=self.adapter_version))
        limits=[] if approved else ["No source record has an approved company/entity resolution."]
        if len(periods)<4: limits.append("Fewer than four comparable publication periods are available.")
        coverage=self._coverage(approved,limitations=limits,qualification_ready=bool(candidates))
        return EvidenceFamilyEnvelope(family_id=self.family_id,adapter_version=self.adapter_version,company_id=company_id,entity_scope=entity_scope,
            cutoff=_utc(analysis_cutoff),availability=coverage.availability,source_health=coverage.source_health,raw_evidence_references=[r.source_record_id for r in approved],
            observations=observations,longitudinal_features=features,candidates=candidates,missingness=limits,
            provenance_complete=all(r.source_hash and r.evidence_span for r in approved),coverage=coverage)


class LeadershipConditionAdapter(EvidenceFamilyAdapter):
    family_id = "leadership_organisation"
    adapter_version = "leadership-organisation-adapter-v0.1"

    def adapt(self, *, company_id: str, entity_scope: str, analysis_cutoff: datetime,
              records: list[EvidenceFamilyRecord]) -> EvidenceFamilyEnvelope:
        eligible=self._eligible(records,analysis_cutoff)
        observations=[_observation(row,value=1,unit="announced_change",statement=str(row.values.get("factual_statement") or row.evidence_span)) for row in eligible]
        by_type=Counter(str(row.values.get("change_type") or "unknown") for row in eligible)
        features={"announced_changes_by_type":dict(by_type),"senior_change_count":len(eligible),
                  "functions_affected":sorted({str(x) for row in eligible for x in row.values.get("functions",[])}),
                  "candidate_relationships":_candidate_relationships(eligible)}
        candidates=[]
        restructuring=[row for row in eligible if row.values.get("change_type") in {"operating_structure","reporting_line_redesign","role_creation_removal"}]
        if restructuring:
            obs=[o for o in observations if o.source_record_ids[0] in {r.source_record_id for r in restructuring}]
            evidence_ids=[eid for o in obs for eid in o.evidence_ids]
            candidates.append(ConditionCandidate(candidate_id=_id("candidate",[company_id,"organisational_restructuring",evidence_ids]),company_id=company_id,
                entity_scope=entity_scope,analysis_cutoff=_utc(analysis_cutoff),candidate_type="organisational_restructuring",
                dimensions=["Workforce & Capability","Change & Execution"],observation_ids=[o.observation_id for o in obs],evidence_ids=evidence_ids,
                evidence_families=[self.family_id],factual_summary=f"{len(obs)} source-backed operating-structure change(s) were announced.",
                proposed_mechanism="Announced operating-structure and accountability redesign",history=_history(obs,1),
                denominator=DenominatorContext(available=False,quality="UNAVAILABLE"),magnitude=MagnitudeContext(absolute_change=float(len(obs)),unit="announced_changes"),
                persistence=PersistenceContext(status="ONE_OFF",consistent_intervals=0,total_intervals=0),corroboration=assess_corroboration(obs),
                data_quality=DataQualityContext(status="GOOD",source_health=["healthy"],stale=False,coverage_limitations=["Public announcements do not provide a complete leadership-change register."]),
                historical_context_status="UNAVAILABLE",peer_context_status="UNAVAILABLE",entity_scope_consistent=all(o.entity_scope==entity_scope for o in obs),
                contradiction_present=False,factual_features=features,adapter_version=self.adapter_version))
        limits=["No inference is made about competence, sentiment or the success of announced changes."]
        coverage=self._coverage(eligible,limitations=limits,qualification_ready=bool(candidates))
        return EvidenceFamilyEnvelope(family_id=self.family_id,adapter_version=self.adapter_version,company_id=company_id,entity_scope=entity_scope,
            cutoff=_utc(analysis_cutoff),availability=coverage.availability,source_health=coverage.source_health,raw_evidence_references=[r.source_record_id for r in eligible],
            observations=observations,longitudinal_features=features,candidates=candidates,missingness=limits,
            provenance_complete=all(r.source_hash and r.evidence_span for r in eligible),coverage=coverage)


class MultiSourceEvidenceEngine:
    engine_version = "piotw-multi-source-evidence-depth-v0.1"

    def __init__(self, adapters: list[EvidenceFamilyAdapter]) -> None:
        ids=[adapter.family_id for adapter in adapters]
        if len(ids)!=len(set(ids)): raise ValueError("duplicate evidence-family adapter")
        self.adapters=adapters

    def adapt(self, *, company_id: str, entity_scope: str, analysis_cutoff: datetime,
              records: list[EvidenceFamilyRecord]) -> list[EvidenceFamilyEnvelope]:
        envelopes=[]
        for adapter in self.adapters:
            family_records=[row for row in records if row.family_id==adapter.family_id]
            scopes={row.entity_scope for row in family_records}
            resolved_scope=next(iter(scopes)) if len(scopes)==1 else entity_scope
            envelopes.append(adapter.adapt(company_id=company_id,entity_scope=resolved_scope,
                analysis_cutoff=analysis_cutoff,records=records))
        links=self.relationships(envelopes)
        all_observations={item.observation_id:item for envelope in envelopes for item in envelope.observations}
        for envelope in envelopes:
            envelope.corroboration_links=[link for link in links if any(
                candidate.candidate_type==link.candidate_type for candidate in envelope.candidates)]
            for index,candidate in enumerate(envelope.candidates):
                relevant=[link for link in links if link.candidate_type==candidate.candidate_type]
                if not relevant: continue
                extra_obs=[oid for link in relevant for oid in link.observation_ids]
                extra_evidence=[eid for link in relevant for eid in link.evidence_ids]
                support=[oid for link in relevant if link.relationship=="INDEPENDENT_SUPPORT" for oid in link.observation_ids]
                contradict=[oid for link in relevant if link.relationship=="CONTRADICTS" for oid in link.observation_ids]
                families=sorted(set(candidate.evidence_families)|{link.family_id for link in relevant})
                scopes={candidate.entity_scope}|{all_observations[oid].entity_scope for oid in extra_obs}
                candidate.corroboration=candidate.corroboration.model_copy(update={
                    "status":"CONTRADICTORY" if contradict else "INDEPENDENT",
                    "independent_source_families":families,
                    "related_observation_count":candidate.corroboration.related_observation_count+len(extra_obs),
                    "supporting_observation_ids":sorted(set(candidate.corroboration.supporting_observation_ids+support)),
                    "contradicting_observation_ids":sorted(set(candidate.corroboration.contradicting_observation_ids+contradict)),
                })
                envelope.candidates[index]=candidate.model_copy(update={
                    "observation_ids":candidate.observation_ids+extra_obs,
                    "evidence_ids":candidate.evidence_ids+extra_evidence,
                    "evidence_families":families,
                    "entity_scope_consistent":len(scopes)==1,
                    "contradiction_present":candidate.contradiction_present or bool(contradict),
                })
        return envelopes

    @staticmethod
    def relationships(envelopes: list[EvidenceFamilyEnvelope]) -> list[CorroborationLink]:
        links=[]
        candidates=[candidate for envelope in envelopes for candidate in envelope.candidates]
        for candidate in candidates:
            for envelope in envelopes:
                if envelope.family_id in candidate.evidence_families or not envelope.observations: continue
                explicit=[o for o in envelope.observations if candidate.candidate_type in
                          next((r for r in envelope.longitudinal_features.get("candidate_relationships",[]) if r.get("observation_id")==o.observation_id),{}).get("supports",[])]
                if explicit:
                    links.append(CorroborationLink(candidate_type=candidate.candidate_type,relationship="INDEPENDENT_SUPPORT",
                        family_id=envelope.family_id,observation_ids=[o.observation_id for o in explicit],
                        evidence_ids=[e for o in explicit for e in o.evidence_ids],reason="Explicit family adapter relationship; not inferred from shared dimensions."))
                opposing=[o for o in envelope.observations if candidate.candidate_type in
                          next((r for r in envelope.longitudinal_features.get("candidate_relationships",[]) if r.get("observation_id")==o.observation_id),{}).get("contradicts",[])]
                if opposing:
                    links.append(CorroborationLink(candidate_type=candidate.candidate_type,relationship="CONTRADICTS",
                        family_id=envelope.family_id,observation_ids=[o.observation_id for o in opposing],
                        evidence_ids=[e for o in opposing for e in o.evidence_ids],reason="Explicit contradictory family claim retained without narrative reconciliation."))
        return links
