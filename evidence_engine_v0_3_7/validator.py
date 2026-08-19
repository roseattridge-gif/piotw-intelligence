from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from .models import AtomicObservation, EvidenceZone, SemanticObservation


def validate_semantic_observation(zone: EvidenceZone, candidate: SemanticObservation) -> AtomicObservation:
    span = candidate.exact_evidence_span
    offset = zone.text.find(span) if span else -1
    decision = {"FACT": "ACCEPT", "NO_FACT": "REJECT", "AMBIGUOUS": "AMBIGUOUS"}[candidate.decision]
    reason = candidate.reason_code
    if candidate.decision == "FACT" and (not candidate.subject or not candidate.action_or_state or not candidate.object):
        decision, reason = "REJECT", "INCOMPLETE_ATOMIC_FACT"
    if span and offset < 0:
        decision, reason = "REJECT", "EVIDENCE_SPAN_NOT_IN_SOURCE"
    if candidate.entity_relationship == "UNCLEAR" and candidate.decision == "FACT":
        decision, reason = "AMBIGUOUS", "ENTITY_ATTRIBUTION_UNCLEAR"
    identity = f"{zone.company_id}|{zone.source_id}|{span}|{candidate.subject}|{candidate.action_or_state}|{candidate.object}"
    return AtomicObservation(
        observation_id=f"obs-037-{hashlib.sha256(identity.encode()).hexdigest()[:20]}",
        company_id=zone.company_id, source_id=zone.source_id, source_hash=zone.source_hash,
        evidence_span=span, evidence_start=zone.start + offset if offset >= 0 else None,
        evidence_end=zone.start + offset + len(span) if offset >= 0 else None,
        subject=candidate.subject, action_or_state=candidate.action_or_state, object=candidate.object,
        timing=candidate.timing, polarity=candidate.polarity, scope=candidate.scope,
        entity_relationship=candidate.entity_relationship, publication_date=zone.publication_date,
        effective_date=None, confidence=candidate.confidence, decision=decision, reason_code=reason,
        extractor_version="evidence-engine-v0.3.7-development", model_version=candidate.model_version,
        created_at=datetime.now(UTC),
    )
