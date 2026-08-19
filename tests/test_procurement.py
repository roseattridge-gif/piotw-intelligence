import json
import sqlite3
from datetime import UTC, datetime

from pipelines.procurement import FindATenderAdapter, resolve_supplier
from pipelines.procurement.storage import approve_mapping, persist_records


def fixture():
    return {"releases": [{"id": "rel-1", "ocid": "ocds-1", "date": "2026-08-01T10:00:00Z",
        "buyer": {"name": "Example Council"}, "tender": {"mainProcurementCategory": "services"},
        "awards": [{"id": "a1", "status": "active", "description": "Maintenance services",
            "value": {"amount": 125000, "currency": "GBP"},
            "contractPeriod": {"startDate": "2026-09-01", "endDate": "2028-08-31"},
            "suppliers": [{"id": "s1", "name": "Acme Services Limited"}]}]}]}


def test_ocds_adapter_preserves_raw_record_and_fields():
    first = FindATenderAdapter.parse_package(fixture(), source_url="https://official.test/api")
    second = FindATenderAdapter.parse_package(fixture(), source_url="https://official.test/api")
    assert first == second and len(first) == 1
    row = first[0]
    assert (row.notice_id, row.buyer, row.supplier_raw_name, row.value, row.currency) == (
        "rel-1", "Example Council", "Acme Services Limited", 125000.0, "GBP")
    assert row.raw_payload and len(row.content_hash) == 64


def test_supplier_resolution_fails_closed_when_ambiguous_or_unknown():
    matched = resolve_supplier("Acme Services Ltd", {"company-acme": ["Acme Services Limited"]})
    assert matched.candidate_company_id == "company-acme" and not matched.manual_review
    unknown = resolve_supplier("Acme", {"company-acme": ["Acme Services Limited"]})
    assert unknown.candidate_company_id is None and unknown.manual_review


def test_persistence_is_idempotent_and_versions_revisions(tmp_path):
    db = tmp_path / "procurement.sqlite3"
    first = FindATenderAdapter.parse_package(fixture(), source_url="https://official.test/api")
    now = datetime(2026, 8, 18, tzinfo=UTC)
    a = persist_records(db, first, fetched_at=now)
    b = persist_records(db, first, fetched_at=now)
    changed = fixture()
    changed["releases"][0]["awards"][0]["value"]["amount"] = 130000
    revised = FindATenderAdapter.parse_package(changed, source_url="https://official.test/api")
    c = persist_records(db, revised, fetched_at=now)
    assert (a["inserted"], b["unchanged"], c["revised"]) == (1, 1, 1)
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT count(*) FROM procurement_releases").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM procurement_release_versions").fetchone()[0] == 2
        payloads = [json.loads(row[0]) for row in connection.execute(
            "SELECT raw_payload FROM procurement_release_versions ORDER BY version")]
        assert payloads[0] != payloads[1]


def test_unresolved_supplier_is_queued_and_manual_approval_creates_alias(tmp_path):
    db = tmp_path / "procurement.sqlite3"
    row = FindATenderAdapter.parse_package(fixture(), source_url="https://official.test/api")[0]
    result = persist_records(db, [row], fetched_at=datetime(2026, 8, 18, tzinfo=UTC))
    assert result["queued"] == 1
    with sqlite3.connect(db) as connection:
        queue_id, status = connection.execute(
            "SELECT queue_id,review_status FROM procurement_entity_review_queue").fetchone()
    assert status == "pending"
    approve_mapping(db, queue_id=queue_id, canonical_entity_id="company-acme",
                    alias_type="legal_name", evidence_source="Companies House record")
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT approved_canonical_entity_id FROM procurement_entity_review_queue").fetchone()[0] == "company-acme"
        assert connection.execute("SELECT alias FROM entity_aliases").fetchone()[0] == "Acme Services Limited"


def test_missing_supplier_does_not_create_review_item(tmp_path):
    payload = fixture(); payload["releases"][0]["awards"][0]["suppliers"] = []
    rows = FindATenderAdapter.parse_package(payload, source_url="https://official.test/api")
    db = tmp_path / "procurement.sqlite3"
    persist_records(db, rows, fetched_at=datetime(2026, 8, 18, tzinfo=UTC))
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT count(*) FROM procurement_entity_review_queue").fetchone()[0] == 0
