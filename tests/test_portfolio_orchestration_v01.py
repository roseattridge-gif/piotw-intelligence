from datetime import UTC, datetime

from piotw_orchestrator.portfolio_v01 import PortfolioOrchestrator


def test_real_portfolio_run_is_deterministic_and_isolates_source_failure(tmp_path):
    orchestrator = PortfolioOrchestrator(
        run_directory=tmp_path / "runs",
        web_directory=tmp_path / "web",
    )
    config = orchestrator.load_config("config/portfolios/real_development_portfolio_v0_1.json")
    as_of = datetime(2026, 9, 4, tzinfo=UTC)

    first = orchestrator.run(config, as_of=as_of)
    second = orchestrator.run(config, as_of=as_of)

    assert first.run_id == second.run_id
    assert first.payload["synthetic"] is False
    assert first.payload["scientific_gate_run"] is False
    assert first.payload["latest_evidence_date"] is not None
    assert first.payload["latest_evidence_date"] <= as_of.date().isoformat()
    assert [item["company_id"] for item in first.payload["attention_items"]] == [
        "travis-perkins", "datadog", "cloudflare"
    ]
    datadog = first.payload["attention_items"][1]
    assert datadog["attention_state"] == "VALIDATE"
    assert datadog["capability_status"] == "INSUFFICIENT_EVIDENCE"
    assert "Development-only" in datadog["missing_information"][0]


def test_previous_run_produces_no_manufactured_change(tmp_path):
    orchestrator = PortfolioOrchestrator(
        run_directory=tmp_path / "runs",
        web_directory=tmp_path / "web",
    )
    config = orchestrator.load_config("config/portfolios/real_development_portfolio_v0_1.json")
    as_of = datetime(2026, 9, 4, tzinfo=UTC)
    first = orchestrator.run(config, as_of=as_of)
    repeated = orchestrator.run(config, as_of=as_of, previous=first.payload)
    assert repeated.payload["changes"] == [{
        "change_type": "NO_MEANINGFUL_CHANGE",
        "company_id": None,
        "statement": "No deterministic portfolio change was detected.",
        "evidence_ids": [],
    }]
