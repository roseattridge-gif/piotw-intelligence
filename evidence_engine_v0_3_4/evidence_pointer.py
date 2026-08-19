from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict

from evidence_engine_v0_3_4.semantic import SemanticCandidate

NONE_POINTER = "span_none"
POINTER_PATTERN = re.compile(r"^span_[0-9a-f]{64}$")


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def build_evidence_pointer_mapping(candidate: SemanticCandidate,
                                   source_evidence_id: str) -> dict:
    span = candidate.exact_candidate_span
    context = candidate.context
    if not span or span not in context:
        raise ValueError("candidate exact span is not contained in context")
    offsets = []
    start = 0
    while True:
        position = context.find(span, start)
        if position < 0:
            break
        offsets.append(position)
        start = position + max(len(span), 1)
    canonical_start = offsets[0]
    canonical_end = canonical_start + len(span)
    pointer = "span_" + _digest({"candidate": asdict(candidate),
        "source_evidence_id": source_evidence_id, "source_start": canonical_start,
        "source_end": canonical_end, "exact_source_sha256": hashlib.sha256(span.encode()).hexdigest()})
    mapping = {"version": "evidence-pointer-v0.3.4.1", "source_evidence_id": source_evidence_id,
        "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
        "pointers": {pointer: {"exact_source_text": span,
            "exact_source_sha256": hashlib.sha256(span.encode()).hexdigest(),
            "source_start": canonical_start, "source_end": canonical_end,
            "occurrence_count": len(offsets)}, NONE_POINTER: None}}
    return mapping


def evidence_pointer_id(mapping: dict) -> str:
    values = [key for key in mapping["pointers"] if key != NONE_POINTER]
    if len(values) != 1 or not POINTER_PATTERN.fullmatch(values[0]):
        raise ValueError("evidence pointer mapping must contain one safe source pointer")
    return values[0]


def provider_pointer_options(mapping: dict) -> list[dict]:
    pointer = evidence_pointer_id(mapping)
    record = mapping["pointers"][pointer]
    return [{"evidence_span_id": pointer, "source_start": record["source_start"],
        "source_end": record["source_end"]}, {"evidence_span_id": NONE_POINTER}]


def resolve_evidence_pointer(pointer: str, mapping: dict, candidate: SemanticCandidate,
                             *, decision: str) -> str | None:
    if pointer not in mapping.get("pointers", {}):
        raise ValueError("unknown evidence pointer")
    if decision == "accept":
        if pointer == NONE_POINTER:
            raise ValueError("accept decision requires a source evidence pointer")
        record = mapping["pointers"][pointer]
        start = record["source_start"]; end = record["source_end"]
        source = record["exact_source_text"]
        if (candidate.context[start:end] != source
                or hashlib.sha256(source.encode()).hexdigest() != record["exact_source_sha256"]
                or source != candidate.exact_candidate_span):
            raise ValueError("evidence pointer provenance mismatch")
        return source
    if pointer != NONE_POINTER:
        raise ValueError("non-accept decision cannot return a source evidence pointer")
    return None
