import csv
import hashlib
import json
from pathlib import Path

from evidence_engine_v0_3_2.events import (
    classify_evidence_structure,
    extract_event_pipeline,
    is_malformed_fragment,
)

ROOT = Path(__file__).resolve().parents[1]


def _pipeline(text: str, period: str = "2024-12-31") -> dict:
    return extract_event_pipeline(text, publication_date="2025-02-01", reporting_period=period)


def test_current_and_comparative_table_columns_are_bound_explicitly():
    structure = classify_evidence_structure(
        "Restructuring costs (millions of dollars) 2024 24 2023 18", "2024-12-31"
    )
    assert structure.structure_type == "table_row"
    assert structure.period_binding == "current_and_comparative"


def test_comparative_only_table_is_not_current():
    structure = classify_evidence_structure("Restructuring costs 2022 18 2021 25", "2024-12-31")
    assert structure.period_binding == "comparative_period"


def test_historical_restructuring_charge_is_rejected_as_event():
    result = _pipeline("Charges related to the 2022 restructuring programme were $18 million.")
    assert result["accepted_events"] == []


def test_current_charge_is_preserved_as_accounting_observation_not_event():
    result = _pipeline("Restructuring charges for 2024 were $24 million.")
    assert result["accepted_events"] == []
    assert result["accounting_observations"]
    assert result["accounting_observations"][0]["operational_event_promoted"] is False


def test_completed_historical_programme_is_not_promoted():
    assert not _pipeline("The restructuring programme was completed in the prior year.")["accepted_events"]


def test_current_programme_is_accepted():
    events = _pipeline("During 2024 we initiated a restructuring programme.")["accepted_events"]
    assert len(events) == 1
    assert events[0]["event_status"] == "current"


def test_current_table_charge_needs_narrative_operational_support():
    text = "During 2024 we initiated a site closure. Restructuring charges for 2024 were $24 million."
    result = _pipeline(text)
    assert any(event["event_type"] == "site_closure" for event in result["accepted_events"])
    assert not any(event["event_type"] == "restructuring" for event in result["accepted_events"])


def test_table_footnote_is_typed_and_not_promoted():
    text = "1 Represents restructuring costs included in operating expenses for 2024."
    result = _pipeline(text)
    candidate = next(item for item in result["candidates"] if item["event_type"] == "restructuring")
    assert candidate["structure_type"] == "table_footnote"
    assert result["accepted_events"] == []


def test_malformed_broken_row_is_detected():
    span = "2024 2023 24 (18 9 7 Restructuring GAAP Adjusted"
    assert is_malformed_fragment(span)
    assert _pipeline(span)["accepted_events"] == []


def test_repeated_table_heading_is_detected():
    span = "2024 2023 GAAP Adjusted Restructuring 2024 2023 Table of Contents"
    assert is_malformed_fragment(span)


def test_negative_bracketed_accounting_row_is_not_operational_event():
    result = _pipeline("Restructuring charges (24) 18")
    assert result["accepted_events"] == []


def test_table_cell_provenance_keeps_row_value_and_context():
    result = _pipeline("Restructuring charges for 2024 were $24 million.")
    provenance = result["accounting_observations"][0]
    assert provenance["metric_label"].lower().startswith("restructuring charge")
    assert provenance["reported_value"] is not None
    assert provenance["source_span"] == "Restructuring charges for 2024 were $24 million."


def test_v031_context_behaviour_does_not_regress():
    assert not _pipeline("No restructuring is planned.")["accepted_events"]
    assert not _pipeline("Supply disruption may occur if a vendor fails.")["accepted_events"]
    assert not _pipeline("She led restructuring programmes at previous employers.")["accepted_events"]
    events = _pipeline("The strike paused production at our facility.")["accepted_events"]
    assert {event["event_type"] for event in events} == {"labour_constraint", "operational_disruption"}


def test_v032_benchmark_is_frozen_and_development_only():
    path = ROOT / "data/evidence_engine_v0_3_2/table_historical_regression_cases.csv"
    manifest = json.loads((ROOT / "data/evidence_engine_v0_3_2/table_historical_regression_cases.freeze.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["sha256"]
    rows = list(csv.DictReader(path.open()))
    assert len(rows) == 35
    assert all(row["formal_gold"] == "false" for row in rows)
    assert all(row["admissible_for_model2_gate"] == "false" for row in rows)
