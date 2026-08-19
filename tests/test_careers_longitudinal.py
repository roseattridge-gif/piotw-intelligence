import json
import sqlite3
from datetime import UTC, datetime, timedelta

from pipelines.careers.longitudinal import record_snapshot, source_health_report, source_is_due
from pipelines.careers.models import JobPosting
from scripts.backfill_careers_snapshot_features_v01 import backfill


def job(external_id="1", title="Operations Manager"):
    return JobPosting(company_id="acme", company_name="Acme", provider="greenhouse",
        external_id=external_id, title=title, location="London", source_url=f"https://jobs/{external_id}")


def test_lifecycle_requires_two_healthy_absences_and_supports_reopen(tmp_path):
    db = tmp_path / "jobs.sqlite3"; now = datetime(2026, 8, 17, tzinfo=UTC)
    assert record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[job()], fetched_at=now, retrieval_success=True).new_count == 1
    assert record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[], fetched_at=now+timedelta(days=2), retrieval_success=True).closed_count == 0
    assert record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[], fetched_at=now+timedelta(days=4), retrieval_success=True).closed_count == 1
    assert record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[job()], fetched_at=now+timedelta(days=6), retrieval_success=True).reopened_count == 1


def test_failure_or_suspicious_drop_does_not_close_jobs(tmp_path):
    db = tmp_path / "jobs.sqlite3"; now = datetime(2026, 8, 17, tzinfo=UTC)
    jobs = [job(str(index)) for index in range(10)]
    record_snapshot(db, company_id="acme", provider="greenhouse", jobs=jobs, fetched_at=now, retrieval_success=True)
    failed = record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[], fetched_at=now+timedelta(days=2), retrieval_success=False)
    suspicious = record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[jobs[0]], fetched_at=now+timedelta(days=4), retrieval_success=True)
    assert failed.health == "fetch_failed" and suspicious.health == "suspicious_drop"
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT count(*) FROM career_job_lifecycle WHERE status='open'").fetchone()[0] == 10


def test_snapshot_is_idempotent_for_same_company_provider_time(tmp_path):
    db = tmp_path / "jobs.sqlite3"; now = datetime(2026, 8, 17, tzinfo=UTC)
    record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[job()], fetched_at=now, retrieval_success=True)
    record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[job()], fetched_at=now, retrieval_success=True)
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT count(*) FROM career_collection_snapshots").fetchone()[0] == 1


def test_source_health_report_keeps_failed_source_visible(tmp_path):
    db = tmp_path / "jobs.sqlite3"; now = datetime(2026, 8, 17, tzinfo=UTC)
    record_snapshot(db, company_id="anduril", provider="greenhouse", jobs=[], fetched_at=now,
                    retrieval_success=False)
    report = source_health_report(db, as_of=now + timedelta(days=3))
    assert report[0]["company_id"] == "anduril"
    assert report[0]["health"] == "fetch_failed"
    assert report[0]["consecutive_failure_count"] == 1
    assert report[0]["stale_source_flag"] is True


def test_snapshot_preserves_richer_role_and_aggregate_structure(tmp_path):
    db = tmp_path / "jobs.sqlite3"; now = datetime(2026, 8, 17, tzinfo=UTC)
    role = job().model_copy(update={"title": "Director, Data Engineering - Python AWS",
        "department": "Engineering", "location": "London, United Kingdom", "workplace_type": "hybrid"})
    result = record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[role],
                             fetched_at=now, retrieval_success=True)
    with sqlite3.connect(db) as connection:
        stored = connection.execute("SELECT function_class,seniority_class,country,named_technologies,derived_origin FROM career_snapshot_roles").fetchone()
        aggregate = connection.execute("SELECT function_mix,seniority_mix,derived_origin FROM career_snapshot_aggregates").fetchone()
    assert stored == ("data_ai", "director", "United Kingdom", '["AWS","Python"]', "LIVE_COLLECTION")
    assert json.loads(aggregate[0]) == {"data_ai": 1}
    assert json.loads(aggregate[1]) == {"director": 1}
    assert aggregate[2] == "LIVE_COLLECTION" and result.absent_once_count == 0


def test_unknown_classifications_and_due_gate_are_explicit(tmp_path):
    db = tmp_path / "jobs.sqlite3"; now = datetime(2026, 8, 17, tzinfo=UTC)
    role = job().model_copy(update={"title": "Associate", "location": None})
    record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[role],
                    fetched_at=now, retrieval_success=True)
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT function_class,country FROM career_snapshot_roles").fetchone() == ("other_unknown", None)
    assert not source_is_due(db, company_id="acme", provider="greenhouse", as_of=now + timedelta(hours=47))
    assert source_is_due(db, company_id="acme", provider="greenhouse", as_of=now + timedelta(hours=48))


def test_backfill_distinguishes_legacy_summary_from_deterministic_reprocessing(tmp_path):
    db = tmp_path / "jobs.sqlite3"; raw = tmp_path / "raw"; raw.mkdir()
    now = datetime(2026, 8, 15, tzinfo=UTC)
    first = record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[job("1")],
                            fetched_at=now, retrieval_success=True)
    second = record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[job("1"), job("2")],
                             fetched_at=now + timedelta(days=2), retrieval_success=True)
    (raw / "snapshot_20260817T000000Z.json").write_text(json.dumps({"runs": [{
        "snapshot_id": second.snapshot_id, "health": "healthy", "new_count": 1,
        "persistent_count": 1, "closed_count": 0, "reopened_count": 0,
        "jobs": [job("1").model_dump(mode="json"), job("2").model_dump(mode="json")]}]}, default=str))
    backfill(db, raw)
    with sqlite3.connect(db) as connection:
        rows = connection.execute("SELECT snapshot_id,derived_origin,aggregate_hash FROM career_snapshot_aggregates ORDER BY snapshot_id").fetchall()
        first_hashes = {row[0]: row[2] for row in rows}
        origins = {row[0]: row[1] for row in rows}
    backfill(db, raw)
    with sqlite3.connect(db) as connection:
        second_hashes = dict(connection.execute("SELECT snapshot_id,aggregate_hash FROM career_snapshot_aggregates"))
    assert origins[first.snapshot_id] == "LEGACY_SUMMARY_ONLY"
    assert origins[second.snapshot_id] == "HISTORICAL_REPROCESSING"
    assert first_hashes == second_hashes
