from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from piotw_intelligence.company_intelligence_v01 import CompanyIntelligenceV01
from piotw_orchestrator.unknown_company_v01 import UnknownCompanyOrchestrator
from pipelines.careers.longitudinal import SCHEMA, record_snapshot
from pipelines.careers.models import JobPosting


def _registry(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([{
        "company_id": "alpha-industries", "company_name": "Alpha Industries",
        "provider": "greenhouse", "identifier": "alpha",
        "careers_url": "https://example.test/alpha/jobs",
        "access_mode": "public_api", "enabled": True,
    }]))
    return path


def _job(number: int, observed_at: datetime) -> JobPosting:
    return JobPosting(
        company_id="alpha-industries", company_name="Alpha Industries", provider="greenhouse",
        external_id=str(number), title=f"Engineer {number}", location="London",
        source_url=f"https://example.test/jobs/{number}", observed_at=observed_at,
    )


def _orchestrator(tmp_path: Path, *, snapshots: str = "healthy") -> UnknownCompanyOrchestrator:
    registry = _registry(tmp_path / "registry.json")
    database = tmp_path / "careers.sqlite3"
    first = datetime(2026, 1, 1, tzinfo=UTC)
    if snapshots == "healthy":
        record_snapshot(database, company_id="alpha-industries", provider="greenhouse",
                        jobs=[_job(1, first)], fetched_at=first, retrieval_success=True)
        second = datetime(2026, 1, 3, tzinfo=UTC)
        record_snapshot(database, company_id="alpha-industries", provider="greenhouse",
                        jobs=[_job(1, second), _job(2, second)], fetched_at=second,
                        retrieval_success=True)
    elif snapshots == "failed":
        record_snapshot(database, company_id="alpha-industries", provider="greenhouse",
                        jobs=[], fetched_at=first, retrieval_success=False)
    elif snapshots == "empty":
        with sqlite3.connect(database) as connection:
            connection.executescript(SCHEMA)
    return UnknownCompanyOrchestrator(
        company_registry=registry, careers_database=database,
        run_directory=tmp_path / "runs", web_directory=tmp_path / "web",
    )


def test_resolves_unknown_company_and_generates_valid_sparse_object(tmp_path: Path) -> None:
    result = _orchestrator(tmp_path).build(
        company="Alpha Industries", as_of=datetime(2026, 1, 4, tzinfo=UTC))
    assert result.manifest.company.company_id == "alpha-industries"
    assert result.manifest.company.match_method == "NORMALIZED_COMPANY_NAME"
    assert isinstance(result.intelligence, CompanyIntelligenceV01)
    assert len(result.intelligence.evidence) == 2
    assert result.intelligence.conditions == []
    assert result.intelligence.condition_qualifications[0].status == "INSUFFICIENT_EVIDENCE"
    assert "history_depth" in result.intelligence.condition_qualifications[0].failed_tests
    assert result.intelligence.capabilities.model_dump() == {
        "detect": "INSUFFICIENT_EVIDENCE", "compare": "INSUFFICIENT_EVIDENCE",
        "predict": "NOT_BUILT", "prescribe": "WITHHELD", "quantify": "WITHHELD",
    }
    assert result.intelligence.predictions[0].probability is None
    assert result.intelligence.financial_impacts[0].base is None


def test_explicit_entity_resolution_and_unknown_identity(tmp_path: Path) -> None:
    engine = _orchestrator(tmp_path)
    resolved = engine.resolve_identity("anything", explicit_entity_id="alpha-industries")
    assert resolved.match_method == "EXPLICIT_ENTITY_ID"
    with pytest.raises(KeyError, match="approved source registry"):
        engine.resolve_identity("Unknown plc")


def test_cutoff_manifest_preserves_included_and_excluded_provenance(tmp_path: Path) -> None:
    result = _orchestrator(tmp_path).build(
        company="alpha-industries", as_of=datetime(2026, 1, 2, tzinfo=UTC))
    assert result.manifest.included_record_count == 1
    assert result.manifest.excluded_record_count == 1
    assert result.manifest.records[1].inclusion_or_exclusion_reason == "EXCLUDED_AFTER_ANALYSIS_CUTOFF"
    evidence = result.intelligence.evidence[0]
    assert evidence.source_hash and len(evidence.source_hash) == 64
    assert evidence.source_id == result.manifest.records[0].source_record_id


def test_unavailable_store_failed_source_and_no_history_are_distinct(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "registry.json")
    unavailable = UnknownCompanyOrchestrator(
        company_registry=registry, careers_database=tmp_path / "missing.sqlite3",
        run_directory=tmp_path / "runs", web_directory=tmp_path / "web",
    ).build(company="alpha-industries", as_of=datetime(2026, 1, 4, tzinfo=UTC))
    assert unavailable.manifest.source_availability[0].status == "UNAVAILABLE"

    failed = _orchestrator(tmp_path / "failed", snapshots="failed").build(
        company="alpha-industries", as_of=datetime(2026, 1, 4, tzinfo=UTC))
    assert failed.manifest.source_availability[0].status == "FAILED"
    assert failed.intelligence.evidence == []

    no_history = _orchestrator(tmp_path / "empty", snapshots="empty").build(
        company="alpha-industries", as_of=datetime(2026, 1, 4, tzinfo=UTC))
    assert no_history.manifest.source_availability[0].status == "NO_HISTORY"
    assert no_history.intelligence.conditions == []


def test_same_inputs_are_reproducible_and_persist_to_generic_path(tmp_path: Path) -> None:
    engine = _orchestrator(tmp_path)
    cutoff = datetime(2026, 1, 4, tzinfo=UTC)
    first = engine.build(company="alpha-industries", as_of=cutoff)
    second = engine.build(company="alpha-industries", as_of=cutoff)
    assert first.run_id == second.run_id
    assert first.manifest.manifest_hash == second.manifest.manifest_hash
    assert first.intelligence.model_dump(mode="json") == second.intelligence.model_dump(mode="json")
    saved = engine.persist(first)
    assert Path(saved.web_path or "").name == "alpha-industries.json"
    assert CompanyIntelligenceV01.model_validate_json(Path(saved.web_path or "").read_text())


def test_invalid_evidence_reference_fails_canonical_contract(tmp_path: Path) -> None:
    result = _orchestrator(tmp_path).build(
        company="alpha-industries", as_of=datetime(2026, 1, 4, tzinfo=UTC))
    payload = result.intelligence.model_dump(mode="json")
    payload["condition_qualifications"][0]["evidence_ids"] = ["ev-does-not-exist"]
    with pytest.raises(ValidationError, match="unknown evidence references"):
        CompanyIntelligenceV01.model_validate(payload)


def test_orchestrator_contains_no_company_specific_rescue_path() -> None:
    source = Path("piotw_orchestrator/unknown_company_v01.py").read_text().lower()
    for company_name in ("travis", "perkins", "cloudflare"):
        assert company_name not in source
