from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from piotw_conditions import (
    CareersConditionAdapter,
    ConditionQualificationEngine,
    QualificationResult,
)
from piotw_intelligence.company_intelligence_v01 import (
    CompanyIntelligenceV01,
    assemble_company_intelligence,
)
from pipelines.careers.models import CareerSource

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPANY_REGISTRY = ROOT / "config/evidence/jobs_sources_v0_2.json"
DEFAULT_CAREERS_DATABASE = ROOT / "data/collection/careers_v1/careers_longitudinal.sqlite3"
DEFAULT_RUN_DIRECTORY = ROOT / "data/derived/unknown_company_runs"
DEFAULT_WEB_DIRECTORY = ROOT / "piotw-web/data/company-intelligence-v01"


class IdentityResolution(BaseModel):
    input_value: str
    company_id: str
    display_name: str
    entity_id: str
    match_method: Literal["EXACT_COMPANY_ID", "NORMALIZED_COMPANY_NAME", "EXPLICIT_ENTITY_ID"]
    source_registry: str


class SourceAvailability(BaseModel):
    source_family: str
    status: Literal["AVAILABLE", "UNAVAILABLE", "FAILED", "NO_HISTORY"]
    collector_or_adapter: str | None = None
    health: str | None = None
    record_count: int = Field(ge=0)
    reason: str


class ManifestEvidenceRecord(BaseModel):
    manifest_record_id: str
    company_id: str
    entity_scope: str
    source_family: str
    source_record_id: str
    publication_or_effective_at: datetime
    retrieved_at: datetime
    collector_or_parser_version: str
    source_url: str | None
    source_hash: str | None
    cutoff_eligible: bool
    included: bool
    inclusion_or_exclusion_reason: str
    collection_health: str
    observed_value: int | None = None
    observed_unit: str | None = None
    derived_snapshot_features: dict[str, object] | None = None


class EvidenceManifest(BaseModel):
    schema_version: Literal["piotw-evidence-manifest-v0.1"]
    run_id: str
    orchestrator_version: str
    condition_policy_version: str
    condition_policy_hash: str
    company: IdentityResolution
    as_of: datetime
    source_availability: list[SourceAvailability]
    records: list[ManifestEvidenceRecord]
    included_record_count: int = Field(ge=0)
    excluded_record_count: int = Field(ge=0)
    manifest_hash: str


class OrchestrationResult(BaseModel):
    run_id: str
    manifest_path: str | None
    intelligence_path: str | None
    qualifications_path: str | None
    web_path: str | None
    manifest: EvidenceManifest
    qualifications: list[QualificationResult]
    intelligence: CompanyIntelligenceV01
    manual_intervention_required: bool = False


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _digest(payload: object) -> str:
    serialised = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialised.encode()).hexdigest()


