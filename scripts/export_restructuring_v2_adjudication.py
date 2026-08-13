"""Create probability-blind outcome packets from frozen manifests and candidate events."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validation.restructuring_v2_data import read_csv, validate_blind_export, write_csv

FIELDS = ["occasion_id", "company", "ticker", "cutoff", "window_end", "candidate_event_id",
          "source_title", "source_url", "public_date", "date_precision", "event_description",
          "parent_entity", "affected_entity", "materiality_evidence", "potential_exclusion"]


def build(partition: str, output: str | Path) -> list[dict[str, str]]:
    if partition not in {"validation", "holdout"}:
        raise ValueError("only validation or holdout may be adjudicated")
    manifest = read_csv(ROOT / f"data/manifests/restructuring_{partition}.csv")
    candidates = read_csv(ROOT / "data/restructuring_v2/candidate_outcomes.csv")
    candidates_by_occasion: dict[str, list[dict[str, str]]] = {}
    for row in candidates:
        candidates_by_occasion.setdefault(row["occasion_id"], []).append(row)
    rows = []
    for occasion in manifest:
        candidate_rows = candidates_by_occasion.get(occasion["occasion_id"], [{}])
        for candidate in candidate_rows:
            rows.append({name: (occasion.get(name) or candidate.get(name) or "") for name in FIELDS})
    validate_blind_export(FIELDS, rows)
    write_csv(output, FIELDS, rows)
    print(f"exported {len(rows)} blinded rows for {len(manifest)} occasions")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("partition", choices=["validation", "holdout"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build(args.partition, args.output)


if __name__ == "__main__":
    main()
