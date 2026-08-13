from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from validation.restructuring_v2_data import (
    event_in_window,
    extraction_hash,
    month_only_date,
    validate_adjudication,
    validate_blind_export,
    validate_evidence,
    validate_manifest,
)


def manifest_row() -> dict[str, str]:
    return {"occasion_id": "x", "cutoff": "2022-12-31", "window_end": "2023-12-31",
            "horizon_days": "365", "dataset_partition": "validation",
            "inclusion_status": "included"}


def test_future_evidence_fails_loudly(tmp_path: Path):
    row = {"evidence_id": "e1", "occasion_id": "x", "available_at": "2023-01-01",
           "source_title": "future", "source_url": "https://example.test", "raw_path": "",
           "raw_sha256": "", "preservation_status": "unavailable_documented",
           "source_location": "p1", "observation": "future", "direction": "support",
           "already_announced_exclusion": "", "extraction_sha256": ""}
    row["extraction_sha256"] = extraction_hash(row)
    with pytest.raises(ValueError, match="future-data leakage"):
        validate_evidence([manifest_row()], [row], tmp_path)


def test_raw_source_hash_is_enforced(tmp_path: Path):
    raw = tmp_path / "source.txt"
    raw.write_text("eligible")
    row = {"evidence_id": "e1", "occasion_id": "x", "available_at": "2022-12-01",
           "source_title": "eligible", "source_url": "https://example.test", "raw_path": "source.txt",
           "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(), "preservation_status": "preserved",
           "source_location": "p1", "observation": "eligible", "direction": "contrary",
           "already_announced_exclusion": "", "extraction_sha256": ""}
    row["extraction_sha256"] = extraction_hash(row)
    validate_evidence([manifest_row()], [row], tmp_path)
    raw.write_text("changed")
    with pytest.raises(ValueError, match="raw source hash mismatch"):
        validate_evidence([manifest_row()], [row], tmp_path)


def test_outcome_boundaries_and_month_only_dates():
    assert not event_in_window("2022-12-31", "2023-12-31", "2022-12-31")
    assert event_in_window("2022-12-31", "2023-12-31", "2023-12-31")
    assert not event_in_window("2022-12-31", "2023-12-31", "2024-01-01")
    assert str(month_only_date("2024-02")) == "2024-02-29"


def test_blind_export_rejects_prediction_information():
    validate_blind_export(["occasion_id", "company"], [{"occasion_id": "x", "company": "A"}])
    with pytest.raises(ValueError, match="exposes model data"):
        validate_blind_export(["occasion_id", "probability"], [])


def test_adjudication_enforces_window_and_required_source():
    good = {"adjudication": "positive", "adjudicator": "reviewer-a",
            "adjudicated_at": "2026-08-13T00:00:00Z", "event_date": "2023-12-31",
            "source_url": "https://example.test", "date_precision": "day"}
    validate_adjudication(good, manifest_row())
    with pytest.raises(ValueError, match="outside outcome window"):
        validate_adjudication({**good, "event_date": "2024-01-01"}, manifest_row())


def test_manifest_rejects_duplicate_occasions():
    with pytest.raises(ValueError, match="duplicate occasion"):
        validate_manifest([manifest_row(), manifest_row()], "validation")
