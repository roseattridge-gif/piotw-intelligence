import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from piotw_intelligence.company_intelligence_v01 import assemble_company_intelligence

FIXTURE = Path("piotw-web/data/company-intelligence-v01/travis-perkins.json")


def payload() -> dict:
    return json.loads(FIXTURE.read_text())


def test_contract_validates_real_runtime_object_and_provenance():
    result = assemble_company_intelligence(payload())
    assert result.schema_version == "piotw-company-intelligence-v0.1"
    assert result.coverage.provenance_complete is True
    assert result.capabilities.predict == "NOT_BUILT"
    assert result.predictions[0].probability is None
    assert result.financial_impacts[0].status == "WITHHELD"


def test_unknown_evidence_reference_fails_closed():
    data = payload()
    data["conditions"][0]["evidence_ids"].append("invented-evidence")
    with pytest.raises(ValidationError, match="unknown evidence references"):
        assemble_company_intelligence(data)


def test_insufficient_peer_evidence_cannot_expose_a_number():
    data = payload()
    withheld = next(item for item in data["comparisons"] if item["status"] != "AVAILABLE")
    withheld["target_value"] = 5.12
    with pytest.raises(ValidationError, match="unavailable comparison cannot expose"):
        assemble_company_intelligence(data)


def test_prediction_requires_real_model_horizon_and_conditions():
    data = payload()
    prediction = data["predictions"][0]
    prediction.update({"status": "AVAILABLE", "probability": 0.7, "withheld_reason": None})
    with pytest.raises(ValidationError, match="available prediction requires"):
        assemble_company_intelligence(data)


def test_intervention_is_withheld_without_evidence():
    data = payload()
    intervention = data["interventions"][0]
    intervention.update({"status": "AVAILABLE", "title": "Test", "mechanism": "Test mechanism",
                         "supporting_condition_ids": [data["conditions"][0]["condition_id"]],
                         "evidence_ids": [], "withheld_reason": None})
    with pytest.raises(ValidationError, match="available intervention requires"):
        assemble_company_intelligence(data)


def test_financial_range_is_withheld_without_assumptions():
    data = payload()
    impact = data["financial_impacts"][0]
    impact.update({"status": "AVAILABLE", "mechanism": "Test", "measure": "Test impact",
                   "low": 1, "base": 2, "high": 3, "currency": "GBP", "unit": "millions",
                   "incremental": True, "evidence_ids": [data["evidence"][0]["evidence_id"]],
                   "assumptions": [], "withheld_reason": None})
    with pytest.raises(ValidationError, match="available financial impact requires assumptions"):
        assemble_company_intelligence(data)


def test_runtime_assembler_contains_no_company_specific_answer_path():
    source = Path("piotw_intelligence/company_intelligence_v01.py").read_text().lower()
    assert "travis" not in source
    assert "company ==" not in source
    assert "company_id ==" not in source


def test_product_contract_cannot_claim_a_scientific_gate_run():
    data = payload()
    data["scientific_gate_run"] = True
    with pytest.raises(ValidationError):
        assemble_company_intelligence(data)
