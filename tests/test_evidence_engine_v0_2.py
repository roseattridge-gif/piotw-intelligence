from __future__ import annotations

import csv
import json
from pathlib import Path

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_2.events import context_status, extract_contextual_events
from evidence_engine_v0_2.ixbrl import extract_numeric_facts, primary_facts
from evidence_engine_v0_2.jobs import TrackedJob, normalize_location, update_job_states

ROOT = Path(__file__).resolve().parents[1]


def ix_document(facts: str, *, current_end: str = "2024-12-31") -> str:
    return f"""
    <xbrli:context id="current"><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity>
      <xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>{current_end}</xbrli:endDate></xbrli:period></xbrli:context>
    <xbrli:context id="prior"><xbrli:entity><xbrli:identifier>1</xbrli:identifier></xbrli:entity>
      <xbrli:period><xbrli:startDate>2023-01-01</xbrli:startDate><xbrli:endDate>2023-12-31</xbrli:endDate></xbrli:period></xbrli:context>
    <xbrli:context id="segment"><xbrli:entity><xbrli:identifier>1</xbrli:identifier><xbrli:segment>
      <xbrldi:explicitMember dimension="x:Segment">x:North</xbrldi:explicitMember></xbrli:segment></xbrli:entity>
      <xbrli:period><xbrli:startDate>2024-01-01</xbrli:startDate><xbrli:endDate>{current_end}</xbrli:endDate></xbrli:period></xbrli:context>
    <xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
    {facts}
    """


def fact(name: str, value: str, *, context: str = "current", scale: int = 6,
         sign: str = "", namespace: str = "us-gaap") -> str:
    sign_attr = f' sign="{sign}"' if sign else ""
    return (f'<ix:nonFraction name="{namespace}:{name}" contextRef="{context}" '
            f'unitRef="usd" scale="{scale}"{sign_attr}>{value}</ix:nonFraction>')


def test_adjusted_and_statutory_are_not_confused():
    document = ix_document(fact("OperatingIncomeLoss", "132") +
        fact("AdjustedOperatingIncome", "159", namespace="acme"))
    facts = primary_facts(document, "2024-12-31")
    assert [(item.metric, item.value, item.accounting_basis) for item in facts] == [
        ("operating_profit", 132, "statutory")]


def test_prior_period_and_segment_facts_are_excluded():
    document = ix_document(fact("Revenues", "100") + fact("Revenues", "90", context="prior") +
                           fact("Revenues", "40", context="segment"))
    facts = extract_numeric_facts(document, "2024-12-31")
    assert [(item.value, item.period_end) for item in facts] == [(100, "2024-12-31")]


def test_currency_scale_and_bracketed_negative_values():
    document = ix_document(fact("OperatingIncomeLoss", "(1,250)", scale=3) +
                           fact("Revenues", "2.5", scale=9))
    values = {item.metric: item for item in primary_facts(document, "2024-12-31")}
    assert values["operating_profit"].value == -1.25
    assert values["operating_profit"].sign == -1
    assert values["revenue"].value == 2500
    assert values["revenue"].currency == "USD"


def test_duplicate_narrative_fact_is_suppressed_and_span_retained():
    one = fact("Revenues", "100")
    facts = primary_facts(ix_document(one + one), "2024-12-31")
    assert len(facts) == 1
    assert facts[0].evidence_span == one


def test_event_negation_and_completed_history_are_suppressed():
    text = "No restructuring planned. The transformation programme completed last year. A cost reduction programme began."
    events = extract_contextual_events(text)
    assert [event["event_type"] for event in events] == ["cost_reduction"]
    assert context_status("No restructuring planned", 3) == "negated"
    assert context_status("Restructuring completed last year", 0) == "historical_or_completed"


def test_taxonomy_overlap_preserves_two_atomic_events():
    events = extract_contextual_events("The restructuring included a cost reduction programme across operations.")
    assert {event["event_type"] for event in events} == {"restructuring", "cost_reduction"}


def test_jobs_outage_does_not_close_everything():
    previous = [TrackedJob(str(index), f"Role {index}", "London") for index in range(10)]
    updated, health = update_job_states(previous, [], collection_success=True)
    assert health["reason"] == "suspected_source_outage"
    assert all(job.status == "open" for job in updated)


def test_job_closure_requires_two_healthy_misses():
    previous = [TrackedJob("1", "Engineer", "London")]
    first, health = update_job_states(previous, [], collection_success=True)
    assert health["healthy"] and first[0].status == "open" and first[0].consecutive_misses == 1
    second, _ = update_job_states(first, [], collection_success=True)
    assert second[0].status == "closed"


def test_fetch_failure_does_not_increment_misses():
    previous = [TrackedJob("1", "Engineer", "London")]
    updated, health = update_job_states(previous, [], collection_success=False)
    assert not health["healthy"] and updated[0].consecutive_misses == 0


def test_repost_is_linked_to_closed_predecessor():
    prior = [TrackedJob("old", "Plant Manager", "New York", status="closed", consecutive_misses=2)]
    current = [TrackedJob("new", "Plant Manager", "New York City")]
    updated, _ = update_job_states(prior, current, collection_success=True)
    assert next(job for job in updated if job.identity == "new").repost_of == "old"
    assert normalize_location("New York City") == "New York, NY"


def test_real_corpus_is_external_and_gold_has_denominators():
    corpus = list(csv.DictReader((ROOT / "data/evidence_engine_v0_2/corpus_manifest.csv").open()))
    gold = list(csv.DictReader((ROOT / "data/evidence_engine_v0_2/gold_observations.csv").open()))
    assert len(corpus) == 75 and len({row["ticker"] for row in corpus}) == 25
    assert all(row["development_partition_status"] == "external_us_development_no_outcomes" for row in corpus)
    assert len(gold) >= 300 and all(row["exact_evidence_span"] for row in gold)


def test_benchmark_json_contains_counts_and_is_not_ready():
    result = json.loads((ROOT / "data/derived/evidence_engine_v0_2_results.json").read_text())
    assert result["numerical_extraction"]["complete_observation_accuracy"]["total"] == 363
    assert result["model2_readiness"]["status"] == "NOT READY"
    assert result["outcomes_used"] is False and result["predictive_model_trained"] is False


def test_rules_1_0_0_remains_protected():
    assert len(verify_frozen_isolation(ROOT)) == 12
