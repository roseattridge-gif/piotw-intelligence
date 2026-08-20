from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from piotw_conditions import ConditionQualificationEngine
from piotw_evidence import (
    EstateConditionAdapter,
    EvidenceFamilyEnvelope,
    EvidenceFamilyRecord,
    LeadershipConditionAdapter,
    MultiSourceEvidenceEngine,
    ProcurementFamilyAdapter,
)
from piotw_orchestrator import UnknownCompanyOrchestrator

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = datetime(2026, 8, 19, tzinfo=UTC)


def _record(identifier: str, family: str, when: str, *, scope: str = "company", record_type: str,
            values: dict[str, object], derivative_group: str | None = None) -> EvidenceFamilyRecord:
    return EvidenceFamilyRecord(source_record_id=identifier, family_id=family, company_id="test-co",
        entity_scope=scope, publication_or_effective_at=datetime.fromisoformat(when), retrieved_at=CUTOFF,
        source_url=f"https://example.test/{identifier}", source_hash="a" * 64,
        evidence_span=f"Exact evidence for {identifier}", collector_or_parser_version="fixture-v1",
        derivative_group=derivative_group, record_type=record_type, values=values)


def test_envelope_fails_closed_when_unavailable_has_observations() -> None:
    with pytest.raises(ValueError, match="unavailable family"):
        EvidenceFamilyEnvelope(family_id="x",adapter_version="v",company_id="c",entity_scope="c",
            cutoff=CUTOFF,availability="UNAVAILABLE",source_health="failed",raw_evidence_references=["r"],
            observations=[{"observation_id":"o","company_id":"c","entity_scope":"c","source_family":"x",
                "observed_at":CUTOFF,"value":1,"unit":"count","factual_statement":"fact","evidence_ids":["e"],
                "source_record_ids":["r"],"collection_health":"healthy"}],longitudinal_features={},candidates=[],
            missingness=[],provenance_complete=True,coverage={"family_id":"x","availability":"UNAVAILABLE",
                "source_health":"failed","history_depth":0,"entity_resolution_quality":"UNRESOLVED",
                "longitudinal_feature_ready":False,"qualification_ready":False})


def test_estate_adapter_is_cutoff_safe_and_preserves_scope() -> None:
    records=[
        _record("e1","estate_footprint_capacity","2024-03-01T00:00:00+00:00",scope="division",record_type="estate_period",values={"period":"2023","site_count":100}),
        _record("e2","estate_footprint_capacity","2025-03-01T00:00:00+00:00",scope="division",record_type="estate_period",values={"period":"2024","site_count":90,"openings":2,"closures":12}),
        _record("future","estate_footprint_capacity","2027-03-01T00:00:00+00:00",scope="division",record_type="estate_period",values={"period":"2026","site_count":60}),
    ]
    result=EstateConditionAdapter().adapt(company_id="test-co",entity_scope="division",analysis_cutoff=CUTOFF,records=records)
    assert result.raw_evidence_references == ["e1","e2"]
    assert all(item.entity_scope == "division" for item in result.observations)
    assert "future" not in result.raw_evidence_references


def test_procurement_requires_approved_entity_resolution() -> None:
    record=_record("p1","contracts_procurement","2025-01-01T00:00:00+00:00",record_type="public_award",
        values={"entity_resolution":"AMBIGUOUS","award_value":10,"currency":"GBP"})
    result=ProcurementFamilyAdapter().adapt(company_id="test-co",entity_scope="company",analysis_cutoff=CUTOFF,records=[record])
    assert result.observations == []
    assert result.availability == "NO_HISTORY"
    assert "entity resolution" in " ".join(result.missingness)


def test_duplicate_evidence_is_not_independent_corroboration() -> None:
    records=[
        _record("l1","leadership_organisation","2025-01-01T00:00:00+00:00",record_type="organisation_change",
            values={"change_type":"operating_structure"},derivative_group="same-release"),
        _record("l2","leadership_organisation","2025-01-02T00:00:00+00:00",record_type="organisation_change",
            values={"change_type":"operating_structure"},derivative_group="same-release"),
    ]
    result=LeadershipConditionAdapter().adapt(company_id="test-co",entity_scope="company",analysis_cutoff=CUTOFF,records=records)
    assert result.candidates[0].corroboration.status == "DUPLICATE_ONLY"
    qualified=ConditionQualificationEngine().qualify(result.candidates[0],observations=result.observations,
        valid_evidence_ids={"ev-l1","ev-l2"})
    assert qualified.qualification_status == "INSUFFICIENT_EVIDENCE"
    assert "duplicate_evidence" in qualified.failed_tests


