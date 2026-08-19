from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/evidence_engine_v0_3/corpus_manifest.csv"
OUTPUT = ROOT / "reviewer_pack_v0_3/04_corpus_manifest/corpus_manifest_blinded.csv"
FIELDS = ["document_id", "company", "report_type", "reporting_period", "publication_date"]


def main() -> None:
    with SOURCE.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row[field] for field in FIELDS} for row in rows])


if __name__ == "__main__":
    main()
