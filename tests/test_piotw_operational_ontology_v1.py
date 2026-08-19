from pathlib import Path

import yaml

from evidence_engine_v0_1.guard import verify_frozen_isolation

ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = yaml.safe_load((ROOT / "config/piotw_operational_ontology_v1.yaml").read_text())
SOURCES = yaml.safe_load((ROOT / "config/piotw_source_registry_v1.yaml").read_text())


def _walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_candidate_ontology_has_stable_unique_dimensions_and_observations():
    assert ONTOLOGY["version"] == "1.0.0-candidate"
    assert "NOT YET EMPIRICALLY VALIDATED" in ONTOLOGY["status"]
    dimensions = [row["dimension_id"] for row in ONTOLOGY["dimension_definitions"]]
    observations = [row["observation_type"] for row in ONTOLOGY["observation_definitions"]]
    assert len(dimensions) == len(set(dimensions)) == 8
    assert len(observations) == len(set(observations))


def test_all_ontology_references_resolve():
    dimensions = {row["dimension_id"] for row in ONTOLOGY["dimension_definitions"]}
    observations = {row["observation_type"] for row in ONTOLOGY["observation_definitions"]}
    outcomes = {row["outcome_id"] for row in ONTOLOGY["outcome_definitions"]}
    source_families = {row["source_family"] for row in SOURCES["source_families"]}
    for row in ONTOLOGY["observation_definitions"]:
        assert set(row["dimension_ids"]) <= dimensions
        assert set(row["source_compatibility"]) <= source_families
    for mapped_dimensions in ONTOLOGY["event_observation_mappings"].values():
        assert set(mapped_dimensions) <= dimensions
    for row in ONTOLOGY["signal_definitions"]:
        assert set(row["input_observations"]) <= observations | {"atomic_event"}
        assert set(row["candidate_prediction_relationships"]) <= outcomes
    for row in SOURCES["source_families"]:
        assert set(row["candidate_outcomes"]) <= outcomes


def test_ontology_contains_no_predictive_weight_fields():
    forbidden = {"weight", "weights", "coefficient", "coefficients"}
    assert not (set(_walk(ONTOLOGY)) & forbidden)
    assert not (set(_walk(SOURCES)) & forbidden)


def test_source_registry_has_unique_families_and_valid_cadences():
    assert SOURCES["version"] == "1.0.0-candidate"
    families = [row["source_family"] for row in SOURCES["source_families"]]
    assert len(families) == len(set(families))
    units = set(SOURCES["cadence_units"])
    for row in SOURCES["source_families"]:
        assert {
            "natural_update_frequency",
            "point_in_time_reconstruction_quality",
            "likely_cost",
            "legal_access_risk",
            "implementation_difficulty",
            "signal_latency",
            "likely_commercial_relevance",
            "mvp_priority",
            "current_support_status",
            "jurisdiction",
            "access_method",
            "production_readiness",
        } <= row.keys()
        cadence = row["default_cadence"]
        assert cadence["unit"] in units
        assert isinstance(cadence["value"], int) and cadence["value"] > 0


def test_rules_1_0_0_protected_artifacts_remain_unchanged():
    assert len(verify_frozen_isolation(ROOT)) == 12
