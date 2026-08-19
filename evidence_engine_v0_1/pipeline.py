from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime
from pathlib import Path

from evidence_engine_v0_1.collectors import (
    FixtureJobsCollector,
    FixtureReportCollector,
    jobs_from_raw,
)
from evidence_engine_v0_1.definitions import feature_definition_catalog
from evidence_engine_v0_1.features import calculate_longitudinal_features
from evidence_engine_v0_1.fixtures import COMPANIES, development_corpus, job_snapshots
from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_1.jobs import calculate_job_features
from evidence_engine_v0_1.models import ReviewDecision
from evidence_engine_v0_1.parsing import extract_financial_observations
from evidence_engine_v0_1.quality import evaluate_extraction
from evidence_engine_v0_1.review import apply_review
from evidence_engine_v0_1.storage import EvidenceStore
from evidence_engine_v0_1.taxonomy import (
    extract_language_observations,
    load_taxonomy,
    observations_to_events,
)


def run_demo(root: str | Path, output: str | Path | None = None) -> dict:
    root = Path(root)
    before = verify_frozen_isolation(root)
    started = time.perf_counter()
    records, gold = development_corpus()
    database = root / "data/derived/evidence_engine_v0_1/demo.sqlite3"
    raw_root = root / "data/derived/evidence_engine_v0_1/raw"
    if database.exists():
        database.unlink()
    store = EvidenceStore(database, raw_root)
    store.initialize(root / "database/evidence_engine_v0_1/0001_evidence_engine.sql")
    collector = FixtureReportCollector(records, raw_root)
    taxonomy = load_taxonomy(root / "config/evidence/event_taxonomy_v0_1.yaml")
    definitions = feature_definition_catalog(taxonomy)
    for definition in definitions:
        store.persist_feature_definition(definition)
    all_observations = []
    all_events = []
    all_features = []
    cutoff = date(2025, 12, 31)
    for company in COMPANIES:
        evidence_rows = collector.collect(company, cutoff)
        company_observations = []
        for evidence in evidence_rows:
            store.persist_raw(evidence)
            candidates = extract_financial_observations(evidence) + extract_language_observations(evidence, taxonomy)
            for candidate in candidates:
                decision = ReviewDecision(decision_id=f"review-{candidate.observation_id}",
                    observation_id=candidate.observation_id, decision="accept", reviewer="fixture-gold-auto-review",
                    decided_at=datetime.now(UTC), note="Synthetic gold fixture acceptance")
                accepted = apply_review(candidate, decision)
                store.persist_observation(accepted)
                store.persist_review(decision)
                company_observations.append(accepted)
        events = observations_to_events(company_observations, taxonomy)
        lookup = {o.observation_id: o for o in company_observations}
        for event in events:
            store.persist_event(event, lookup)
        features = calculate_longitudinal_features(company, company_observations, events, cutoff)
        for feature in features:
            store.persist_feature(feature)
        all_observations.extend(company_observations)
        all_events.extend(events)
        all_features.extend(features)
    previous_jobs_fixture, current_jobs_fixture = job_snapshots()
    jobs_collector = FixtureJobsCollector([
        (previous_jobs_fixture[0].collected_at, previous_jobs_fixture),
        (current_jobs_fixture[0].collected_at, current_jobs_fixture),
    ], raw_root)
    job_evidence = jobs_collector.collect("synthetic-01", cutoff)
    for evidence in job_evidence:
        store.persist_raw(evidence)
    previous_jobs = jobs_from_raw(job_evidence[0])
    current_jobs = jobs_from_raw(job_evidence[1])
    for job in previous_jobs + current_jobs:
        store.persist_job(job)
    job_features = calculate_job_features("synthetic-01", current_jobs, previous_jobs, cutoff,
        current_evidence_id=job_evidence[1].evidence_id,
        previous_evidence_id=job_evidence[0].evidence_id)
    for feature in job_features:
        store.persist_feature(feature)
    duration = time.perf_counter() - started
    quality = evaluate_extraction(all_observations, all_events, gold)
    example_features = [f.model_dump(mode="json") for f in all_features + job_features if f.company_id == "synthetic-01"]
    example_observations = [o.model_dump(mode="json") for o in all_observations if o.company_id == "synthetic-01"]
    result = {
        "engine_version": "evidence_engine_v0_1",
        "outcomes_used": False,
        "predictive_model_trained": False,
        "frozen_guard_file_count": len(before),
        "feature_definition_count": len(definitions),
        "corpus": {"kind": "synthetic_gold_fixture", "companies": 10, "periods_per_company": 2, "reports": 20},
        "quality": quality,
        "performance": {
            "reports": 20, "duration_seconds": round(duration, 6),
            "seconds_per_report": round(duration / 20, 6), "llm_calls": 0,
            "llm_cost_usd_per_report": 0, "collector_cost_usd": 0,
            "database_bytes": database.stat().st_size,
        },
        "example_company": {
            "company_id": "synthetic-01", "as_of_date": cutoff.isoformat(),
            "observations": example_observations, "events": [e.model_dump(mode="json") for e in all_events if e.company_id == "synthetic-01"],
            "feature_snapshot": example_features,
            "jobs": {"previous": [j.model_dump(mode="json") for j in previous_jobs], "current": [j.model_dump(mode="json") for j in current_jobs]},
        },
    }
    destination = Path(output) if output else root / "data/derived/evidence_engine_v0_1/demo_output.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    verify_frozen_isolation(root)
    return result