def test_multi_source_engine_does_not_infer_support_from_shared_dimensions() -> None:
    engine=MultiSourceEvidenceEngine([EstateConditionAdapter(),LeadershipConditionAdapter()])
    records=[
        _record("e1","estate_footprint_capacity","2023-01-01T00:00:00+00:00",record_type="estate_period",values={"period":"2022","site_count":100}),
        _record("e2","estate_footprint_capacity","2024-01-01T00:00:00+00:00",record_type="estate_period",values={"period":"2023","site_count":90,"closures":10}),
        _record("l1","leadership_organisation","2025-01-01T00:00:00+00:00",record_type="organisation_change",values={"change_type":"operating_structure"}),
    ]
    envelopes=engine.adapt(company_id="test-co",entity_scope="company",analysis_cutoff=CUTOFF,records=records)
    assert engine.relationships(envelopes) == []


def test_explicit_cross_family_contradiction_is_preserved() -> None:
    engine=MultiSourceEvidenceEngine([EstateConditionAdapter(),LeadershipConditionAdapter()])
    records=[
        _record("e1","estate_footprint_capacity","2023-01-01T00:00:00+00:00",record_type="estate_period",values={"period":"2022","site_count":100}),
        _record("e2","estate_footprint_capacity","2024-01-01T00:00:00+00:00",record_type="estate_period",values={"period":"2023","site_count":90,"closures":10}),
        _record("l1","leadership_organisation","2025-01-01T00:00:00+00:00",record_type="organisation_change",
            values={"change_type":"other","contradicts_candidates":["estate_contraction"]}),
    ]
    envelopes=engine.adapt(company_id="test-co",entity_scope="company",analysis_cutoff=CUTOFF,records=records)
    estate=next(envelope for envelope in envelopes if envelope.family_id=="estate_footprint_capacity")
    assert estate.candidates[0].contradiction_present is True
    assert estate.candidates[0].corroboration.status == "CONTRADICTORY"
    assert estate.corroboration_links[0].relationship == "CONTRADICTS"


def test_real_travis_perkins_multisource_run_uses_generic_orchestrator() -> None:
    result=UnknownCompanyOrchestrator().build(company="travis-perkins",as_of=CUTOFF)
    present=set(result.intelligence.coverage.source_families_present)
    assert {"estate_footprint_capacity","contracts_procurement","leadership_organisation"} <= present
    assert len(result.intelligence.evidence) == 6
    assert result.intelligence.scientific_gate_run is False
    assert any(item.condition_candidate_type == "estate_reshaping" for item in result.qualifications)
    assert result.intelligence.capabilities.predict == "NOT_BUILT"


def test_cloudflare_run_keeps_missing_families_explicit() -> None:
    result=UnknownCompanyOrchestrator().build(company="cloudflare",as_of=CUTOFF)
    availability={item.source_family:item.status for item in result.manifest.source_availability}
    assert availability["estate_footprint_capacity"] == "NO_HISTORY"
    assert availability["contracts_procurement"] == "NO_HISTORY"
    assert availability["leadership_organisation"] == "NO_HISTORY"


def test_source_publication_time_controls_cutoff() -> None:
    row = _record("late-report", "estate_footprint_capacity", "2024-01-31T00:00:00+00:00",
                  record_type="estate_period", values={"period": "2024", "site_count": 10})
    row = row.model_copy(update={"source_published_at": datetime.fromisoformat("2025-03-01T00:00:00+00:00")})
    result = EstateConditionAdapter().adapt(company_id="test-co", entity_scope="company",
        analysis_cutoff=datetime.fromisoformat("2025-02-28T23:59:59+00:00"), records=[row])
    assert result.availability == "NO_HISTORY"


def test_estate_churn_and_net_direction_are_distinct_candidates() -> None:
    rows = [
        _record("ea", "estate_footprint_capacity", "2023-01-31T00:00:00+00:00",
                record_type="estate_period", values={"period": "2023", "site_count": 100}),
        _record("eb", "estate_footprint_capacity", "2024-01-31T00:00:00+00:00",
                record_type="estate_period", values={"period": "2024", "site_count": 110}),
        _record("ec", "estate_footprint_capacity", "2025-01-31T00:00:00+00:00",
                record_type="estate_period", values={"period": "2025", "site_count": 120, "openings": 15, "closures": 5}),
    ]
    result = EstateConditionAdapter().adapt(company_id="test-co", entity_scope="company",
                                             analysis_cutoff=CUTOFF, records=rows)
    assert {item.candidate_type for item in result.candidates} == {"estate_reshaping", "estate_expansion"}


def test_procurement_history_counts_comparison_periods() -> None:
    rows = [_record(f"award-{index}", "contracts_procurement", f"{period}-06-01T00:00:00+00:00",
        record_type="award_notice", values={"entity_resolution": "APPROVED", "award_value": 1,
                                             "currency": "GBP", "comparison_period": period})
        for index, period in enumerate(["2023", "2024", "2024", "2025", "2025", "2025"])]
    result = ProcurementFamilyAdapter().adapt(company_id="test-co", entity_scope="company",
                                               analysis_cutoff=CUTOFF, records=rows)
    assert result.candidates[0].history.snapshot_count == 3
    assert result.candidates[0].history.history_depth == "SHALLOW"
