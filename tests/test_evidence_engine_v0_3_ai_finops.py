from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_3.ai_finops import validate_import

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_ai_finops_import_is_explicitly_inadmissible_for_human_gate():
    metadata = json.loads((ROOT / "data/ai_finops_first_pass/import_metadata.json").read_text())
    assert metadata["reviewer_type"] == "AI_ASSISTED_FINOPS_FIRST_PASS"
    assert metadata["reviewer_identity"] == "OpenAI GPT-5.6 Sol"
    assert metadata["status"] == "exploratory_diagnostic"
    assert metadata["formal_gold"] is False
    assert metadata["admissible_for_model2_gate"] is False


def test_import_schema_ids_metadata_timestamps_and_evidence_are_valid():
    imported = validate_import(ROOT)
    assert len(imported["numerical"]) == 24
    assert len(imported["events"]) == 15
    assert len({row["document_id"] for row in imported["numerical"] + imported["events"]}) == 6


def test_formal_human_gold_remains_blank_and_matches_freeze_manifest():
    freeze = json.loads((ROOT / "data/evidence_engine_v0_3/annotation_freeze_manifest.json").read_text())
    for name in ("gold_observations.csv", "gold_events.csv"):
        path = ROOT / "data/evidence_engine_v0_3" / name
        assert digest(path) == freeze["blank_file_hashes"][name]
        assert list(csv.DictReader(path.open())) == []


def test_readiness_gate_and_protected_rules_are_unchanged():
    assert digest(ROOT / "docs/evidence-engine-v0.3-model2-readiness-gate.md") == (
        "d671a97b9a03135c6ce80d1bbc7d83c244abb36a2c253014a06e9915bc65381e"
    )
    assert len(verify_frozen_isolation(ROOT)) == 12


def test_comparison_is_diagnostic_and_albemarle_issue_is_separate():
    result = json.loads((ROOT / "data/derived/evidence_engine_v0_3_ai_finops_comparison.json").read_text())
    assert result["methodological_boundary"].startswith("AI-assisted reviewer diagnostic")
    assert result["official_readiness_status"] == "NOT READY"
    assert result["outcomes_accessed"] is False and result["model2_trained"] is False
    assert result["scope"]["documents"] == 6
    issue = result["source_pack_issues"][0]
    assert issue["document_id"] == "ee03-alb-0000915913-24-000156"
    assert issue["classification"] == "review_pack_source_completeness_defect"
    assert issue["piotw_primary_document_numeric_facts"] == 0
