from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from validation.registry_v2 import register_predictions
from validation.restructuring_v2_data import extraction_hash

ROOT = Path(__file__).resolve().parents[1]


def test_v2_registry_is_reproducible_and_immutable(tmp_path: Path):
    raw = tmp_path / "source.txt"
    raw.write_text("pressure but strong cash")
    manifest = [{
        "occasion_id": "rv2-TST-2022-12-31", "company": "Test", "ticker": "TST",
        "stable_id": "gb-tst", "sector": "Engineering", "stratum": "engineering_equipment",
        "cutoff": "2022-12-31", "window_end": "2023-12-31", "dataset_partition": "validation",
        "target": "restructuring_announced", "horizon_days": "365", "inclusion_status": "included",
        "exclusion_reason": "", "selection_rank": "1", "selection_hash": "abc",
    }]
    evidence = [{
        "evidence_id": "e1", "occasion_id": manifest[0]["occasion_id"], "company": "Test", "ticker": "TST",
        "available_at": "2022-12-01", "source_title": "Interim", "source_url": "https://example.test",
        "retrieved_at": "2026-08-13T00:00:00Z", "raw_path": "source.txt",
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "preservation_status": "preserved",
        "parser_version": "manual-1", "source_location": "p1", "observation": "pressure but strong cash",
        "direction": "mixed", "already_announced_exclusion": "", "extraction_sha256": "",
        "review_status": "manual_primary_source",
    }]
    evidence[0]["extraction_sha256"] = extraction_hash(evidence[0])
    features = [{"occasion_id": manifest[0]["occasion_id"], "pressure_language": "0.4",
                 "margin_pressure": "0.3", "cash_pressure": "0.2", "contrary_strength": "0.7",
                 "evidence_ids": "e1", "feature_review_status": "manual"}]
    database = tmp_path / "registry.sqlite3"
    first = register_predictions(manifest, evidence, features, tmp_path, database,
                                 ROOT / "config/models/restructuring_rules_1_0_0.json")
    second = register_predictions(manifest, evidence, features, tmp_path, database,
                                  ROOT / "config/models/restructuring_rules_1_0_0.json")
    assert first == second
    with sqlite3.connect(database) as connection, pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute("UPDATE v2_predictions SET probability=0")