class UnknownCompanyOrchestrator:
    """Assemble a sparse, cutoff-safe company object from approved stored evidence."""

    orchestrator_version = "unknown-company-orchestrator-v0.2-condition-qualification"

    def __init__(
        self,
        *,
        company_registry: str | Path = DEFAULT_COMPANY_REGISTRY,
        careers_database: str | Path = DEFAULT_CAREERS_DATABASE,
        run_directory: str | Path = DEFAULT_RUN_DIRECTORY,
        web_directory: str | Path = DEFAULT_WEB_DIRECTORY,
    ) -> None:
        self.company_registry = Path(company_registry)
        self.careers_database = Path(careers_database)
        self.run_directory = Path(run_directory)
        self.web_directory = Path(web_directory)
        self.condition_adapter = CareersConditionAdapter()
        self.condition_engine = ConditionQualificationEngine()

    def resolve_identity(self, company: str, explicit_entity_id: str | None = None) -> IdentityResolution:
        sources = [CareerSource.model_validate(row) for row in json.loads(self.company_registry.read_text())]
        if explicit_entity_id:
            matches = [source for source in sources if source.company_id == explicit_entity_id]
            method = "EXPLICIT_ENTITY_ID"
        else:
            exact = [source for source in sources if source.company_id == company]
            matches = exact or [source for source in sources if _normalise(source.company_name) == _normalise(company)]
            method = "EXACT_COMPANY_ID" if exact else "NORMALIZED_COMPANY_NAME"
        if not matches:
            raise KeyError(f"company is not present in the approved source registry: {company}")
        company_ids = {source.company_id for source in matches}
        if len(company_ids) != 1:
            raise ValueError(f"ambiguous company identity: {company}")
        source = matches[0]
        return IdentityResolution(
            input_value=company,
            company_id=source.company_id,
            display_name=source.company_name,
            entity_id=source.company_id,
            match_method=method,
            source_registry=str(self.company_registry),
        )

    def _configured_source(self, company_id: str) -> CareerSource:
        sources = [CareerSource.model_validate(row) for row in json.loads(self.company_registry.read_text())]
        return next(source for source in sources if source.company_id == company_id)

    def _careers_records(
        self, identity: IdentityResolution, as_of: datetime
    ) -> tuple[list[ManifestEvidenceRecord], SourceAvailability]:
        source = self._configured_source(identity.company_id)
        if not self.careers_database.is_file():
            return [], SourceAvailability(
                source_family="careers_ats", status="UNAVAILABLE", collector_or_adapter=source.provider,
                record_count=0, reason="Configured source exists but the approved careers evidence store is unavailable.",
            )
        with sqlite3.connect(self.careers_database) as connection:
            state = connection.execute(
                """SELECT health,last_successful_fetch FROM career_source_state
                   WHERE company_id=? AND provider=?""", (identity.company_id, source.provider)
            ).fetchone()
            rows = connection.execute(
                """SELECT s.snapshot_id,s.fetch_timestamp,s.retrieval_status,s.source_hash,s.open_count,s.collector_version,
                          a.derived_origin,a.new_count,a.persistent_count,a.absent_once_count,a.confirmed_closed_count,
                          a.reopened_count,a.function_mix,a.seniority_mix,a.geography_mix,a.technology_mix,a.missingness
                   FROM career_collection_snapshots s LEFT JOIN career_snapshot_aggregates a ON a.snapshot_id=s.snapshot_id
                   WHERE s.company_id=? AND s.provider=?
                   ORDER BY fetch_timestamp""", (identity.company_id, source.provider)
            ).fetchall()
        records: list[ManifestEvidenceRecord] = []
        for row in rows:
            snapshot_id, fetched_at, health, source_hash, open_count, version = row[:6]
            aggregate = None
            if row[6]:
                aggregate = {"derived_origin": row[6], "new_count": row[7], "persistent_count": row[8],
                    "absent_once_count": row[9], "confirmed_closed_count": row[10], "reopened_count": row[11],
                    "function_mix": json.loads(row[12]), "seniority_mix": json.loads(row[13]),
                    "geography_mix": json.loads(row[14]), "technology_mix": json.loads(row[15]),
                    "missingness": json.loads(row[16])}
            timestamp = _utc(datetime.fromisoformat(fetched_at))
            eligible = timestamp <= as_of
            included = eligible and health == "healthy" and bool(source_hash)
            reason = (
                "INCLUDED_CUTOFF_SAFE_HEALTHY_SNAPSHOT" if included else
                "EXCLUDED_AFTER_ANALYSIS_CUTOFF" if not eligible else
                f"EXCLUDED_COLLECTION_{str(health).upper()}"
            )
            records.append(ManifestEvidenceRecord(
                manifest_record_id=f"manifest-{snapshot_id}", company_id=identity.company_id,
                entity_scope=identity.entity_id, source_family="careers_ats", source_record_id=snapshot_id,
                publication_or_effective_at=timestamp, retrieved_at=timestamp,
                collector_or_parser_version=version, source_url=source.careers_url,
                source_hash=source_hash, cutoff_eligible=eligible, included=included,
                inclusion_or_exclusion_reason=reason, collection_health=health,
                observed_value=open_count, observed_unit="open_postings",
                derived_snapshot_features=aggregate,
            ))
        included_count = sum(record.included for record in records)
        current_health = state[0] if state else None
        if included_count:
            status = "AVAILABLE"
            reason = f"{included_count} healthy stored snapshot(s) were available by the cutoff."
        elif rows and any(record.cutoff_eligible for record in records):
            status = "FAILED" if current_health == "fetch_failed" else "NO_HISTORY"
            reason = "Stored cutoff-eligible collection attempts exist but none is a healthy evidence record."
        elif rows:
            status = "NO_HISTORY"
            reason = "The source has stored history, but all records are after the analysis cutoff."
        else:
            status = "NO_HISTORY"
            reason = "The company is configured, but no stored careers snapshots exist."
        return records, SourceAvailability(
            source_family="careers_ats", status=status, collector_or_adapter=source.provider,
            health=current_health, record_count=included_count, reason=reason,
        )

    @staticmethod
    def _unsupported_sources() -> list[SourceAvailability]:
        return [
            SourceAvailability(source_family="contracts_procurement", status="UNAVAILABLE",
                record_count=0, reason="No approved supplier-to-company entity match exists for this run."),
            SourceAvailability(source_family="issuer_disclosures", status="UNAVAILABLE",
                record_count=0, reason="No company-agnostic approved issuer collector is wired to this orchestrator."),
            SourceAvailability(source_family="regulatory_operating_notices", status="UNAVAILABLE",
                record_count=0, reason="Feasibility is documented, but no approved production collector is wired."),
        ]

    def build(self, *, company: str, as_of: datetime, explicit_entity_id: str | None = None) -> OrchestrationResult:
        as_of = _utc(as_of)
        identity = self.resolve_identity(company, explicit_entity_id)
        records, careers_status = self._careers_records(identity, as_of)
        source_availability = [careers_status, *self._unsupported_sources()]
        manifest_material = {
            "orchestrator_version": self.orchestrator_version,
            "condition_policy_version": self.condition_engine.policy["policy_version"],
            "condition_policy_hash": self.condition_engine.policy_hash,
            "company": identity.model_dump(mode="json"), "as_of": as_of.isoformat(),
            "sources": [item.model_dump(mode="json") for item in source_availability],
            "records": [item.model_dump(mode="json") for item in records],
        }
        manifest_hash = _digest(manifest_material)
        run_id = f"uc-{identity.company_id}-{as_of.strftime('%Y%m%dT%H%M%SZ')}-{manifest_hash[:12]}"
        manifest = EvidenceManifest(
            schema_version="piotw-evidence-manifest-v0.1", run_id=run_id, company=identity,
            orchestrator_version=self.orchestrator_version,
            condition_policy_version=self.condition_engine.policy["policy_version"],
            condition_policy_hash=self.condition_engine.policy_hash,
            as_of=as_of, source_availability=source_availability, records=records,
            included_record_count=sum(item.included for item in records),
            excluded_record_count=sum(not item.included for item in records), manifest_hash=manifest_hash,
        )
        qualifications = self._qualify(identity, as_of, records)
        intelligence = self._assemble(identity, as_of, records, source_availability, qualifications)
        return OrchestrationResult(run_id=run_id, manifest_path=None, intelligence_path=None,
            qualifications_path=None, web_path=None, manifest=manifest,
            qualifications=qualifications, intelligence=intelligence)

    def _qualify(
        self, identity: IdentityResolution, as_of: datetime, records: list[ManifestEvidenceRecord]
    ) -> list[QualificationResult]:
        snapshots = [{
            "source_record_id": record.source_record_id,
            "evidence_id": f"ev-{record.source_record_id}",
            "entity_scope": record.entity_scope,
            "observed_at": record.publication_or_effective_at,
            "value": record.observed_value,
            "health": record.collection_health,
            "included": record.included,
            **(record.derived_snapshot_features or {}),
        } for record in records if record.observed_value is not None]
        adapted = self.condition_adapter.adapt(
            company_id=identity.company_id, entity_scope=identity.entity_id,
            analysis_cutoff=as_of, snapshots=snapshots)
        valid_evidence_ids = {f"ev-{record.source_record_id}" for record in records if record.included}
        return [self.condition_engine.qualify(candidate, observations=adapted.observations,
            valid_evidence_ids=valid_evidence_ids) for candidate in adapted.candidates]

    def _assemble(
        self, identity: IdentityResolution, as_of: datetime,
        records: list[ManifestEvidenceRecord], availability: list[SourceAvailability],
        qualifications: list[QualificationResult],
    ) -> CompanyIntelligenceV01:
        included = [record for record in records if record.included]
        evidence = [
            {"evidence_id": f"ev-{record.source_record_id}", "source_id": record.source_record_id,
             "title": f"Careers snapshot — {record.publication_or_effective_at.isoformat()}",
             "source_family": record.source_family, "source_url": record.source_url,
             "source_hash": record.source_hash, "publication_date": record.publication_or_effective_at.date().isoformat(),
             "information_available_at": record.retrieved_at, "entity_scope": record.entity_scope,
             "evidence_span": f"Approved careers collector observed {record.observed_value} open postings for {identity.display_name}.",
             "collector_or_parser_version": record.collector_or_parser_version}
            for record in included
        ]
        conditions = [condition for result in qualifications
                      if (condition := result.canonical_condition()) is not None]
        qualification_views = [{
            "qualification_id": result.qualification_id,
            "candidate_type": result.condition_candidate_type,
            "status": result.qualification_status,
            "dimension": result.dimensions[0],
            "observation_ids": result.supporting_observation_ids,
            "evidence_ids": result.supporting_evidence_ids,
            "what_observed": result.observed_explanation,
            "why_it_might_matter": result.why_it_might_matter,
            "evidence_strength": result.evidence_strength_explanation,
            "failed_tests": result.failed_tests,
            "missing_information": result.missing_information,
            "what_would_change_view": result.what_would_change_view,
            "policy_version": result.policy_version,
            "scientifically_validated": False,
        } for result in qualifications]
        comparison = []
        if conditions:
            comparison = [{"comparison_id":"comparison-careers-state","condition_id":conditions[0]["condition_id"],
                "status":"INSUFFICIENT_EVIDENCE","basis":"PEER_AND_HISTORY","metric":"Open-vacancy movement",
                "target_value":None,"comparator_value":None,"gap":None,"unit":None,"percentile":None,
                "sample_size":None,"peer_set_or_history":None,"method":None,"confidence":"NOT_ASSESSED",
                "evidence_ids":[],"caveats":[],
                "withheld_reason":"Only one or two early snapshots exist and no approved size/coverage-normalised peer benchmark is available."}]
        predictions = [{"prediction_id":"prediction-unknown-company","status":"NOT_BUILT","target_event":None,
            "horizon":None,"probability":None,"confidence":"NOT_ASSESSED","model_version":None,
            "historical_pattern":None,"supporting_condition_ids":[],"evidence_ids":[],"caveats":[],
            "withheld_reason":"No validated operational predictive-pattern engine is available."}]
        interventions = [{"intervention_id":"intervention-unknown-company","status":"WITHHELD","title":None,
            "mechanism":None,"investigation_steps":[],"supporting_condition_ids":[],"evidence_ids":[],
            "evidence_strength":"NOT_ASSESSED","falsifiers":[],"caveats":[],
            "withheld_reason":"A factual vacancy count alone does not support a driver-specific intervention."}]
        impacts = [{"impact_id":"impact-unknown-company","intervention_id":"intervention-unknown-company",
            "status":"WITHHELD","mechanism":None,"measure":None,"low":None,"base":None,"high":None,
            "currency":None,"unit":None,"period":None,"incremental":None,"assumptions":[],"evidence_ids":[],
            "caveats":[],"withheld_reason":"No evidence-backed intervention or financial mechanism is available."}]
        present = [item.source_family for item in availability if item.status == "AVAILABLE"]
        missing = [item.source_family for item in availability if item.status != "AVAILABLE"]
        coverage_status = "LOW" if included else "INSUFFICIENT"
        payload = {
            "schema_version":"piotw-company-intelligence-v0.1",
            "company":{"company_id":identity.company_id,"display_name":identity.display_name,"legal_name":None,
                       "ticker":None,"geography":None,"activity":None},
            "as_of":as_of,"generated_at":as_of,"methodology_version":self.orchestrator_version,
            "scientific_gate_run":False,
            "coverage":{"status":coverage_status,"source_families_present":present,
                "source_families_missing":missing,"evidence_count":len(evidence),
                "provenance_complete":all(item["source_hash"] for item in evidence),
                "caveats":[item.reason for item in availability if item.status != "AVAILABLE"]},
            "evidence":evidence,"condition_qualifications":qualification_views,
            "conditions":conditions,"comparisons":comparison,"predictions":predictions,
            "interventions":interventions,"financial_impacts":impacts,
            "capabilities":{"detect":"AVAILABLE" if conditions else "INSUFFICIENT_EVIDENCE","compare":"INSUFFICIENT_EVIDENCE",
                "predict":"NOT_BUILT","prescribe":"WITHHELD","quantify":"WITHHELD"},
            "missing_capabilities":["Scientifically validated operational-condition qualification policy",
                "Coverage-normalised peer and historical benchmark","Validated predictive-pattern engine",
                "Driver-specific intervention engine","Evidence-backed financial mechanism"],
            "overall_confidence":"LOW" if evidence else "NOT_ASSESSED",
        }
        return assemble_company_intelligence(payload)

    def persist(self, result: OrchestrationResult, *, publish_to_web: bool = True) -> OrchestrationResult:
        run_path = self.run_directory / result.run_id
        run_path.mkdir(parents=True, exist_ok=True)
        manifest_path = run_path / "evidence_manifest.json"
        intelligence_path = run_path / "company_intelligence.json"
        qualifications_path = run_path / "condition_qualifications.json"
        manifest_path.write_text(result.manifest.model_dump_json(indent=2) + "\n")
        intelligence_path.write_text(result.intelligence.model_dump_json(indent=2) + "\n")
        qualifications_path.write_text(json.dumps(
            [item.model_dump(mode="json") for item in result.qualifications], indent=2) + "\n")
        web_path = None
        if publish_to_web:
            self.web_directory.mkdir(parents=True, exist_ok=True)
            web_path = self.web_directory / f"{result.intelligence.company.company_id}.json"
            web_path.write_text(result.intelligence.model_dump_json(indent=2) + "\n")
        return result.model_copy(update={"manifest_path":str(manifest_path),
            "intelligence_path":str(intelligence_path), "qualifications_path":str(qualifications_path),
            "web_path":str(web_path) if web_path else None})
