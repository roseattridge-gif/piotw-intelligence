from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from evidence_engine_v0_3_7.models import EvidenceZone, SemanticObservation
from evidence_engine_v0_3_7.validator import validate_semantic_observation
from evidence_engine_v0_3_7.zones import select_evidence_zones

ROOT = Path(__file__).resolve().parents[1]


def zone(text: str) -> EvidenceZone:
    return EvidenceZone(zone_id="z", company_id="issuer", source_id="s", source_hash="a" * 64,
                        publication_date=date(2026, 1, 1), text=text, start=0, end=len(text),
                        selection_reasons=["test"])


CASES = [
    ("The company closed its Leeds site in June.", "FACT", "HISTORICAL", "ISSUER", "ACCEPT"),
    ("The company closed its Leeds site in 2021.", "FACT", "HISTORICAL", "ISSUER", "ACCEPT"),
    ("The company has committed to open a Leeds site next year.", "FACT", "PLANNED_COMMITTED", "ISSUER", "ACCEPT"),
    ("The Leeds site could close if demand falls.", "NO_FACT", "HYPOTHETICAL", "ISSUER", "REJECT"),
    ("The company reduced its workforce by 80 roles.", "FACT", "COMPLETED_RECENT", "ISSUER", "ACCEPT"),
    ("The board appointed Jo Smith as CFO.", "FACT", "COMPLETED_RECENT", "ISSUER", "ACCEPT"),
    ("A supplier shut its factory for three days.", "FACT", "COMPLETED_RECENT", "SUPPLIER", "ACCEPT"),
    ("The issuer's component shortage stopped production.", "FACT", "CURRENT", "ISSUER", "ACCEPT"),
    ("Order backlog increased 12%.", "FACT", "COMPLETED_RECENT", "ISSUER", "ACCEPT"),
    ("Sales volumes declined 9%.", "FACT", "COMPLETED_RECENT", "ISSUER", "ACCEPT"),
    ("The company recalled 2,000 products.", "FACT", "COMPLETED_RECENT", "ISSUER", "ACCEPT"),
    ("Restructuring charges were £4m.", "AMBIGUOUS", "UNCLEAR", "ISSUER", "AMBIGUOUS"),
    ("Asset restructuring (53) (20) 670.", "NO_FACT", "UNCLEAR", "ISSUER", "REJECT"),
    ("A competitor opened a new factory.", "FACT", "COMPLETED_RECENT", "COMPETITOR", "ACCEPT"),
    ("The transformation should improve delivery.", "AMBIGUOUS", "UNCLEAR", "UNCLEAR", "AMBIGUOUS"),
]


@pytest.mark.parametrize("text,semantic_decision,timing,entity,expected", CASES)
def test_atomic_observation_adversarial_cases(text, semantic_decision, timing, entity, expected):
    candidate = SemanticObservation(
        decision=semantic_decision, subject="issuer" if entity == "ISSUER" else entity.casefold(),
        action_or_state="reported", object="operational condition", timing=timing, polarity="UNCLEAR",
        scope="stated scope", entity_relationship=entity, exact_evidence_span=text,
        confidence="HIGH", reason_code="SYNTHETIC", model_version="synthetic-v1",
    )
    assert validate_semantic_observation(zone(text), candidate).decision == expected


def test_high_recall_zone_selection_does_not_assign_event_identity():
    text = "Boilerplate governance text.\nSales volumes declined 9% and a plant closed.\nOther notes."
    selected = select_evidence_zones(company_id="issuer", source_id="s", publication_date=date(2026, 1, 1), text=text)
    assert len(selected) == 1
    assert "Sales volumes" in selected[0].text
    assert not hasattr(selected[0], "event_family")
    assert not hasattr(selected[0], "dimension")


def test_schema_excludes_scores_families_dimensions_and_predictions():
    schema = json.loads((ROOT / "config/evidence/atomic_observation_v0_3_7.schema.json").read_text())
    forbidden = {"event_family", "dimension", "risk_score", "operational_score", "prediction", "predicted_outcome"}
    assert forbidden.isdisjoint(schema["properties"])


def test_ai_review_is_explicitly_development_only():
    rows = json.loads((ROOT / "data/evidence_engine_v0_3_7/ai_assisted_finops_review_v1.json").read_text())
    assert len(rows) == 36
    assert all(row["review_type"] == "AI_ASSISTED_FINOPS_REVIEW" for row in rows)
    assert all(row["formal_independent_human_gold"] is False for row in rows)
