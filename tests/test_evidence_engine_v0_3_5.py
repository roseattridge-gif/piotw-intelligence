from pathlib import Path

import yaml

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_3_4.evidence_pointer import (
    build_evidence_pointer_mapping,
    evidence_pointer_id,
    resolve_evidence_pointer,
)
from evidence_engine_v0_3_4.semantic import SemanticCandidate
from evidence_engine_v0_3_5.semantic import (
    DeterministicSemanticVerifierV035,
    evidence_sufficiency,
    polarity_for,
)

ROOT = Path(__file__).resolve().parents[1]


def candidate(span: str, event_type: str, *, subject="target_company", status="current", heading="Operations"):
    return SemanticCandidate("Example plc", event_type, span, span, heading, "2026-01-01", {
        "subject_type": subject, "entity_scope": "group", "factual_status": "actual",
        "event_status": status, "allowed_remaps": [],
    })


def test_contaminated_regressions_are_labelled_and_handled():
    data = yaml.safe_load((ROOT / "data/evidence_engine_v0_3_5/semantic_regression_cases.yaml").read_text())
    assert data["status"] == "DEVELOPMENT_CONTAMINATED — NOT VALIDATION"
    verifier = DeterministicSemanticVerifierV035()
    decisions = []
    for row in data["cases"]:
        item = candidate(row["span"], row["event_type"], subject=row["subject_type"])
        decisions.append((row["id"], verifier.verify(item).decision, row["expected"]))
    assert all(actual == expected for _, actual, expected in decisions), decisions


def test_adversarial_factuality_attribution_and_timing():
    verifier = DeterministicSemanticVerifierV035()
    rows = [
        ("The company may close the Leeds site if demand weakens.", "site_closure", "target_company", "reject"),
        ("The company closed the Leeds site during 2025.", "site_closure", "target_company", "accept"),
        ("A competitor closed its Leeds site during 2025.", "site_closure", "competitor", "reject"),
        ("The subsidiary opened a new factory during 2025.", "new_facility", "target_subsidiary", "accept"),
        ("The supplier closed its factory during 2025.", "site_closure", "supplier", "reject"),
        ("An analyst said the company could close a site.", "site_closure", "quoted_third_party", "reject"),
        ("The company initiated a restructuring programme during 2025.", "restructuring", "target_company", "accept"),
        ("Restructuring is defined as qualifying termination activity.", "restructuring", "target_company", "reject"),
    ]
    for span, event_type, subject, expected in rows:
        assert verifier.verify(candidate(span, event_type, subject=subject)).decision == expected


def test_polarity_is_explicit_for_directional_examples():
    examples = {
        "Revenue increased during the year.": "increase_or_improvement",
        "Backlog declined during the year.": "decrease_or_deterioration",
        "Operating margin improved during the year.": "increase_or_improvement",
        "Capacity was reduced during the year.": "decrease_or_deterioration",
        "The company opened a new site during the year.": "increase_or_improvement",
        "Pricing pressure increased during the year.": "mixed",
    }
    for span, expected in examples.items():
        assert polarity_for(candidate(span, "growth_language")) == expected


def test_evidence_sufficiency_requires_target_and_complete_proposition():
    complete = evidence_sufficiency(candidate("The subsidiary reduced capacity during 2025.", "capacity_reduction", subject="target_subsidiary"))
    assert all(complete.values())
    item = candidate("Capacity reduction", "capacity_reduction")
    item = SemanticCandidate(item.target_company, item.candidate_event_type, item.exact_candidate_span,
        item.context, item.heading, item.publication_date, {**item.deterministic_metadata, "event_status": None})
    incomplete = evidence_sufficiency(item)
    assert not incomplete["predicate"] and not incomplete["timing"]


def test_v034_evidence_pointer_transport_is_preserved_and_fail_closed():
    item = candidate("The company closed the Leeds site during 2025.", "site_closure")
    mapping = build_evidence_pointer_mapping(item, "evidence-1")
    pointer = evidence_pointer_id(mapping)
    assert resolve_evidence_pointer(pointer, mapping, item, decision="accept") == item.exact_candidate_span
    try:
        resolve_evidence_pointer("span_unknown", mapping, item, decision="accept")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown pointer must fail closed")


def test_rules_artifacts_unchanged():
    assert len(verify_frozen_isolation(ROOT)) == 12
