from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


TARGETS = {
    "material_capacity_expansion": {"dimension": "expansion", "horizon_months": 18, "prior": 0.15},
    "restructuring_announced": {"dimension": "pressure", "horizon_months": 12, "prior": 0.12},
    "profit_trading_warning": {"dimension": "pressure", "horizon_months": 6, "prior": 0.08},
    "operating_margin_deterioration": {"dimension": "pressure", "horizon_months": 12, "prior": 0.20},
    "senior_operational_leadership_change": {"dimension": "pressure", "horizon_months": 12, "prior": 0.15},
}


@dataclass(frozen=True)
class TargetContribution:
    evidence_id: str
    event_id: str | None
    relationship: str
    value: float
    explanation: str


def evidence_snapshot_hash(evidence_ids: list[str], feature_values: dict[str, float]) -> str:
    canonical = json.dumps({"evidence_ids": sorted(evidence_ids), "features": feature_values},
                           sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def target_probability(target: str, contributions: list[TargetContribution], scale: float = 4.0) -> float:
    prior = TARGETS[target]["prior"]
    logit = math.log(prior / (1 - prior))
    signed = sum(item.value if item.relationship == "supports" else -abs(item.value)
                 for item in contributions)
    return round(1 / (1 + math.exp(-(logit + scale * signed))), 6)


class PredictionRegistry:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def register(self, company_id: str, target: str, cutoff: datetime, model_version: str,
                 feature_values: dict[str, float], contributions: list[TargetContribution],
                 confidence: float, created_at: datetime, prediction_id: str | None = None) -> str:
        if target not in TARGETS:
            raise ValueError(f"Unknown target {target}")
        evidence_ids = [item.evidence_id for item in contributions]
        supports = [item.evidence_id for item in contributions if item.relationship == "supports"]
        contradicts = [item.evidence_id for item in contributions if item.relationship == "contradicts"]
        identifier = prediction_id or str(uuid4())
        probability = target_probability(target, contributions)
        self.connection.execute("""
            INSERT INTO predictions(
              prediction_id,company_id,prediction_target,probability,confidence,horizon_months,
              prediction_created_at,information_cutoff_at,model_version,feature_values_json,
              evidence_snapshot_hash,supporting_evidence_json,contradicting_evidence_json,status)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (identifier, company_id, target, probability, confidence,
              TARGETS[target]["horizon_months"], created_at.isoformat(), cutoff.isoformat(), model_version,
              json.dumps(feature_values, sort_keys=True), evidence_snapshot_hash(evidence_ids, feature_values),
              json.dumps(supports), json.dumps(contradicts), "open"))
        for item in contributions:
            self.connection.execute(
                "INSERT INTO prediction_evidence VALUES(?,?,?,?,?)",
                (identifier, item.evidence_id, item.event_id, item.relationship, item.value))
        return identifier
