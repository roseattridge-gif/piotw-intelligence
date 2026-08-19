from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from pipelines.procurement.find_a_tender import ProcurementRecord, SupplierResolution

SCHEMA = """
CREATE TABLE IF NOT EXISTS procurement_collection_runs (
  run_id TEXT PRIMARY KEY, source TEXT NOT NULL, fetched_at TEXT NOT NULL,
  status TEXT NOT NULL, release_count INTEGER NOT NULL, error TEXT
);
CREATE TABLE IF NOT EXISTS procurement_releases (
  release_key TEXT PRIMARY KEY, notice_id TEXT NOT NULL, supplier_raw_name TEXT,
  current_version INTEGER NOT NULL, current_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS procurement_release_versions (
  release_key TEXT NOT NULL, version INTEGER NOT NULL, content_hash TEXT NOT NULL,
  fetched_at TEXT NOT NULL, publication_date TEXT, buyer TEXT, supplier_raw_name TEXT,
  value REAL, currency TEXT, category TEXT, description TEXT, status TEXT,
  contract_start TEXT, contract_end TEXT, source_url TEXT NOT NULL,
  raw_payload TEXT NOT NULL, collector_version TEXT NOT NULL,
  PRIMARY KEY(release_key, version), UNIQUE(release_key, content_hash)
);
CREATE TABLE IF NOT EXISTS procurement_entity_review_queue (
  queue_id TEXT PRIMARY KEY, release_key TEXT NOT NULL, raw_supplier_name TEXT NOT NULL,
  normalized_supplier_name TEXT NOT NULL, candidate_company_id TEXT,
  match_method TEXT NOT NULL, match_confidence REAL NOT NULL, ambiguity_reason TEXT NOT NULL,
  review_status TEXT NOT NULL, approved_canonical_entity_id TEXT,
  reviewed_at TEXT, UNIQUE(release_key, raw_supplier_name)
);
CREATE TABLE IF NOT EXISTS entity_aliases (
  canonical_entity_id TEXT NOT NULL, alias TEXT NOT NULL, alias_type TEXT NOT NULL,
  parent_entity_id TEXT, registration_id TEXT, evidence_source TEXT NOT NULL,
  approved_at TEXT NOT NULL, PRIMARY KEY(canonical_entity_id, alias)
);
"""


def _release_key(record: ProcurementRecord) -> str:
    material = f"{record.notice_id}|{record.supplier_raw_name or ''}"
    return hashlib.sha256(material.encode()).hexdigest()[:32]


def persist_records(path: str | Path, records: list[ProcurementRecord], *, fetched_at: datetime,
                    resolutions: dict[str, SupplierResolution] | None = None,
                    status: str = "success", error: str | None = None) -> dict[str, int | str]:
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=UTC)
    stamp = fetched_at.isoformat()
    database = Path(path)
    database.parent.mkdir(parents=True, exist_ok=True)
    run_id = hashlib.sha256(f"find-a-tender|{stamp}".encode()).hexdigest()[:24]
    inserted = unchanged = revised = queued = 0
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA)
        connection.execute("INSERT OR REPLACE INTO procurement_collection_runs VALUES(?,?,?,?,?,?)",
                           (run_id, "find_a_tender_ocds", stamp, status, len(records), error))
        for record in records:
            key = _release_key(record)
            current = connection.execute(
                "SELECT current_version,current_hash FROM procurement_releases WHERE release_key=?", (key,)
            ).fetchone()
            if current and current[1] == record.content_hash:
                unchanged += 1
            else:
                version = 1 if current is None else current[0] + 1
                inserted += current is None
                revised += current is not None
                connection.execute("""INSERT INTO procurement_release_versions VALUES(
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (key, version, record.content_hash, stamp,
                    record.publication_date, record.buyer, record.supplier_raw_name, record.value,
                    record.currency, record.category, record.description, record.status,
                    record.contract_start, record.contract_end, record.source_url,
                    json.dumps(record.raw_payload, sort_keys=True), record.collector_version))
                connection.execute("""INSERT INTO procurement_releases VALUES(?,?,?,?,?)
                    ON CONFLICT(release_key) DO UPDATE SET current_version=excluded.current_version,
                    current_hash=excluded.current_hash""",
                    (key, record.notice_id, record.supplier_raw_name, version, record.content_hash))
            if not record.supplier_raw_name:
                continue
            resolution = (resolutions or {}).get(record.supplier_raw_name)
            if resolution is None or resolution.manual_review:
                normalized = resolution.normalized_supplier_name if resolution else record.supplier_raw_name.lower().strip()
                candidate = resolution.candidate_company_id if resolution else None
                method = resolution.match_method if resolution else "not_attempted"
                confidence = resolution.match_confidence if resolution else 0.0
                queue_id = hashlib.sha256(f"{key}|{record.supplier_raw_name}".encode()).hexdigest()[:24]
                before = connection.total_changes
                connection.execute("""INSERT OR IGNORE INTO procurement_entity_review_queue VALUES(
                    ?,?,?,?,?,?,?,?,'pending',NULL,NULL)""",
                    (queue_id, key, record.supplier_raw_name, normalized, candidate, method, confidence,
                     "No unique approved exact alias; canonical mapping withheld."))
                queued += connection.total_changes > before
    return {"run_id": run_id, "inserted": inserted, "unchanged": unchanged,
            "revised": revised, "queued": queued}


def approve_mapping(path: str | Path, *, queue_id: str, canonical_entity_id: str,
                    alias_type: str, evidence_source: str, parent_entity_id: str | None = None,
                    registration_id: str | None = None, reviewed_at: datetime | None = None) -> None:
    stamp = (reviewed_at or datetime.now(UTC)).isoformat()
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        row = connection.execute(
            "SELECT raw_supplier_name FROM procurement_entity_review_queue WHERE queue_id=? AND review_status='pending'",
            (queue_id,),
        ).fetchone()
        if not row:
            raise ValueError("pending entity-resolution queue item not found")
        connection.execute("""INSERT INTO entity_aliases VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(canonical_entity_id,alias) DO NOTHING""",
            (canonical_entity_id, row[0], alias_type, parent_entity_id, registration_id,
             evidence_source, stamp))
        connection.execute("""UPDATE procurement_entity_review_queue SET review_status='approved',
            approved_canonical_entity_id=?, reviewed_at=? WHERE queue_id=?""",
            (canonical_entity_id, stamp, queue_id))
