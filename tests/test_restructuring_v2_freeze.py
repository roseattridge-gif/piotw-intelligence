from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from validation.restructuring_v2 import MODEL_PATH, predict_restructuring, specification_hash

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_model_reproduces_all_v1_predictions_and_contributions():
    fixture = json.loads((ROOT / "data/derived/restructuring_predictions_pre_outcome.json").read_text())
    expected = {(row["ticker"], row["information_cutoff"]): row for row in fixture["predictions"]}
    rows = list(csv.DictReader((ROOT / "data/restructuring/pre_cutoff_evidence.csv").open()))
    assert len(rows) == len(expected) == 20
    for row in rows:
        features = {name: float(row[name]) for name in (
            "pressure_language", "margin_pressure", "cash_pressure", "contrary_strength")}
        probability, contributions = predict_restructuring(features)
        prediction = expected[(row["ticker"], row["cutoff"])]
        assert probability == prediction["probability"]
        assert contributions == prediction["feature_contributions"]


def test_frozen_model_rejects_missing_extra_and_out_of_range_features():
    with pytest.raises(ValueError, match="feature mismatch"):
        predict_restructuring({"margin_pressure": 0.2})
    with pytest.raises(ValueError, match="outside frozen range"):
        predict_restructuring({
            "pressure_language": 0.2, "margin_pressure": 1.1,
            "cash_pressure": 0.2, "contrary_strength": 0.2})


def test_model_specification_hash_is_stable():
    assert len(specification_hash(MODEL_PATH)) == 64
