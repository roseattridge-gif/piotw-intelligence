from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from piotw_conditions.qualification_v01 import (
    CareersConditionAdapter,
    ConditionQualificationEngine,
    FactualObservation,
    ProcurementConditionAdapter,
    assess_corroboration,
)
from pipelines.procurement.find_a_tender import ProcurementRecord


def _snapshots(values: list[int], *, health: str = "healthy", scopes: list[str] | None = None,
               start: datetime | None = None) -> list[dict[str, object]]:
    start = start or datetime(2026, 1, 1, tzinfo=UTC)
    scopes = scopes or ["company-alpha"] * len(values)
    return [{
        "source_record_id": f"snapshot-{index}", "evidence_id": f"ev-snapshot-{index}",
        "entity_scope": scopes[index], "observed_at": start + timedelta(days=index * 2),
        "value": value, "health": health, "included": True,
    } for index, value in enumerate(values)]


def _qualify(values: list[int], **snapshot_kwargs):
    cutoff = datetime(2026, 2, 1, tzinfo=UTC)
    adapted = CareersConditionAdapter().adapt(
        company_id="company-alpha", entity_scope="company-alpha", analysis_cutoff=cutoff,
        snapshots=_snapshots(values, **snapshot_kwargs))
    assert adapted.candidates
    result = ConditionQualificationEngine().qualify(
        adapted.candidates[0], observations=adapted.observations,
        valid_evidence_ids={value for item in adapted.observations for value in item.evidence_ids})
    return adapted, result


def test_persistent_material_careers_change_can_qualify_under_development_policy() -> None:
    adapted, result = _qualify([100, 85, 70, 55])
    assert result.qualification_status == "QUALIFIED"
    assert result.direction == "DECREASING"
    assert result.materiality == "LOW"
    assert result.scientifically_validated is False
    assert result.canonical_condition() is not None
    assert len(adapted.observations) == 4


@pytest.mark.parametrize(
    ("values", "failed_test"),
    [([100, 98], "history_depth"), ([100, 99, 98, 97], "magnitude"),
     ([100, 80, 90, 70], "contradiction")],
)
def test_shallow_small_or_contradictory_change_is_withheld(values: list[int], failed_test: str) -> None:
    _, result = _qualify(values)
    assert result.qualification_status == "INSUFFICIENT_EVIDENCE"
    assert failed_test in result.failed_tests
    assert result.direction == "UNKNOWN" and result.materiality == "UNKNOWN"


def test_rich_snapshot_features_remain_factual_and_do_not_bypass_qualification() -> None:
    rows = _snapshots([100, 96])
    rows[0].update({"derived_origin": "LEGACY_SUMMARY_ONLY", "function_mix": {}})
    rows[1].update({"derived_origin": "HISTORICAL_REPROCESSING",
        "function_mix": {"engineering": 40, "other_unknown": 56},
        "seniority_mix": {"individual_contributor": 90, "manager": 6},
        "geography_mix": {"United Kingdom": 20, "unknown": 76},
        "technology_mix": {"Python": 8}, "new_count": 3, "persistent_count": 93,
        "absent_once_count": None, "confirmed_closed_count": 7, "reopened_count": 0})
    adapted = CareersConditionAdapter().adapt(company_id="company-alpha", entity_scope="company-alpha",
        analysis_cutoff=datetime(2026, 2, 1, tzinfo=UTC), snapshots=rows)
    result = ConditionQualificationEngine().qualify(adapted.candidates[0], observations=adapted.observations,
        valid_evidence_ids={"ev-snapshot-0", "ev-snapshot-1"})
    assert adapted.factual_features["function_mix_trajectory"]["engineering"] == [None, 40]
    assert adapted.factual_features["missing_period_flags"] == [True, False]
    assert adapted.candidates[0].corroboration.status == "MULTIPLE_OBSERVATIONS_ONE_FAMILY"
    assert result.qualification_status == "INSUFFICIENT_EVIDENCE"


def test_missing_denominator_collection_failure_and_scope_conflict_fail_closed() -> None:
    _, missing_denominator = _qualify([0, 10, 20, 30])
    assert "denominator" in missing_denominator.failed_tests

    _, failed_source = _qualify([100, 80, 60, 40], health="fetch_failed")
    assert "source_health" in failed_source.failed_tests

    _, scope_conflict = _qualify([100, 80, 60, 40],
        scopes=["company-alpha", "segment-a", "company-alpha", "company-alpha"])
    assert "entity_scope" in scope_conflict.failed_tests


def test_duplicate_evidence_is_not_independent_corroboration() -> None:
    adapted, _ = _qualify([100, 80, 60, 40])
    candidate = adapted.candidates[0].model_copy(update={
        "evidence_ids": [*adapted.candidates[0].evidence_ids, adapted.candidates[0].evidence_ids[0]],
        "corroboration": adapted.candidates[0].corroboration.model_copy(update={"status": "DUPLICATE_ONLY"}),
    })
    result = ConditionQualificationEngine().qualify(candidate, observations=adapted.observations,
        valid_evidence_ids=set(candidate.evidence_ids))
    assert result.qualification_status == "INSUFFICIENT_EVIDENCE"
    assert "duplicate_evidence" in result.failed_tests


