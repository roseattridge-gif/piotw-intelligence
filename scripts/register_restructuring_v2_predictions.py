from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validation.registry_v2 import register_predictions
from validation.restructuring_v2_data import read_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("partition", choices=["validation", "holdout"])
    args = parser.parse_args()
    manifest = read_csv(ROOT / f"data/manifests/restructuring_{args.partition}.csv")
    occasion_ids = {row["occasion_id"] for row in manifest}
    result = register_predictions(
        manifest,
        [row for row in read_csv(ROOT / "data/restructuring_v2/evidence.csv")
         if row["occasion_id"] in occasion_ids],
        [row for row in read_csv(ROOT / "data/restructuring_v2/features.csv")
         if row["occasion_id"] in occasion_ids], ROOT,
        ROOT / "data/derived/restructuring_validation_v2.sqlite3",
        ROOT / "config/models/restructuring_rules_1_0_0.json",
    )
    output = ROOT / f"data/derived/restructuring_{args.partition}_predictions_v2.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"registered {result['prediction_count']} immutable {args.partition} predictions")


if __name__ == "__main__":
    main()
