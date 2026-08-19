from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from evidence_engine_v0_3_3.events import extract_event_pipeline as extract_v033_pipeline
from evidence_engine_v0_3_4.semantic import (
    DeterministicSemanticVerifier,
    SemanticCandidate,
    SemanticDecision,
    SemanticDecisionCache,
    SemanticVerifier,
    fail_closed,
)

TAXONOMY_VERSION = "event_taxonomy_v0_1"


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _context(event: dict, *, heading: str | None = None, max_chars: int = 2400) -> str:
    """Return only the candidate and its local deterministic context."""
    parts = [heading or "", event.get("nearby_context", ""), event["source_span"]]
    joined = "\n".join(part.strip() for part in parts if part and part.strip())
    if event["source_span"] not in joined:
        joined = event["source_span"]
    if len(joined) <= max_chars:
        return joined
    span = event["source_span"]
    position = joined.find(span)
    if position < 0 or len(span) >= max_chars:
        return span[:max_chars]
    flank = max((max_chars - len(span)) // 2, 0)
    start = max(position - flank, 0)
    end = min(start + max_chars, len(joined))
    start = max(end - max_chars, 0)
    return joined[start:end]


def _decision_from_cached(raw: dict) -> SemanticDecision:
    return SemanticDecision(**raw)


def extract_event_pipeline(
    text: str,
    *,
    target_company: str = "target company",
    publication_date: str | None = None,
    reporting_period: str | None = None,
    page_or_section: str | None = None,
    verifier: SemanticVerifier | None = None,
    cache: SemanticDecisionCache | None = None,
    max_context_chars: int = 2400,
) -> dict:
    base = extract_v033_pipeline(
        text,
        publication_date=publication_date,
        reporting_period=reporting_period,
        page_or_section=page_or_section,
    )
    verifier = verifier or DeterministicSemanticVerifier()
    accepted: list[dict] = []
    rejected: list[dict] = []
    ambiguous: list[dict] = []
    assessments: list[dict] = []
    cache_hits = 0
    provider_calls = 0
    prepared: list[dict] = []

    for event in base["accepted_events"]:
        context = _context(event, heading=page_or_section, max_chars=max_context_chars)
        candidate = SemanticCandidate(
            target_company=target_company,
            candidate_event_type=event["event_type"],
            exact_candidate_span=event["source_span"],
            context=context,
            heading=page_or_section,
            publication_date=publication_date,
            deterministic_metadata={
                "subject_type": event.get("subject_type"),
                "entity_scope": event.get("entity_scope"),
                "factual_status": event.get("factual_status"),
                "event_status": event.get("event_status"),
                "allowed_remaps": event.get("allowed_remaps", []),
            },
        )
        key = cache.key(candidate, verifier, TAXONOMY_VERSION) if cache else None
        cached = cache.get(key) if cache and key else None
        prepared.append({"event": event, "context": context, "candidate": candidate,
            "key": key, "cached": cached, "decision": None})

    unresolved = [item for item in prepared if not item["cached"]]
    if unresolved:
        candidates = [item["candidate"] for item in unresolved]
        try:
            verify_many = getattr(verifier, "verify_many", None)
            if callable(verify_many):
                batch_decisions = verify_many(candidates)
                provider_calls = (len(verifier.last_batch_records)
                    if hasattr(verifier, "last_batch_records") else 1)
            else:
                batch_decisions = [verifier.verify(candidate) for candidate in candidates]
                provider_calls = len(candidates)
            if len(batch_decisions) != len(unresolved):
                raise ValueError("semantic verifier returned the wrong decision count")
            for item, decision in zip(unresolved, batch_decisions, strict=True):
                item["decision"] = decision
                if cache and item["key"]:
                    cache.put(item["key"], decision)
        except Exception as exc:  # noqa: BLE001 - provider boundary must fail closed
            for item in unresolved:
                item["decision"] = fail_closed(item["candidate"],
                    f"semantic verifier failure: {type(exc).__name__}",
                    provider=verifier.provider, model=verifier.model_version,
                    prompt=verifier.prompt_version)

    for item in prepared:
        event = item["event"]
        context = item["context"]
        candidate = item["candidate"]
        key = item["key"]
        cached = item["cached"]
        if cached:
            decision = _decision_from_cached(cached)
            cache_hits += 1
        else:
            decision = item["decision"]
        enriched = {
            **event,
            "semantic_decision": decision.decision,
            "semantic_reason_code": decision.reason_code,
            "semantic_short_reason": decision.short_reason,
            "semantic_event_type": decision.event_type,
            "semantic_subject_type": decision.subject_type,
            "semantic_event_status": decision.event_status,
            "semantic_scope": decision.scope,
            "semantic_exact_support_span": decision.exact_support_span,
            "semantic_provider": decision.provider,
            "semantic_model_version": decision.model_version,
            "semantic_prompt_version": decision.prompt_version,
            "semantic_input_tokens": decision.input_tokens,
            "semantic_output_tokens": decision.output_tokens,
            "semantic_latency_ms": decision.latency_ms,
            "semantic_context_hash": hashlib.sha256(context.encode()).hexdigest(),
            "semantic_output_hash": _hash(asdict(decision)),
            "semantic_cache_key": key,
            "semantic_cache_hit": bool(cached),
            "deterministic_assessment": "accepted_for_semantic_adjudication",
            "final_decision": decision.decision,
            "final_reason": decision.reason_code,
        }
        assessments.append(enriched)
        if decision.decision == "accept":
            enriched["event_type"] = decision.event_type
            enriched["event_status"] = decision.event_status
            enriched["scope"] = decision.scope
            accepted.append(enriched)
        elif decision.decision == "reject":
            rejected.append(enriched)
        else:
            ambiguous.append(enriched)

    return {
        **base,
        "accepted_events": accepted,
        "event_rejections": base["event_rejections"] + rejected,
        "ambiguous_events": base["ambiguous_events"] + ambiguous,
        "semantic_assessments": assessments,
        "semantic_rejections": rejected,
        "semantic_ambiguous": ambiguous,
        "semantic_calls": provider_calls,
        "semantic_cache_hits": cache_hits,
        "semantic_provider": verifier.provider,
        "semantic_model_version": verifier.model_version,
        "model_backed": verifier.provider not in {"mock", "deterministic_semantic_development"},
    }


def extract_contextual_events_v034(text: str, **kwargs: object) -> list[dict]:
    pipeline = extract_event_pipeline(text, **kwargs)
    return [
        {
            "event_type": event["event_type"],
            "evidence_span": event["source_span"],
            "context_status": event["event_status"],
            "quantified": any(char.isdigit() for char in event["source_span"]),
            "scope": event["scope"],
            "confidence": event["confidence"],
            "candidate_ids": event["candidate_ids"],
            "subject_type": event["semantic_subject_type"],
            "entity_scope": event["entity_scope"],
            "factual_status": event["semantic_event_status"],
            "semantic_reason_code": event["semantic_reason_code"],
        }
        for event in pipeline["accepted_events"]
    ]