def test_corroboration_distinguishes_cross_source_duplicate_and_contradiction() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    def observation(identifier: str, family: str, group: str) -> FactualObservation:
        return FactualObservation(observation_id=identifier, company_id="company-alpha",
            entity_scope="company-alpha", source_family=family, observed_at=now, value=1, unit="count",
            factual_statement=identifier, evidence_ids=[f"ev-{identifier}"], source_record_ids=[identifier],
            collection_health="healthy", derivative_group=group)
    careers = observation("careers", "careers_ats", "careers")
    procurement = observation("procurement", "contracts_procurement", "procurement")
    duplicate = observation("duplicate", "careers_ats", "careers")
    assert assess_corroboration([careers, procurement]).status == "INDEPENDENT"
    duplicated = assess_corroboration([careers, duplicate])
    assert duplicated.status == "DUPLICATE_ONLY" and duplicated.duplicate_observation_count == 1
    contradictory = assess_corroboration([careers, procurement], contradicting_observation_ids=["procurement"])
    assert contradictory.status == "CONTRADICTORY"


def test_future_evidence_and_single_snapshot_do_not_create_candidate() -> None:
    cutoff = datetime(2026, 1, 2, tzinfo=UTC)
    snapshots = _snapshots([100, 50], start=datetime(2026, 1, 1, tzinfo=UTC))
    adapted = CareersConditionAdapter().adapt(
        company_id="company-alpha", entity_scope="company-alpha",
        analysis_cutoff=cutoff, snapshots=snapshots)
    assert len(adapted.observations) == 1
    assert adapted.candidates == []


def test_adapter_does_not_turn_missing_or_unchanged_data_into_health() -> None:
    adapter = CareersConditionAdapter()
    cutoff = datetime(2026, 2, 1, tzinfo=UTC)
    empty = adapter.adapt(company_id="company-alpha", entity_scope="company-alpha",
        analysis_cutoff=cutoff, snapshots=[])
    unchanged = adapter.adapt(company_id="company-alpha", entity_scope="company-alpha",
        analysis_cutoff=cutoff, snapshots=_snapshots([100, 100]))
    assert empty.candidates == [] and unchanged.candidates == []
    assert empty.unsupported_features and unchanged.unsupported_features


def test_unknown_evidence_reference_fails_qualification() -> None:
    adapted, _ = _qualify([100, 80, 60, 40])
    result = ConditionQualificationEngine().qualify(
        adapted.candidates[0], observations=adapted.observations, valid_evidence_ids=set())
    assert result.qualification_status == "INSUFFICIENT_EVIDENCE"
    assert "references" in result.failed_tests


def _procurement_record(month: int, sequence: int) -> ProcurementRecord:
    record_id = f"proc-{month}-{sequence}"
    return ProcurementRecord(
        source_record_id=record_id, source_family="contracts_procurement", notice_id=record_id,
        publication_date=f"2026-{month:02d}-10T00:00:00+00:00", buyer="Buyer",
        supplier_raw_name="Alpha Industries", value=1000.0, currency="GBP", category="services",
        description="Service award", status="active", contract_start=None, contract_end=None,
        source_url=f"https://example.test/{record_id}", raw_payload={"id": record_id},
        content_hash=(f"{sequence}{month}" * 64)[:64])


def test_non_careers_procurement_adapter_uses_same_qualification_core() -> None:
    records = [_procurement_record(month, sequence)
               for month in range(1, 5) for sequence in range(1, month + 1)]
    cutoff = datetime(2026, 5, 1, tzinfo=UTC)
    adapted = ProcurementConditionAdapter().adapt(
        company_id="company-alpha", entity_scope="company-alpha", analysis_cutoff=cutoff,
        records=records, approved_entity=True)
    assert adapted.candidates[0].candidate_type == "procurement_activity_acceleration"
    result = ConditionQualificationEngine().qualify(adapted.candidates[0],
        observations=adapted.observations,
        valid_evidence_ids={value for item in adapted.observations for value in item.evidence_ids})
    assert result.qualification_status == "QUALIFIED"
    assert result.dimensions == ["Demand & Growth", "Change & Execution"]


def test_procurement_without_approved_entity_resolution_is_unsupported() -> None:
    adapted = ProcurementConditionAdapter().adapt(
        company_id="company-alpha", entity_scope="company-alpha",
        analysis_cutoff=datetime(2026, 5, 1, tzinfo=UTC),
        records=[_procurement_record(1, 1)], approved_entity=False)
    assert adapted.observations == [] and adapted.candidates == []
    assert "entity resolution" in adapted.unsupported_features[0]
