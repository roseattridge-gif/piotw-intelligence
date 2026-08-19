from __future__ import annotations

from collections import Counter

from evidence_engine_v0_1.models import Event, Observation


def evaluate_extraction(observations: list[Observation], events: list[Event], gold: dict) -> dict:
    numeric_expected = 0
    numeric_correct = 0
    missing = 0
    for key, expected in gold["numeric"].items():
        company, period = key
        actual = {o.observation_type: o.value for o in observations
                  if o.company_id == company and o.reporting_period == period
                  and isinstance(o.value, (int, float))}
        numeric_expected += len(expected)
        for metric, value in expected.items():
            if metric not in actual:
                missing += 1
            elif abs(float(actual[metric]) - value) < 1e-9:
                numeric_correct += 1
    expected_events = 0
    correct_events = 0
    event_keys = {(e.company_id, e.reporting_period, e.event_type) for e in events}
    for (company, period), types in gold["events"].items():
        expected_events += len(types)
        correct_events += sum((company, period, event_type) in event_keys for event_type in types)
    event_fingerprints = Counter(e.event_id for e in events)
    reviewed = [o for o in observations if o.validation_status in {"accepted", "corrected", "rejected"}]
    return {
        "corpus_kind": "synthetic_gold_fixture",
        "companies": len({o.company_id for o in observations}),
        "reports": len({o.source_evidence_id for o in observations}),
        "numerical_expected": numeric_expected,
        "numerical_extraction_accuracy": numeric_correct / numeric_expected if numeric_expected else None,
        "event_expected": expected_events,
        "event_classification_recall": correct_events / expected_events if expected_events else None,
        "reviewer_correction_rate": sum(o.validation_status == "corrected" for o in reviewed) / len(reviewed) if reviewed else None,
        "missing_value_rate": missing / numeric_expected if numeric_expected else None,
        "duplicate_event_rate": sum(count - 1 for count in event_fingerprints.values()) / len(events) if events else 0,
        "provenance_completeness": sum(bool(o.source_evidence_id and o.evidence_span and o.page_or_section) for o in observations) / len(observations),
        "exact_evidence_span_rate": sum(bool(o.evidence_span.strip()) for o in observations) / len(observations),
        "warning": "Fixture accuracy measures deterministic plumbing only; it is not real-report accuracy.",
    }

