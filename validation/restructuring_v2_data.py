from __future__ import annotations

import csv
import hashlib
from calendar import monthrange
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

from validation.restructuring_v2 import canonical_json

FORBIDDEN_BLIND_FIELDS = {
    "probability", "confidence", "risk_rank", "feature_contributions",
    "pressure_language", "margin_pressure", "cash_pressure", "contrary_strength",
    "constant_prior", "financial_stress_rule", "disclosure_language_rule",
    "financial_only_logistic", "leave_one_company_out_development_rate",
}


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: str | Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def cutoff_end(cutoff: str) -> datetime:
    return datetime.combine(date.fromisoformat(cutoff), time.max, tzinfo=UTC)


def parse_public_datetime(value: str) -> datetime:
    if "T" not in value:
        return datetime.combine(date.fromisoformat(value), time.max, tzinfo=UTC)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("available_at timestamp must include a timezone")
    return parsed.astimezone(UTC)


def month_only_date(year_month: str) -> date:
    year, month = map(int, year_month.split("-"))
    return date(year, month, monthrange(year, month)[1])


def event_in_window(cutoff: str, window_end: str, event_date: str) -> bool:
    event = date.fromisoformat(event_date)
    return date.fromisoformat(cutoff) < event <= date.fromisoformat(window_end)


def validate_manifest(rows: list[dict[str, str]], expected_partition: str | None = None) -> None:
    ids = [row["occasion_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate occasion_id in manifest")
    for row in rows:
        if expected_partition and row["dataset_partition"] != expected_partition:
            raise ValueError("manifest partition mismatch")
        cutoff = date.fromisoformat(row["cutoff"])
        window_end = date.fromisoformat(row["window_end"])
        if (window_end - cutoff).days != int(row["horizon_days"]):
            raise ValueError(f"outcome window mismatch at {row['occasion_id']}")


def extraction_hash(row: dict[str, str]) -> str:
    fields = {name: row[name] for name in (
        "evidence_id", "occasion_id", "available_at", "source_title", "source_url",
        "raw_sha256", "source_location", "observation", "direction",
        "already_announced_exclusion")}
    return hashlib.sha256(canonical_json(fields).encode()).hexdigest()


def validate_evidence(manifest: list[dict[str, str]], evidence: list[dict[str, str]],
                      root: str | Path) -> None:
    manifest_by_id = {row["occasion_id"]: row for row in manifest}
    evidence_ids: set[str] = set()
    root = Path(root)
    for row in evidence:
        if row["evidence_id"] in evidence_ids:
            raise ValueError(f"duplicate evidence: {row['evidence_id']}")
        evidence_ids.add(row["evidence_id"])
        if row["occasion_id"] not in manifest_by_id:
            raise ValueError(f"evidence not in manifest: {row['occasion_id']}")
        occasion = manifest_by_id[row["occasion_id"]]
        if parse_public_datetime(row["available_at"]) > cutoff_end(occasion["cutoff"]):
            raise ValueError(f"future-data leakage at {row['evidence_id']}")
        if row["extraction_sha256"] != extraction_hash(row):
            raise ValueError(f"extraction hash mismatch at {row['evidence_id']}")
        if row["raw_path"]:
            raw_path = root / row["raw_path"]
            if not raw_path.is_file():
                raise ValueError(f"missing raw source at {row['evidence_id']}")
            actual_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            if actual_hash != row["raw_sha256"]:
                raise ValueError(f"raw source hash mismatch at {row['evidence_id']}")
        elif row["preservation_status"] != "unavailable_documented":
            raise ValueError(f"missing source requires documented preservation status at {row['evidence_id']}")


def validate_features(manifest: list[dict[str, str]], evidence: list[dict[str, str]],
                      features: list[dict[str, str]]) -> None:
    included = {row["occasion_id"] for row in manifest
                if row["inclusion_status"].startswith("included")}
    feature_ids = [row["occasion_id"] for row in features]
    if len(feature_ids) != len(set(feature_ids)):
        raise ValueError("duplicate feature occasion")
    if set(feature_ids) != included:
        missing = sorted(included - set(feature_ids))
        extra = sorted(set(feature_ids) - included)
        raise ValueError(f"feature coverage mismatch; missing={missing[:5]}, extra={extra[:5]}")
    evidence_ids = {row["evidence_id"] for row in evidence}
    evidence_occasion = {row["evidence_id"]: row["occasion_id"] for row in evidence}
    for row in features:
        linked = [item for item in row["evidence_ids"].split("|") if item]
        if not linked:
            raise ValueError(f"feature row has no evidence: {row['occasion_id']}")
        if any(item not in evidence_ids for item in linked):
            raise ValueError(f"unknown evidence link at {row['occasion_id']}")
        if any(evidence_occasion[item] != row["occasion_id"] for item in linked):
            raise ValueError(f"cross-occasion evidence link at {row['occasion_id']}")
        for name in ("pressure_language", "margin_pressure", "cash_pressure", "contrary_strength"):
            value = float(row[name])
            if not 0 <= value <= 1:
                raise ValueError(f"feature outside 0..1 at {row['occasion_id']}")


def validate_blind_export(fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    exposed = FORBIDDEN_BLIND_FIELDS & set(fieldnames)
    if exposed:
        raise ValueError(f"adjudication export exposes model data: {sorted(exposed)}")
    for row in rows:
        if FORBIDDEN_BLIND_FIELDS & set(row):
            raise ValueError("adjudication row exposes model data")


def validate_adjudication(row: dict[str, str], manifest_row: dict[str, str]) -> None:
    if row["adjudication"] not in {"positive", "negative", "uncertain"}:
        raise ValueError("invalid adjudication")
    if not row["adjudicator"] or not row["adjudicated_at"]:
        raise ValueError("adjudicator and timestamp are required")
    if row["adjudication"] == "positive":
        if not row["event_date"] or not row["source_url"]:
            raise ValueError("positive adjudication needs event date and source")
        if not event_in_window(manifest_row["cutoff"], manifest_row["window_end"], row["event_date"]):
            raise ValueError("positive event outside outcome window")
    if row["date_precision"] not in {"day", "month", "none"}:
        raise ValueError("invalid date precision")
