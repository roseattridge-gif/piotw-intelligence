from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "reviewer_pack_human_ambiguity_v1"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_membership_and_independent_ordering():
    membership = json.loads((PACK / "internal_do_not_share/frozen_36_case_membership.json").read_text())
    a = json.loads((PACK / "reviewer_A/order_manifest.json").read_text())["case_ids_in_order"]
    b = json.loads((PACK / "reviewer_B/order_manifest.json").read_text())["case_ids_in_order"]
    expected = {row["case_id"] for row in membership["cases"]}
    assert len(expected) == 36
    assert set(a) == set(b) == expected
    assert a != b


def test_reviewer_materials_are_blinded():
    baseline = json.loads((PACK / "internal_do_not_share/comparison_baseline.json").read_text())
    forbidden_ids = {row["candidate_id"] for row in baseline["cases"]}
    for reviewer in ("reviewer_A", "reviewer_B"):
        cases = json.loads((PACK / reviewer / "cases.json").read_text())
        assert all(set(row) == {"case_id", "document_type", "form", "publication_date", "reporting_period", "bounded_evidence_context"} for row in cases)
        text = json.dumps(cases)
        assert not any(value in text for value in forbidden_ids)


def test_blank_templates_validate_and_have_no_answers():
    validator = load_script("validate_human_review_response_v1")
    for reviewer in ("reviewer_A", "reviewer_B"):
        template = PACK / reviewer / "response_template.json"
        rows = validator.validate(template, PACK / reviewer / "cases.json", allow_blank=True)
        assert all(not row["factual_observation"] for row in rows)


def test_material_disagreement_detection():
    compare = load_script("compare_human_review_v1")
    base = {"factual_observation": "YES", "timing": "CURRENT", "polarity": "POSITIVE", "entity_relationship": "ISSUER", "subject": "issuer", "action_or_state": "opened", "object": "site", "scope": "group"}
    same = dict(base)
    different = dict(base, timing="HISTORICAL")
    assert compare.materially_equal(base, same)
    assert not compare.materially_equal(base, different)


def test_adjudicated_comparison_fields_are_supported():
    compare = load_script("compare_human_review_v1")
    membership = json.loads((PACK / "internal_do_not_share/frozen_36_case_membership.json").read_text())
    rows = []
    for case in membership["cases"]:
        rows.append({"case_id": case["case_id"], "factual_observation": "YES", "timing": case["original_ai_timing"].upper(), "entity_relationship": case["original_ai_entity_relationship"]})
    result = {}
    compare.add_adjudicated_diagnostics(result, rows, membership)
    assert result["status"] == "FULL_POST_ADJUDICATION_DIAGNOSTIC"
    assert result["adjudicated_human_vs_ai_factual_agreement"]["total"] == 36
