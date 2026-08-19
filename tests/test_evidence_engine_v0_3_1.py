import csv
import hashlib
import json
from pathlib import Path

import pytest

from evidence_engine_v0_3_1.events import extract_event_pipeline
from evidence_engine_v0_3_1.numerical import canonicalize_numeric

ROOT = Path(__file__).resolve().parents[1]


def _one(text, **kwargs):
    return extract_event_pipeline(text, reporting_period="2024", **kwargs)


@pytest.mark.parametrize(
    ("text", "expected", "status"),
    [
        ("We are reducing operating costs across the Group.", 1, "current"),
        ("We plan to reduce the size of our workforce.", 1, "planned"),
        ("The restructuring was completed in 2021.", 0, None),
        ("No restructuring is planned.", 0, None),
        ("Supply disruption may occur if a vendor fails.", 0, None),
        ("She led restructuring programmes at previous employers.", 0, None),
        ("A supplier closed its facility.", 0, None),
    ],
)
def test_context_statuses(text, expected, status):
    result = _one(text)
    assert len(result["accepted_events"]) == expected
    if expected:
        assert result["accepted_events"][0]["event_status"] == status


def test_scope_and_provenance_are_retained():
    text = "Our Aviation segment reduced capacity at the Belfast facility."
    result = _one(text)
    event = result["accepted_events"][0]
    assert event["scope"] in {"segment_or_geography", "facility"}
    assert event["source_span"] == text


def test_multi_label_strike_is_atomic_not_synonym_duplication():
    result = _one("The strike paused production at our facility.")
    assert {e["event_type"] for e in result["accepted_events"]} == {
        "labour_constraint", "operational_disruption"
    }


def test_duplicate_wording_is_suppressed():
    text = "We announced a restructuring programme. We announced a restructuring program."
    result = _one(text)
    assert len(result["accepted_events"]) == 1
    assert len(result["deduplication_links"]) == 1


def test_current_condition_in_risk_section_is_not_blindly_excluded():
    text = "Risk factors. We have experienced supply chain disruption that slowed production."
    result = _one(text)
    assert {e["event_type"] for e in result["accepted_events"]} >= {
        "supply_chain_constraint"
    }


def test_capex_preserves_reported_sign_and_normalizes_magnitude():
    value = canonicalize_numeric("capex", -125.0, "company_defined")
    assert value.reported_value == -125.0
    assert value.normalized_value == 125.0
    assert value.normalization == "absolute economic expenditure magnitude; reported sign preserved separately"


def test_accounting_basis_must_not_be_invented():
    assert canonicalize_numeric("ebitda", 10, None).accounting_basis == "unclear"
    with pytest.raises(ValueError):
        canonicalize_numeric("ebitda", 10, "guessed_statutory")


def test_development_benchmark_is_frozen_and_not_formal_gold():
    manifest = json.loads((ROOT / "data/evidence_engine_v0_3_1/event_context_regression_cases.freeze.json").read_text())
    path = ROOT / "data/evidence_engine_v0_3_1/event_context_regression_cases.csv"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["sha256"]
    rows = list(csv.DictReader(path.open()))
    assert rows and all(row["formal_gold"].lower() == "false" for row in rows)
    assert all(row["admissible_for_model2_gate"].lower() == "false" for row in rows)


def test_repaired_albemarle_pdf_is_additive_and_original_is_preserved():
    original = ROOT / "output/pdf/evidence_engine_v0_3/ee03-alb-0000915913-24-000156.pdf"
    repaired = ROOT / "output/pdf/evidence_engine_v0_3_1/ee03-alb-0000915913-24-000156-complete.pdf"
    assert hashlib.sha256(original.read_bytes()).hexdigest() == "050f39c61a73b5bc5fa136b294d3752cfabe074226c5a3672017b138e94dca19"
    assert repaired.exists() and repaired.read_bytes() != original.read_bytes()
