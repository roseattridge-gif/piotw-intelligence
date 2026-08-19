import csv
import json
from pathlib import Path

import pytest

from evidence_engine_v0_3_4.semantic import SemanticCandidate
from evidence_engine_v0_3_6.families import (
    FAMILY_BY_EVENT,
    FAMILY_VERIFIERS,
    route_family,
    verify_candidate,
)


def candidate(event_type: str, span: str, subject: str = "target_company") -> SemanticCandidate:
    return SemanticCandidate("Example plc", event_type, span, span, None, "2026-01-01",
        {"subject_type": subject, "entity_scope": "group", "factual_status": "actual_current",
         "event_status": "current", "allowed_remaps": []})


def test_demand_family_rejects_cost_growth_and_accepts_revenue_growth():
    assert verify_candidate(candidate("growth_language", "Cost of sales increased 7% during the period.")).disposition == "reject"
    assert verify_candidate(candidate("growth_language", "Revenue increased 7% during the period.")).disposition == "accept"


def test_restructuring_family_rejects_product_name_and_customer_action():
    name = "Customers selected the PAC-3 Cost Reduction Initiative for missile defence."
    third_party = "Our customer entered restructuring discussions during the quarter."
    assert verify_candidate(candidate("cost_reduction", name)).reason == "programme_or_product_name_only"
    assert verify_candidate(candidate("restructuring", third_party)).reason == "third_party_action"


def test_restructuring_family_accepts_direct_target_action():
    result = verify_candidate(candidate("restructuring",
        "We announced a restructuring programme during the quarter."))
    assert result.disposition == "accept"


@pytest.mark.parametrize(("event_type", "span", "expected"), [
    ("workforce_reduction", "We announced a reduction of 300 roles during the quarter.", "accept"),
    ("labour_constraint", "A strike disrupted production at our principal plant.", "accept"),
    ("hiring", "The group is recruiting engineers for its UK operations.", "accept"),
    ("site_closure", "We announced that we will close the Leeds factory.", "accept"),
    ("capacity_expansion", "The group is adding production capacity at its Texas site.", "accept"),
    ("operational_disruption", "Production was paused following the incident.", "accept"),
    ("supply_chain_constraint", "Our production was affected by a component shortage.", "accept"),
    ("destocking", "Our sales were impacted by customer destocking during the period.", "accept"),
    ("recall", "The company initiated a recall of the affected product.", "accept"),
    ("quality_failure", "A quality issue resulted in additional inspection work.", "accept"),
    ("regulatory_intervention", "The regulator ordered the company to suspend production.", "accept"),
    ("transformation", "We launched a business transformation programme this year.", "accept"),
    ("leadership_change", "The company appointed a new Chief Operating Officer.", "accept"),
])
def test_remaining_event_families_accept_direct_factual_evidence(event_type, span, expected):
    result = verify_candidate(candidate(event_type, span))
    assert result.disposition == expected
    assert result.evidence_span == span


@pytest.mark.parametrize(("event_type", "span", "subject", "reason"), [
    ("site_closure", "A competitor closed its factory.", "third_party", "wrong_entity"),
    ("site_closure", "There is a risk of site closure.", "target_company", "hypothetical_only"),
    ("recall", "The company did not initiate a product recall.", "target_company", "negated_event"),
    ("transformation", "Her biography says she led transformation at a previous employer.",
     "target_company", "biography_or_prior_employer"),
    ("supply_chain_constraint", "Supply disruption could adversely affect production.",
     "target_company", "hypothetical_only"),
])
def test_family_safety_contracts_reject_non_events(event_type, span, subject, reason):
    assert verify_candidate(candidate(event_type, span, subject)).reason == reason


def test_router_covers_all_seven_families_and_fails_closed_for_unknown_event():
    assert len(FAMILY_VERIFIERS) == 7
    assert route_family("quality_failure") == "quality_regulatory"
    result = verify_candidate(candidate("unmapped_future_event", "We changed something."))
    assert result.disposition == "ambiguous" and result.reason == "family_not_implemented"


def test_restructuring_contract_handles_indirect_action_and_accounting_only_reference():
    indirect = verify_candidate(candidate("cost_reduction", "We reduced the cost base during the year."))
    accounting = verify_candidate(candidate("restructuring", "The restructuring provision is defined as follows."))
    assert indirect.disposition == "accept"
    assert accounting.disposition == "ambiguous"


