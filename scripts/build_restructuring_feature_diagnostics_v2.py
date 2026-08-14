"""Create contribution-level diagnostics without changing the frozen model."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/derived/restructuring_feature_diagnostics_v2.csv"
FIELDS = ["dataset", "prediction_id", "company", "ticker", "cutoff", "outcome", "outcome_date",
          "probability", "feature_name", "feature_value", "contribution", "direction",
          "evidence_ids", "evidence_observation", "already_announced_exclusion", "diagnostic_only"]


def main() -> None:
    predictions = json.loads((ROOT / "data/derived/restructuring_predictions_pre_outcome.json").read_text())
    outcomes = {row["prediction_id"]: row for row in csv.DictReader(
        (ROOT / "data/restructuring/outcomes.csv").open())}
    evidence = {(row["ticker"], row["cutoff"]): row for row in csv.DictReader(
        (ROOT / "data/restructuring/pre_cutoff_evidence.csv").open())}
    rows = []
    for prediction in predictions["predictions"]:
        outcome = outcomes[prediction["prediction_id"]]
        source = evidence[(prediction["ticker"], prediction["information_cutoff"])]
        for feature, contribution in prediction["feature_contributions"].items():
            rows.append({
                "dataset": "v1_development", "prediction_id": prediction["prediction_id"],
                "company": prediction["company"], "ticker": prediction["ticker"],
                "cutoff": prediction["information_cutoff"], "outcome": outcome["occurred"],
                "outcome_date": outcome["outcome_date"], "probability": prediction["probability"],
                "feature_name": feature, "feature_value": source[feature], "contribution": contribution,
                "direction": "support" if contribution >= 0 else "contradict",
                "evidence_ids": "|".join(prediction["evidence_ids"]),
                "evidence_observation": source["observation"],
                "already_announced_exclusion": prediction["already_announced_exclusion"],
                "diagnostic_only": "true",
            })
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} contribution diagnostics")


if __name__ == "__main__":
    main()
