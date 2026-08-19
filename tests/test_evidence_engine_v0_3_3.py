import csv
import hashlib
import json
from pathlib import Path

from evidence_engine_v0_3_3.events import attribute_subject, extract_event_pipeline

ROOT = Path(__file__).resolve().parents[1]


def _events(text: str) -> list[dict]:
    return extract_event_pipeline(text, publication_date="2025-02-01",
                                  reporting_period="2024-12-31")["accepted_events"]


def test_supplier_condition_is_not_target_company_event():
    assert not _events("Our suppliers experienced labour shortages.")


def test_supplier_cause_and_company_impact_are_separated():
    events = _events("Supplier labor shortages caused production disruption affecting our production.")
    assert {event["event_type"] for event in events} == {"operational_disruption"}
    assert events[0]["subject_type"] == "target_company"


def test_customer_condition_is_external_without_company_impact():
    assert not _events("Our customers faced weak demand.")


def test_customer_destocking_with_explicit_impact_is_target_relevant():
    events = _events("Customer destocking caused weak demand and reduced our sales volume by 18%.")
    assert events and all(event["subject_type"] == "target_company" for event in events)


def test_competitor_and_industry_events_are_external():
    assert not _events("Our competitors announced capacity expansion.")
    assert not _events("The semiconductor industry experienced weak demand.")


def test_biography_and_third_party_quote_are_rejected():
    assert not _events("She previously led a restructuring programme at Company X.")
    assert not _events("According to analysts, weak demand could continue.")


def test_acquisition_target_and_joint_venture_have_explicit_subject_types():
    assert attribute_subject("The acquisition target plans a site closure.").subject_type == "acquisition_target"
    assert attribute_subject("Our joint venture announced capacity expansion.").subject_type == "joint_venture"


def test_target_subsidiary_and_segment_scope_are_preserved():
    subsidiary = _events("Our controlled subsidiary initiated a site closure.")[0]
    segment = _events("Our Aviation segment experienced weak demand.")[0]
    assert subsidiary["subject_type"] == "target_subsidiary"
    assert subsidiary["entity_scope"] == "subsidiary"
    assert segment["subject_type"] == "target_segment"
    assert segment["segment_name"].lower() == "aviation"


def test_generic_risk_rejected_but_actual_risk_condition_accepted():
    assert not _events("Risk Factors: We may experience supply chain disruption.")
    actual = _events("Risk Factors: We are currently experiencing supply chain disruption affecting production.")
    assert actual and actual[0]["factual_status"] == "actual_current"


def test_modal_sentence_preserves_embedded_current_fact():
    events = _events("Weak demand could continue after our sales decreased 20% this quarter.")
    assert events and events[0]["factual_status"] == "actual_current_with_forecast"


def test_pronoun_resolution_and_subject_ambiguity():
    assert _events("We experienced supply chain disruption during the quarter.")[0]["subject_type"] == "target_company"
    assert not _events("Weak demand remains a concern.")


def test_entity_benchmark_is_frozen_and_development_only():
    path = ROOT / "data/evidence_engine_v0_3_3/entity_risk_context_regression_cases.csv"
    manifest = json.loads((ROOT / "data/evidence_engine_v0_3_3/entity_risk_context_regression_cases.freeze.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["sha256"]
    rows = list(csv.DictReader(path.open()))
    assert len(rows) == 29
    assert all(row["formal_gold"] == "false" for row in rows)
    assert all(row["admissible_for_model2_gate"] == "false" for row in rows)