def test_machine_readable_contract_matches_implemented_router():
    contract = json.loads(Path("config/evidence/event_family_contracts_v0_3_6.json").read_text())
    assert set(contract["families"]) == set(FAMILY_VERIFIERS)
    configured_events = {event for row in contract["families"].values() for event in row["events"]}
    assert configured_events == set(FAMILY_BY_EVENT)
    assert contract["unknown_family_behavior"] == "AMBIGUOUS_FAIL_CLOSED"
    assert contract["fresh_validation_performed"] is False


def test_expanded_family_development_corpus_matches_declared_contracts():
    corpus = json.loads(Path("data/evidence_engine_v0_3_6/family_development_cases.json").read_text())
    assert corpus["status"] == "DEVELOPMENT_SYNTHETIC_NOT_VALIDATION"
    assert len(corpus["cases"]) == 69
    for row in corpus["cases"]:
        metadata = {"subject_type": row["subject"], "entity_scope": "group",
                    "factual_status": "actual_current", "event_status": "current",
                    "allowed_remaps": [], "heading_only": row.get("heading_only", False),
                    "accounting_table_only": row.get("accounting_table_only", False)}
        item = SemanticCandidate("Example plc", row["event_type"], row["span"], row["span"],
                                 None, "2026-01-01", metadata)
        result = verify_candidate(item)
        assert result.family == row["family"], row["id"]
        assert result.disposition == row["expected"], f"{row['id']}: {result.reason}"
        assert result.evidence_span == row["span"]


def test_final_hardening_and_cross_family_cases_match_declared_meaning():
    corpus = json.loads(Path("data/evidence_engine_v0_3_6/final_hardening_cases.json").read_text())
    assert corpus["status"] == "DEVELOPMENT_SYNTHETIC_NOT_VALIDATION"
    assert len(corpus["cases"]) >= 48
    for row in corpus["cases"]:
        metadata = {
            "subject_type": row["subject"],
            "entity_scope": "group",
            "factual_status": "actual_current",
            "event_status": "current",
            "allowed_remaps": [],
            "heading_only": row.get("heading_only", False),
            "accounting_table_only": row.get("accounting_table_only", False),
        }
        item = SemanticCandidate(
            "Example plc", row["event_type"], row["span"], row["span"], None, "2026-01-01", metadata
        )
        result = verify_candidate(item)
        assert result.family == row["family"], row["id"]
        assert result.disposition == row["expected"], f"{row['id']}: {result.reason}"
        assert result.evidence_span == row["span"]


def test_cross_family_cases_preserve_atomic_routes_without_duplicate_observations():
    corpus = json.loads(Path("data/evidence_engine_v0_3_6/final_hardening_cases.json").read_text())
    cross = [row for row in corpus["cases"] if row["adversary"] == "cross_family"]
    spans = {row["span"] for row in cross}
    assert len(cross) == 12 and len(spans) == 6
    for span in spans:
        rows = [row for row in cross if row["span"] == span]
        assert len(rows) == 2
        assert len({row["event_type"] for row in rows}) == 2
        # The source span is one immutable observation; routing may support two
        # genuinely distinct atomic events without copying or rewriting evidence.
        assert {row["span"] for row in rows} == {span}


def test_known_failure_register_is_complete_resolved_and_development_only():
    with Path("data/derived/evidence_engine_v0_3_6_known_failure_register.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 20
    assert {row["failure_type"] for row in rows} == {"false_accept", "missed_supported"}
    assert all(row["resolved"] == "true" for row in rows)
    assert all(row["formal_gold"] == "false" for row in rows)
    assert all(row["contamination_status"] == "DEVELOPMENT_CONTAMINATED_NOT_VALIDATION" for row in rows)
    required = {
        "family", "candidate_event_type", "expected_classification", "pre_hardening_actual",
        "post_hardening_actual", "evidence_span", "surrounding_context", "target_entity",
        "polarity", "temporal_status", "failure_type", "root_cause",
        "deterministic_shared_logic_relevant", "family_specific_logic_relevant",
        "source_extraction_relevant", "proposed_general_fix", "overfitting_risk",
        "regression_test_id",
    }
    assert required <= set(rows[0])
