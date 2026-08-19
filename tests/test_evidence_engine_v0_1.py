from __future__ import annotations

import json
from datetime import UTC, date, datetime

import pytest

from evidence_engine_v0_1.collectors import (
    Collector,
    FixtureJobsCollector,
    FixtureReportCollector,
    LocalReportCollector,
    jobs_from_raw,
)
from evidence_engine_v0_1.definitions import feature_definition_catalog
from evidence_engine_v0_1.features import calculate_longitudinal_features, eligible_observations
from evidence_engine_v0_1.fixtures import development_corpus, job_snapshots
from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_1.jobs import calculate_job_features, deduplicate_jobs
from evidence_engine_v0_1.models import ReviewDecision
from evidence_engine_v0_1.parsing import (
    extract_financial_observations,
    parse_numeric,
    parse_percentage,
)
from evidence_engine_v0_1.pipeline import run_demo
from evidence_engine_v0_1.review import apply_review
from evidence_engine_v0_1.taxonomy import (
    extract_language_observations,
    load_taxonomy,
    observations_to_events,
)

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
def collected_evidence(tmp_path):
    rows, _ = development_corpus()
    return FixtureReportCollector(rows, tmp_path).collect("synthetic-01", date(2025, 12, 31))


def accepted(observations):
    return [o.model_copy(update={"validation_status": "accepted"}) for o in observations]


def extract_all(evidence):
    return [observation for item in evidence for observation in extract_financial_observations(item)]


def test_observation_provenance_is_complete(tmp_path):
    evidence = collected_evidence(tmp_path)[0]
    observation = extract_financial_observations(evidence)[0]
    assert observation.source_evidence_id == evidence.evidence_id
    assert observation.evidence_span in evidence.raw_text
    assert observation.page_or_section


@pytest.mark.parametrize(("text", "value", "currency", "unit"), [
    ("GBP 1.2 billion", 1200, "GBP", "million"),
    ("£45.5m", 45.5, "GBP", "million"),
    ("USD 200 million", 200, "USD", "million"),
    ("12.4 percent", 12.4, None, "percent"),
    ("2.1x", 2.1, None, "times"),
])
def test_financial_value_and_currency_parsing(text, value, currency, unit):
    assert parse_numeric(text) == (value, currency, unit)


def test_percentage_parsing():
    assert parse_percentage("margin was 8.75%") == 8.75
    with pytest.raises(ValueError):
        parse_percentage("not disclosed")


def test_period_matching_and_basis_point_calculation(tmp_path):
    evidence = collected_evidence(tmp_path)
    observations = accepted(extract_all(evidence))
    features = calculate_longitudinal_features("synthetic-01", observations, [], date(2025, 12, 31))
    margin = next(f for f in features if f.feature_id == "operating_margin_change_bps")
    assert margin.value == -110
    assert len(margin.input_observation_ids) == 2
    assert len(margin.evidence_ids) == 2


def test_missing_data_yields_no_feature(tmp_path):
    evidence = collected_evidence(tmp_path)[0]
    observations = accepted(extract_financial_observations(evidence))
    features = calculate_longitudinal_features("synthetic-01", observations, [], date(2024, 12, 31))
    assert not any(f.feature_id == "operating_margin_change_bps" for f in features)


def test_future_evidence_is_excluded_from_historical_snapshot(tmp_path):
    evidence = collected_evidence(tmp_path)
    observations = accepted(extract_all(evidence))
    cutoff = date(2024, 12, 31)
    assert all(o.information_available_at.date() <= cutoff for o in eligible_observations(observations, cutoff))
    assert not any(o.reporting_period == "FY2024" for o in eligible_observations(observations, cutoff))


def test_language_taxonomy_and_duplicate_events(tmp_path):
    taxonomy = load_taxonomy(ROOT / "config/evidence/event_taxonomy_v0_1.yaml")
    evidence = collected_evidence(tmp_path)[1]
    observations = accepted(extract_language_observations(evidence, taxonomy))
    events = observations_to_events(observations + observations, taxonomy)
    assert {e.event_type for e in events} >= {"cost_reduction", "demand_weakness"}
    assert len({e.event_id for e in events}) == len(events)


def test_every_generated_feature_has_a_versioned_definition(tmp_path):
    taxonomy = load_taxonomy(ROOT / "config/evidence/event_taxonomy_v0_1.yaml")
    catalog = {definition.feature_id for definition in feature_definition_catalog(taxonomy)}
    evidence = collected_evidence(tmp_path)
    observations = accepted(extract_all(evidence))
    report_features = calculate_longitudinal_features(
        "synthetic-01", observations, [], date(2025, 12, 31))
    previous, current = job_snapshots()
    job_features = calculate_job_features(
        "synthetic-01", current, previous, date(2025, 12, 31))
    assert {feature.feature_id for feature in report_features + job_features} <= catalog


