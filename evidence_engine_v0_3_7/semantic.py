from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .models import EvidenceZone, SemanticObservation


class SemanticObservationProvider(Protocol):
    def extract(self, zone: EvidenceZone) -> SemanticObservation: ...


class DevelopmentReviewReplayProvider:
    """Replays contaminated AI review rows to test plumbing; it is not an accuracy evaluator."""

    def __init__(self, path: Path):
        rows = json.loads(path.read_text())
        if len(rows) != 36 or any(row.get("formal_independent_human_gold") is not False for row in rows):
            raise ValueError("development review must contain 36 explicitly non-gold rows")
        if any(row.get("review_type") != "AI_ASSISTED_FINOPS_REVIEW" for row in rows):
            raise ValueError("review type boundary is missing")
        self.rows = {row["case_id"]: row for row in rows}

    def extract(self, zone: EvidenceZone) -> SemanticObservation:
        row = self.rows[zone.zone_id]
        decision = {"YES": "FACT", "NO": "NO_FACT", "AMBIGUOUS": "AMBIGUOUS"}[row["factual_observation"]]
        return SemanticObservation(
            decision=decision, subject=row["subject"], action_or_state=row["action_or_state"],
            object=row["object"], timing=row["timing"] or "UNCLEAR", polarity=row["polarity"] or "UNCLEAR",
            scope=row["scope"], entity_relationship=row["entity_relationship"] or "UNCLEAR",
            exact_evidence_span=row["exact_evidence_span"], confidence=row["reviewer_confidence"],
            reason_code=f"DEVELOPMENT_REPLAY_{row['factual_observation']}", model_version="ai-finops-review-replay-v1",
        )
