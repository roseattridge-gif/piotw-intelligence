import csv
from pathlib import Path

from scripts.check_evidence_v036_contamination import check_manifest

FIELDS = ["document_id", "company", "ticker", "source_url", "sha256", "event_family",
          "development_safe_status"]


def _write(path: Path, row: dict):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader(); writer.writerow(row)


def test_contamination_guard_rejects_known_company(tmp_path):
    path = tmp_path / "candidate.csv"
    _write(path, {"document_id": "new-document", "company": "Apple Inc.", "ticker": "NEW",
                  "source_url": "https://example.test/new", "sha256": "new-hash",
                  "event_family": "quality_regulatory", "development_safe_status": "proposed"})
    result = check_manifest(path)
    assert result["status"] == "FAIL"
    assert any(row["field"] == "company" for row in result["overlaps"])


def test_contamination_guard_allows_unused_fixture_identity(tmp_path):
    path = tmp_path / "candidate.csv"
    _write(path, {"document_id": "future-unused-doc-xyz", "company": "Unused Fixture Entity XYZ",
                  "ticker": "UFEXYZ", "source_url": "https://example.test/future-unused-xyz",
                  "sha256": "unused-hash-xyz", "event_family": "quality_regulatory",
                  "development_safe_status": "proposed"})
    assert check_manifest(path)["status"] == "PASS"
