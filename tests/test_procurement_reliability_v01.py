from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from piotw_evidence.families_v01 import EvidenceFamilyRecord, ProcurementFamilyAdapter
from piotw_evidence.procurement_reliability_v01 import (
    ReliabilityAwardRecord,
    deduplicate_awards,
    enforce_feature_roles,
    evaluate_negative_controls,
    procurement_coverage_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]


def award(identifier: str, year: int, underlying: str, *, buyer: str = "Buyer A",
          category: str | None = "technology", value: float | None = 100.0,
          exact: bool = True) -> ReliabilityAwardRecord:
    return ReliabilityAwardRecord(
        source_record_id=identifier, company_id="example", legal_name="Example Limited",
        company_number="01234567", publication_year=year, buyer=buyer, category=category,
        value=value, currency="GBP" if value is not None else None,
        underlying_award_id=underlying, source_url=f"https://example.test/{identifier}",
        source_hash=hashlib.sha256(identifier.encode()).hexdigest(), exact_identifier=exact,
    )


def family_record(identifier: str, when: str, *, underlying: str, buyer: str = "Buyer A") -> EvidenceFamilyRecord:
    timestamp = datetime.fromisoformat(when)
    return EvidenceFamilyRecord(
        source_record_id=identifier, family_id="contracts_procurement", company_id="example",
        entity_scope="example", publication_or_effective_at=timestamp,
        source_published_at=timestamp, retrieved_at=timestamp, source_url=f"https://example.test/{identifier}",
        source_hash=hashlib.sha256(identifier.encode()).hexdigest(), evidence_span="Exact supplier award.",
        collector_or_parser_version="test", record_type="award_notice", legal_entity_identifier="01234567",
        entity_resolution_method="exact_legal_name_and_company_number_in_primary_notice",
        entity_resolution_confidence="HIGH", values={
            "entity_resolution": "APPROVED", "award_value": 100.0, "currency": "GBP",
            "category": "technology", "buyer": buyer, "comparison_period": str(timestamp.year),
            "source_policy_id": "piotw-procurement-source-policy-find-a-tender-v0.1-development",
            "notice_type": "contract_award_notice", "underlying_award_id": underlying,
        },
    )


def test_exact_entity_resolution_and_underlying_award_deduplication():
    rows = [award("v1", 2024, "same"), award("v2", 2025, "same"), award("other", 2025, "other")]
    retained, lineage = deduplicate_awards(rows)
    assert len(retained) == 2
    assert lineage["example:same"] == ["v1", "v2"]
    diagnostics = procurement_coverage_diagnostics(rows, start_year=2024, end_year=2025)
    assert diagnostics["notice_versions_removed"] == 1
    assert diagnostics["exact_legal_entity_resolution_rate"] == 1.0


def test_publication_period_buyer_category_value_and_missingness_diagnostics():
    rows = [
        award("a", 2021, "a", buyer="Buyer A", category="technology", value=100),
        award("b", 2021, "b", buyer="Buyer A", category=None, value=None),
        award("c", 2023, "c", buyer="Buyer B", category="facilities", value=900),
    ]
    result = procurement_coverage_diagnostics(rows, start_year=2021, end_year=2023)
    assert result["award_count_by_period"] == {"2021": 2, "2022": None, "2023": 1}
    assert result["periods_without_records"] == [2022]
    assert result["buyer_count"] == 2
    assert result["category_mix"] == {"technology": 1, "unknown": 1, "facilities": 1}
    assert result["usable_value_count"] == 2
    assert result["usable_value_proportion"] == 2 / 3
    assert "not zero activity" in result["missingness_rule"]


def test_negative_controls_detect_concentration_versions_missing_values_and_dominance():
    rows = [
        award("a", 2021, "same", value=1000),
        award("a2", 2022, "same", value=1000),
        award("b", 2022, "b", value=None),
        award("c", 2022, "c", value=None),
        award("d", 2023, "d", value=None),
    ]
    controls = evaluate_negative_controls(procurement_coverage_diagnostics(rows, start_year=2021, end_year=2023))
    assert controls["one_buyer_repeated_publication"]
    assert controls["multiple_notice_versions_one_award"]
    assert controls["mostly_missing_values"]
    assert controls["one_large_award_dominates_period"]


def test_feature_roles_fail_closed_for_retired_factual_and_corroboration_only_features():
    roles = json.loads((ROOT / "config/conditions/procurement_feature_role_policy_v0_1.json").read_text())["roles"]
    features = {name: {"observed": True} for name in roles}
    alone = enforce_feature_roles(features, roles, external_candidate_present=False)
    assert not alone["may_emit_independent_condition"]
    assert alone["corroborating_features"] == []
    assert alone["retired_features"] == ["raw_award_count"]
    with_external = enforce_feature_roles(features, roles, external_candidate_present=True)
    assert set(with_external["corroborating_features"]) == {
        "buyer_breadth", "award_category_mix", "new_strategic_relationship", "persistent_procurement_theme"
    }
    assert set(with_external["factual_only_features"]) == {
        "disclosed_contract_value", "supplier_concentration_diversification"
    }


def test_procurement_adapter_preserves_facts_but_emits_no_retired_count_condition_and_is_cutoff_safe():
    records = [
        family_record("a", "2022-01-01T00:00:00+00:00", underlying="a"),
        family_record("b", "2023-01-01T00:00:00+00:00", underlying="b"),
        family_record("c", "2024-01-01T00:00:00+00:00", underlying="c", buyer="Buyer B"),
        family_record("future", "2027-01-01T00:00:00+00:00", underlying="future"),
    ]
    envelope = ProcurementFamilyAdapter().adapt(
        company_id="example", entity_scope="example",
        analysis_cutoff=datetime(2025, 1, 1, tzinfo=UTC), records=records,
    )
    assert len(envelope.observations) == 3
    assert "future" not in envelope.raw_evidence_references
    assert envelope.candidates == []
    assert not envelope.coverage.qualification_ready
    assert envelope.longitudinal_features["role_enforcement"]["retired_features"] == ["raw_award_count"]
    assert envelope.longitudinal_features["buyer_breadth"] == 2
