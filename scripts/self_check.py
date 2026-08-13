"""Dependency-light verification of the complete local MVP path."""
from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtesting.evaluation import evaluate_binary
from intelligence.models import EvidenceObservation, SourceCoverage
from intelligence.scoring.evidence_model import EvidenceModel
from pipelines.careers.discovery import detect_provider
from pipelines.careers.jsonld import extract_job_postings
from pipelines.careers.models import JobPosting
from pipelines.careers.storage import save_snapshot


def main() -> None:
    scorer = EvidenceModel(ROOT / "intelligence/ontology/signal_weights_v02.yaml",
                           ROOT / "intelligence/ontology/signal_catalog_v02.yaml")
    observation = EvidenceObservation(
        observation_id="check", company_id="acme", family="workforce_demand_skills",
        feature="vacancy_acceleration", event_date=date(2026, 1, 1),
        available_at=datetime(2026, 1, 1, tzinfo=timezone.utc), source_type="ats",
        source_url="https://example.test/jobs", source_name="Test", source_is_company_controlled=True,
        event_cluster_id="check", direction_pressure=1, direction_expansion=1, strength=1,
        source_reliability=1, measurement_quality=1, materiality=1, independence=1,
        explanation="check", extraction_method="self_check")
    coverage = [SourceCoverage(company_id="acme", family="workforce_demand_skills",
                               as_of_date=date(2026, 1, 1), coverage=1, note="check")]
    prediction = scorer.predict("acme", "operational_pressure", 18, date(2026, 1, 1),
                                [observation], coverage)
    assert prediction.probability > prediction.prior_probability
    assert prediction.confidence <= 0.55
    assert detect_provider("https://boards.greenhouse.io/acme").public_api
    assert not detect_provider("https://acme.wd3.myworkdayjobs.com/jobs").public_api
    assert len(extract_job_postings(
        '<script type="application/ld+json">{"@type":"JobPosting","title":"Engineer"}</script>')) == 1
    assert evaluate_binary([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]).average_precision == 1
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "jobs.sqlite3"
        job = JobPosting(company_id="acme", company_name="Acme", provider="greenhouse",
                         external_id="1", title="Engineer", source_url="https://example.test/1")
        save_snapshot(database, "acme", "greenhouse", [job], datetime(2026, 1, 1, tzinfo=timezone.utc))
        save_snapshot(database, "acme", "greenhouse", [], datetime(2026, 1, 2, tzinfo=timezone.utc))
        with sqlite3.connect(database) as connection:
            assert connection.execute("SELECT closed_at FROM career_jobs").fetchone()[0]
    subprocess.run([sys.executable, str(ROOT / "scripts/validate_pilot.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_vertical_slice.py")], cwd=ROOT, check=True)
    with sqlite3.connect(ROOT / "data/derived/piotw_mvp.sqlite3") as connection:
        assert connection.execute("SELECT COUNT(*) FROM predictions").fetchone()[0] == 1
        assert connection.execute("SELECT resolution_status FROM prediction_resolutions").fetchone()[0] == "resolved_negative"
        assert connection.execute("SELECT COUNT(*) FROM backtest_results").fetchone()[0] == 1
    print("MVP self-check passed: collection, entities, events, features, immutable prediction, outcome, backtest and dashboard data")


if __name__ == "__main__":
    main()
