from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_outcomes_resolve_frozen_predictions_and_are_immutable():
    subprocess.run([sys.executable, str(ROOT / "scripts/register_restructuring_predictions.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_restructuring_validation.py")], check=True)
    predictions = json.loads((ROOT / "data/derived/restructuring_predictions_pre_outcome.json").read_text())
    outcomes = list(csv.DictReader((ROOT / "data/restructuring/outcomes.csv").open()))
    results = json.loads((ROOT / "data/derived/restructuring_validation_results.json").read_text())
    assert len(outcomes) == predictions["prediction_count"] == results["scored_count"] == 20
    assert results["positive_count"] == 4
    assert results["gate"]["eligible_comparators"] == ["constant_12_percent"]
    assert results["gate"]["passed"] is False
    assert results["gate"]["quantitative_candidate_met"] is True
    with sqlite3.connect(ROOT / "data/derived/restructuring_validation.sqlite3") as connection:
        prediction_id = outcomes[0]["prediction_id"]
        try:
            connection.execute("UPDATE validation_outcomes SET occurred=1 WHERE prediction_id=?", (prediction_id,))
        except sqlite3.IntegrityError as error:
            assert "immutable" in str(error)
        else:
            raise AssertionError("outcome update should be blocked")
