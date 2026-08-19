from __future__ import annotations

from evidence_engine_v0_1.models import Observation, ReviewDecision


def apply_review(observation: Observation, decision: ReviewDecision) -> Observation:
    if decision.observation_id != observation.observation_id:
        raise ValueError("review decision targets another observation")
    updated = observation.model_copy(deep=True)
    if decision.decision == "accept":
        updated.validation_status = "accepted"
    elif decision.decision == "reject":
        updated.validation_status = "rejected"
    else:
        updated.value = decision.corrected_value
        if decision.corrected_unit is not None:
            updated.unit = decision.corrected_unit
        updated.validation_status = "corrected"
    return updated