def test_review_accept_correct_reject_workflow(tmp_path):
    observation = extract_financial_observations(collected_evidence(tmp_path)[0])[0]
    now = datetime.now(UTC)
    corrected = apply_review(observation, ReviewDecision(decision_id="d1", observation_id=observation.observation_id,
        decision="correct", reviewer="tester", decided_at=now, corrected_value=999, corrected_unit="million"))
    rejected = apply_review(observation, ReviewDecision(decision_id="d2", observation_id=observation.observation_id,
        decision="reject", reviewer="tester", decided_at=now))
    assert (corrected.value, corrected.validation_status) == (999, "corrected")
    assert rejected.validation_status == "rejected"


def test_collector_interface_and_cutoff(tmp_path):
    collector = FixtureReportCollector(development_corpus()[0], tmp_path)
    assert isinstance(collector, Collector)
    assert [e.reporting_period for e in collector.collect("synthetic-01", date(2024, 12, 31))] == ["FY2023"]


def test_local_report_collector_supports_report_family(tmp_path):
    report = tmp_path / "interim.txt"
    report.write_text("Revenue: GBP 10 million")
    manifest = [{"evidence_id": "local-1", "company_id": "acme", "source_type": "interim_report",
        "source_title": "Acme interim", "source_url": "fixture://acme/interim", "reporting_period": "H1 2024",
        "publication_date": "2024-08-01", "period_end": "2024-06-30",
        "collected_at": "2024-08-02T00:00:00+00:00", "information_available_at": "2024-08-01T07:00:00+00:00",
        "path": str(report), "mime_type": "text/plain"}]
    evidence = LocalReportCollector(manifest).collect("acme", date(2024, 12, 31))
    assert evidence[0].source_type == "interim_report"
    assert extract_financial_observations(evidence[0])[0].value == 10


def test_jobs_collector_uses_common_raw_evidence_contract(tmp_path):
    previous, current = job_snapshots()
    collector = FixtureJobsCollector([(previous[0].collected_at, previous),
                                      (current[0].collected_at, current)], tmp_path)
    evidence = collector.collect("synthetic-01", date(2024, 10, 1))
    assert isinstance(collector, Collector)
    assert len(evidence) == 1
    assert jobs_from_raw(evidence[0])[0].company_id == "synthetic-01"


def test_job_deduplication_first_and_last_seen():
    previous, current = job_snapshots()
    duplicate = current[0].model_copy(update={"first_seen": previous[0].first_seen})
    deduped = deduplicate_jobs([current[0], duplicate])
    assert len(deduped) == 1
    assert deduped[0].first_seen == previous[0].first_seen
    assert deduped[0].last_seen == current[0].last_seen


def test_job_features_are_observational_not_interpretive():
    previous, current = job_snapshots()
    features = {f.feature_id: f.value for f in calculate_job_features("synthetic-01", current, previous, date(2024, 12, 31))}
    assert features["open_vacancy_count"] == 4
    assert features["vacancy_count_change"] == -2
    assert features["ai_data_hiring_count"] == 2
    assert "pressure" not in features


def test_feature_reproducibility(tmp_path):
    evidence = collected_evidence(tmp_path)
    observations = accepted(extract_all(evidence))
    one = calculate_longitudinal_features("synthetic-01", observations, [], date(2025, 12, 31))
    two = calculate_longitudinal_features("synthetic-01", observations, [], date(2025, 12, 31))
    assert [(f.feature_snapshot_id, f.feature_id, f.value, f.evidence_ids) for f in one] == [(f.feature_snapshot_id, f.feature_id, f.value, f.evidence_ids) for f in two]


def test_frozen_rules_guard_and_demo_isolation(tmp_path):
    before = verify_frozen_isolation(ROOT)
    run_demo(ROOT, tmp_path / "demo.json")
    after = verify_frozen_isolation(ROOT)
    assert before == after
    payload = json.loads((tmp_path / "demo.json").read_text())
    assert payload["outcomes_used"] is False
    assert payload["predictive_model_trained"] is False
    assert payload["frozen_guard_file_count"] == 12


def test_guard_detects_changed_copy(tmp_path):
    guard = json.loads((ROOT / "config/evidence/frozen_rules_1_0_0_guard.json").read_text())
    (tmp_path / "config/evidence").mkdir(parents=True)
    (tmp_path / "config/frozen").mkdir(parents=True)
    (tmp_path / "config/evidence/frozen_rules_1_0_0_guard.json").write_text(json.dumps(guard))
    (tmp_path / "config/frozen/restructuring_v2_lock.json").write_text((ROOT / "config/frozen/restructuring_v2_lock.json").read_text())
    for relative in guard["files"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    protected = tmp_path / "config/models/restructuring_rules_1_0_0.json"
    protected.write_text(protected.read_text() + "\n")
    with pytest.raises(RuntimeError, match="frozen Rules"):
        verify_frozen_isolation(tmp_path)
