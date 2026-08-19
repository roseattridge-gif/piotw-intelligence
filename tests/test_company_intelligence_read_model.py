from datetime import UTC, datetime, timedelta

from piotw_read_model.api import load_company_snapshot
from piotw_read_model.company_intelligence import build_careers_profile
from pipelines.careers.longitudinal import record_snapshot
from pipelines.careers.models import JobPosting


def job(external_id: str) -> JobPosting:
    return JobPosting(company_id="acme", company_name="Acme", provider="greenhouse",
        external_id=external_id, title="Operations Engineer", location="London",
        source_url=f"https://jobs.example/{external_id}")


def test_read_model_renders_facts_and_explicitly_withholds_scores(tmp_path):
    db = tmp_path / "careers.sqlite3"; now = datetime(2026, 8, 1, tzinfo=UTC)
    record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[job("1")],
                    fetched_at=now, retrieval_success=True)
    record_snapshot(db, company_id="acme", provider="greenhouse", jobs=[job("1"), job("2")],
                    fetched_at=now + timedelta(days=2), retrieval_success=True)
    profile = build_careers_profile(db, company_id="acme", display_name="Acme", as_of=now + timedelta(days=2))
    workforce = next(row for row in profile.dimensions if row.dimension_id == "workforce_capability")
    assert workforce.observations[0].state == 2
    assert workforce.observations[0].change == 1
    assert profile.overall_score.status == "NOT_YET_VALIDATED" and profile.overall_score.value is None
    assert profile.prediction.status == "NOT_YET_VALIDATED"
    assert len(profile.dimensions) == 8


def test_demo_snapshot_is_available_as_internal_api_payload():
    payload = load_company_snapshot("data/derived/company_intelligence_v1", "affirm")
    assert payload["company_id"] == "affirm"
    assert payload["overall_score"] == {"status": "NOT_YET_VALIDATED", "value": None}
