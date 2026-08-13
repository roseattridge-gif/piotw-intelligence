from datetime import datetime, timezone

from pipelines.careers.adapters import GreenhouseAdapter, LeverAdapter
from pipelines.careers.discovery import detect_provider
from pipelines.careers.jsonld import extract_job_postings
from pipelines.careers.models import CareerSource, JobPosting
from pipelines.careers.storage import save_snapshot


class FakeClient:
    def __init__(self, payload): self.payload = payload
    def get_json(self, _url): return self.payload


def source(provider="greenhouse"):
    return CareerSource(company_id="acme", company_name="Acme", provider=provider,
                        identifier="acme", careers_url="https://example.test")


def test_detects_public_and_closed_ats_routes():
    assert detect_provider("https://boards.greenhouse.io/acme").provider == "greenhouse"
    assert detect_provider("https://jobs.lever.co/acme").identifier == "acme"
    assert detect_provider("https://acme.wd3.myworkdayjobs.com/jobs").public_api is False
    assert detect_provider("https://apply.workable.com/acme").provider == "workable"


def test_normalizes_greenhouse():
    payload = {"jobs": [{"id": 12, "title": "Plant Manager", "location": {"name": "Leeds"},
                         "departments": [{"name": "Operations"}], "content": "<p>Lead change</p>",
                         "updated_at": "2026-08-01T10:00:00Z", "absolute_url": "https://jobs/12"}]}
    job = GreenhouseAdapter(FakeClient(payload)).collect(source())[0]
    assert (job.title, job.department, job.description) == ("Plant Manager", "Operations", "Lead change")


def test_normalizes_lever():
    payload = [{"id": "x", "text": "Data Lead", "categories": {"location": "London", "team": "Data"},
                "descriptionPlain": "Build the function", "hostedUrl": "https://jobs/x", "applyUrl": "https://apply/x"}]
    job = LeverAdapter(FakeClient(payload)).collect(source("lever"))[0]
    assert job.location == "London"
    assert job.identity == "acme:lever:x"


def test_extracts_jobposting_jsonld():
    html = '<script type="application/ld+json">{"@type":"JobPosting","title":"Engineer"}</script>'
    assert extract_job_postings(html)[0]["title"] == "Engineer"


def test_snapshot_marks_disappeared_job_closed(tmp_path):
    database = tmp_path / "jobs.sqlite3"
    job = JobPosting(company_id="acme", company_name="Acme", provider="greenhouse", external_id="1",
                     title="Engineer", source_url="https://jobs/1")
    first = datetime(2026, 8, 1, tzinfo=timezone.utc)
    later = datetime(2026, 8, 2, tzinfo=timezone.utc)
    save_snapshot(database, "acme", "greenhouse", [job], first)
    save_snapshot(database, "acme", "greenhouse", [], later)
    import sqlite3
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT closed_at FROM career_jobs").fetchone()[0] == later.isoformat()
