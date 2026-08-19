from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

REQUIRED_OBSERVATION_FIELDS = {
    "document_id", "metric_type", "value", "unit", "scale", "currency", "period",
    "accounting_basis", "source_page_section", "exact_evidence_span", "reviewer_id",
    "annotation_timestamp", "ambiguity_flag",
}
REQUIRED_EVENT_FIELDS = {
    "document_id", "reviewer_free_text_label", "mapped_event_type", "label_status",
    "source_page_section", "exact_evidence_span", "reviewer_id", "annotation_timestamp",
    "ambiguity_flag",
}
FORBIDDEN_BLIND_FIELDS = {
    "piotw_value", "piotw_event_label", "extraction_confidence", "parser_output",
    "feature_value", "machine_prediction",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def validate_blind_schema(path: Path, required: set[str]) -> None:
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
    missing = required - fields
    leaked = FORBIDDEN_BLIND_FIELDS & fields
    if missing or leaked:
        raise ValueError(f"invalid blind schema {path}: missing={sorted(missing)} leaked={sorted(leaked)}")


def freeze_annotations(data_dir: Path, reviewer_id: str) -> dict:
    """Freeze completed human-first gold. Refuses empty, incomplete, or anonymous work."""
    observation_path = data_dir / "gold_observations.csv"
    event_path = data_dir / "gold_events.csv"
    validate_blind_schema(observation_path, REQUIRED_OBSERVATION_FIELDS)
    validate_blind_schema(event_path, REQUIRED_EVENT_FIELDS)
    observations = read_rows(observation_path)
    events = read_rows(event_path)
    if not observations or not events:
        raise ValueError("independent annotations are empty")
    if not reviewer_id.strip():
        raise ValueError("reviewer_id is required")
    for row in observations + events:
        if row.get("reviewer_id") != reviewer_id:
            raise ValueError("all annotations must identify the freezing reviewer")
        if not row.get("annotation_timestamp") or not row.get("exact_evidence_span"):
            raise ValueError("every annotation requires timestamp and exact evidence span")
    manifest = {
        "schema_version": "0.3.0",
        "status": "frozen",
        "blinded_human_first": True,
        "reviewer_id": reviewer_id,
        "frozen_at": datetime.now(UTC).isoformat(),
        "files": {
            "gold_observations.csv": {"sha256": sha256(observation_path), "rows": len(observations)},
            "gold_events.csv": {"sha256": sha256(event_path), "rows": len(events)},
        },
    }
    (data_dir / "annotation_freeze_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return manifest


def verify_frozen_annotations(data_dir: Path) -> dict:
    manifest = json.loads((data_dir / "annotation_freeze_manifest.json").read_text())
    if manifest.get("status") != "frozen" or not manifest.get("blinded_human_first"):
        raise ValueError("independent gold is not frozen")
    for name, expected in manifest["files"].items():
        path = data_dir / name
        if sha256(path) != expected["sha256"]:
            raise ValueError(f"frozen annotation changed: {name}")
        if len(read_rows(path)) != expected["rows"]:
            raise ValueError(f"frozen annotation row count changed: {name}")
    return manifest
