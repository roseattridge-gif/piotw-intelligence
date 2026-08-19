from __future__ import annotations

from evidence_engine_v0_3_4.events import extract_event_pipeline as extract_v034_pipeline

from .semantic import DeterministicSemanticVerifierV035


def extract_event_pipeline(text: str, **kwargs: object) -> dict:
    kwargs.setdefault("verifier", DeterministicSemanticVerifierV035())
    result = extract_v034_pipeline(text, **kwargs)
    result["engine_version"] = "0.3.5-development"
    result["validation_status"] = "DEVELOPMENT_CONTAMINATED — NOT VALIDATION"
    return result

