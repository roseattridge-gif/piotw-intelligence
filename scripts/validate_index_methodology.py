"""Validate PIOTW Index v0.1 registries without calculating any score."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "methodology" / "index"
VALID_POLARITIES = {"positive", "negative", "neutral/context", "bidirectional"}
VALID_STATUSES = {"candidate", "provisional", "excluded", "needs-validation"}
REQUIRED_CONFIG = {
    "methodology_id", "index_methodology_version", "status", "validated",
    "production_scoring_enabled", "constructs", "dimension_weights",
    "feature_weighting", "normalisation_method_candidates", "peer_thresholds",
    "rating_bands", "rating_bands_status", "methodology_freeze_rule",
}


def load_json(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def parse_bool(value: str, field: str, feature_id: str) -> bool:
    if value not in {"true", "false"}:
        raise AssertionError(f"{feature_id}: {field} must be true or false")
    return value == "true"


def validate() -> dict[str, int | str]:
    dimensions_doc = load_json("DIMENSION_REGISTRY_v0.1.json")
    finance_doc = load_json("FINANCIAL_LINKAGE_REGISTRY_v0.1.json")
    interventions_doc = load_json("INTERVENTION_CLASS_REGISTRY_v0.1.json")
    config = load_json("index-config.example.json")

    dimensions = dimensions_doc["dimensions"]
    dimension_ids = {item["dimension_id"] for item in dimensions}
    assert len(dimensions) == 6 and len(dimension_ids) == 6
    assert all(item["status"] in VALID_STATUSES for item in dimensions)

    with (BASE / "FEATURE_REGISTRY_v0.1.csv").open(newline="", encoding="utf-8") as handle:
        features = list(csv.DictReader(handle))
    feature_ids = [item["feature_id"] for item in features]
    assert len(feature_ids) == len(set(feature_ids)), "feature IDs must be unique"
    assert features, "feature registry must not be empty"
    for item in features:
        feature_id = item["feature_id"]
        assert item["dimension"] in dimension_ids, f"{feature_id}: invalid dimension"
        assert item["polarity"] in VALID_POLARITIES, f"{feature_id}: invalid polarity"
        assert item["status"] in VALID_STATUSES, f"{feature_id}: invalid status"
        for field in (
            "health_index_eligible", "pressure_index_eligible", "context_dependent",
            "recency_required", "persistence_required", "evidence_confidence_required",
        ):
            parse_bool(item[field], field, feature_id)
        assert int(item["minimum_evidence_count"]) >= 1
        if item["polarity"] == "neutral/context":
            assert not parse_bool(item["health_index_eligible"], "health_index_eligible", feature_id), (
                f"{feature_id}: neutral/context feature cannot directly enter health index"
            )
        assert item["missing_data_policy"] != "missing_as_zero"

    for linkage in finance_doc["linkages"]:
        assert set(linkage["dimensions"]) <= dimension_ids
        assert set(linkage["features"]) <= set(feature_ids)
        assert linkage["status"] in VALID_STATUSES
        assert linkage["confidence"] in {"low", "medium", "high"}

    for intervention in interventions_doc["intervention_classes"]:
        assert set(intervention["related_dimensions"]) <= dimension_ids
        assert set(intervention["related_signals"]) <= set(feature_ids)
        assert intervention["status"] in VALID_STATUSES

    assert REQUIRED_CONFIG <= set(config), "required methodology metadata missing"
    assert config["index_methodology_version"] == "0.1.0"
    assert config["status"] == "development-only"
    assert config["validated"] is False
    assert config["production_scoring_enabled"] is False
    assert set(config["dimension_weights"]) == dimension_ids
    assert math.isclose(sum(config["dimension_weights"].values()), 1.0, abs_tol=1e-12)
    assert "PROVISIONAL" in config["rating_bands_status"]
    assert config["selected_normalisation_method"] is None
    assert config["recency_function"]["selected"] is None

    for name in (
        "PIOTW_INDEX_SPEC_v0.1.md", "PEER_BENCHMARK_SPEC_v0.1.md",
        "VALIDATION_PLAN_v0.1.md",
    ):
        text = (BASE / name).read_text(encoding="utf-8")
        assert "0.1.0" in text
        assert "NOT VALIDATED" in text or "NOT EMPIRICALLY VALIDATED" in text or "NO VALIDATION RESULTS" in text

    return {
        "methodology_version": config["index_methodology_version"],
        "dimensions": len(dimensions),
        "features": len(features),
        "financial_linkages": len(finance_doc["linkages"]),
        "intervention_classes": len(interventions_doc["intervention_classes"]),
    }


if __name__ == "__main__":
    result = validate()
    print("PIOTW Index methodology registry validation: PASS")
    for key, value in result.items():
        print(f"  {key}: {value}")
