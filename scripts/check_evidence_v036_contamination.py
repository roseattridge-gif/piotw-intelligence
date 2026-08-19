from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = ROOT / "data/evidence_engine_v0_3_6/fresh_candidate_manifest.csv"

FIELDS = {
    "company": ("company", "target_company", "company_name"),
    "ticker": ("ticker",),
    "document_id": ("document_id",),
    "source_url": ("source_url",),
    "sha256": ("sha256", "source_hash", "content_hash"),
}


def _normal(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def prior_values(root: Path = ROOT) -> dict[str, set[str]]:
    values = {field: set() for field in FIELDS}
    candidate = (root / "data/evidence_engine_v0_3_6/fresh_candidate_manifest.csv").resolve()
    for path in (root / "data").rglob("*.csv"):
        if path.resolve() == candidate:
            continue
        try:
            with path.open(errors="replace") as handle:
                for row in csv.DictReader(handle):
                    for field, aliases in FIELDS.items():
                        for alias in aliases:
                            if row.get(alias):
                                values[field].add(_normal(row[alias]))
        except (csv.Error, UnicodeDecodeError):
            continue
    return values


def check_manifest(path: Path, root: Path = ROOT) -> dict:
    prior = prior_values(root)
    overlaps = []
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    for row_number, row in enumerate(rows, start=2):
        for field in FIELDS:
            value = _normal(row.get(field, ""))
            if value and value in prior[field]:
                overlaps.append({"row": row_number, "field": field, "value": row.get(field, "")})
    return {"status": "PASS" if not overlaps else "FAIL", "candidate_rows": len(rows),
            "overlaps": overlaps, "gate_execution_authorized": False}


def main() -> None:
    result = check_manifest(DEFAULT_CANDIDATE)
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
