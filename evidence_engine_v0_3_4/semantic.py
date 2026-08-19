from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Protocol

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

DECISIONS = {"accept", "reject", "ambiguous"}
STATUSES = {"current", "ongoing", "planned", "historical", "hypothetical", "ambiguous"}
ACCEPT_REASONS = {"DIRECT_CURRENT_EVENT", "DIRECT_ONGOING_CONDITION", "DIRECT_PLANNED_EVENT",
                  "DIRECT_SEGMENT_EVENT", "DIRECT_SUBSIDIARY_EVENT"}
REJECT_REASONS = {"GENERIC_RISK", "HYPOTHETICAL_ONLY", "THIRD_PARTY_ONLY", "BIOGRAPHY",
    "LEGAL_REFERENCE", "CROSS_REFERENCE_ONLY", "HEADING_ONLY", "ACCOUNTING_DEFINITION",
    "ACCOUNTING_MEASURE_ONLY", "HISTORICAL_ONLY", "NEGATED", "WRONG_ENTITY", "WRONG_CONTEXT",
    "MALFORMED_FRAGMENT", "INSUFFICIENT_SUPPORT"}
AMBIGUOUS_REASONS = {"SUBJECT_AMBIGUOUS", "TIMING_AMBIGUOUS", "EVENT_TYPE_AMBIGUOUS",
                     "SOURCE_FRAGMENT_AMBIGUOUS"}
REASON_CODES = ACCEPT_REASONS | REJECT_REASONS | AMBIGUOUS_REASONS


def _visible_source_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\\u2022", "•")
    value = value.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    value = "".join(char for char in value
        if not unicodedata.category(char).startswith("C"))
    return re.sub(r"\s+", " ", value).strip()


@dataclass(frozen=True)
class SemanticCandidate:
    target_company: str
    candidate_event_type: str
    exact_candidate_span: str
    context: str
    heading: str | None
    publication_date: str | None
    deterministic_metadata: dict


@dataclass(frozen=True)
class SemanticDecision:
    decision: str
    event_type: str | None
    subject_type: str
    event_status: str
    scope: str | None
    evidence_supported: bool
    exact_support_span: str | None
    reason_code: str
    short_reason: str
    provider: str
    model_version: str
    prompt_version: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0

    @classmethod
    def from_dict(cls, raw: dict, *, provider: str, model_version: str,
                  prompt_version: str, candidate: SemanticCandidate,
                  latency_ms: int = 0, input_tokens: int = 0,
                  output_tokens: int = 0) -> SemanticDecision:
        required = {"decision", "event_type", "subject_type", "event_status", "scope",
            "evidence_supported", "exact_support_span", "reason_code", "short_reason"}
        if set(raw) != required or raw["decision"] not in DECISIONS or raw["reason_code"] not in REASON_CODES:
            raise ValueError("invalid semantic output schema")
        if (not isinstance(raw["subject_type"], str)
                or not isinstance(raw["short_reason"], str)
                or not isinstance(raw["evidence_supported"], bool)
                or raw["event_type"] is not None and not isinstance(raw["event_type"], str)
                or raw["scope"] is not None and not isinstance(raw["scope"], str)
                or raw["exact_support_span"] is not None
                and not isinstance(raw["exact_support_span"], str)):
            raise ValueError("invalid semantic output field type")
        if raw["event_status"] not in STATUSES:
            raise ValueError("invalid event status")
        if raw["decision"] == "accept":
            span = raw["exact_support_span"]
            if span and span not in candidate.context:
                normalized_span = _visible_source_text(span)
                normalized_candidate = _visible_source_text(candidate.exact_candidate_span)
                if (normalized_span and normalized_span in normalized_candidate
                        and candidate.exact_candidate_span in candidate.context):
                    span = candidate.exact_candidate_span
            if not raw["evidence_supported"] or not span or span not in candidate.context:
                raise ValueError("accepted decision requires an exact supplied evidence span")
            if raw["event_type"] != candidate.candidate_event_type:
                allowed = candidate.deterministic_metadata.get("allowed_remaps", [])
                if raw["event_type"] not in allowed:
                    raise ValueError("unsupported event remap")
        elif raw["evidence_supported"] or raw["exact_support_span"] is not None:
            raise ValueError("non-accepted decision cannot assert direct support")
        if raw["decision"] == "reject" and raw["reason_code"] not in REJECT_REASONS:
            raise ValueError("reject decision requires a reject reason")
        if raw["decision"] == "ambiguous" and raw["reason_code"] not in AMBIGUOUS_REASONS:
            raise ValueError("ambiguous decision requires an ambiguous reason")
        if raw["decision"] == "accept" and raw["reason_code"] not in ACCEPT_REASONS:
            raise ValueError("accept decision requires an accept reason")
        values = {key: raw[key] for key in required}
        if raw["decision"] == "accept":
            values["exact_support_span"] = span
        return cls(**values, provider=provider,
            model_version=model_version, prompt_version=prompt_version,
            latency_ms=latency_ms, input_tokens=input_tokens, output_tokens=output_tokens)


class SemanticVerifier(Protocol):
    provider: str
    model_version: str
    prompt_version: str

    def verify(self, candidate: SemanticCandidate) -> SemanticDecision: ...

    def verify_many(self, candidates: Sequence[SemanticCandidate]) -> list[SemanticDecision]: ...


def fail_closed(candidate: SemanticCandidate, reason: str, *, provider: str,
                model: str, prompt: str) -> SemanticDecision:
    return SemanticDecision("ambiguous", None, "unknown", "ambiguous", None, False, None,
        "SOURCE_FRAGMENT_AMBIGUOUS", reason, provider, model, prompt)


class MockSemanticVerifier:
    provider = "mock"
    model_version = "mock-v1"
    prompt_version = "semantic-event-v0.3.4"

    def __init__(self, responses: list[dict] | None = None, error: Exception | None = None):
        self.responses = list(responses or [])
        self.error = error

    def verify(self, candidate: SemanticCandidate) -> SemanticDecision:
        if self.error: raise self.error
        raw = self.responses.pop(0)
        return SemanticDecision.from_dict(raw, provider=self.provider,
            model_version=self.model_version, prompt_version=self.prompt_version,
            candidate=candidate)


class DeterministicSemanticVerifier:
    provider = "deterministic_semantic_development"
    model_version = "semantic-rules-v0.3.4"
    prompt_version = "semantic-event-v0.3.4"

    EXCLUSIONS: ClassVar[list[tuple[str, str]]] = [
        ("LEGAL_REFERENCE", r"\b(?:litigation|lawsuits?|legal proceedings?|claims? alleging)\b"),
        ("CROSS_REFERENCE_ONLY", r"^\s*(?:see|refer to) (?:note|the section|item)\b"),
        ("ACCOUNTING_DEFINITION", r"\b(?:represent gross reductions|for accounting purposes|are defined as|(?:restructuring|impairment) (?:costs|charges) consist of)\b"),
        ("HEADING_ONLY", r"^\s*(?:cost savings plans?|restructuring(?: costs| charges)?|component shortages)\.?\s*$"),
        ("GENERIC_RISK", r"\b(?:may be subject to|could affect|often increases during periods|risk of)\b"),
        ("MALFORMED_FRAGMENT", r"^(?:\s*table of contents\s*)$|\byear in review\b.{0,80}\$\d"),
    ]

    def verify(self, candidate: SemanticCandidate) -> SemanticDecision:
        started = time.perf_counter(); span = candidate.exact_candidate_span
        reason = next((code for code, pattern in self.EXCLUSIONS
                       if re.search(pattern, span, re.IGNORECASE | re.DOTALL)), None)
        meta = candidate.deterministic_metadata
        if meta.get("subject_type") not in {"target_company", "target_segment", "target_subsidiary"}:
            reason = "THIRD_PARTY_ONLY" if meta.get("subject_type") != "unknown" else "WRONG_ENTITY"
        if meta.get("factual_status") in {"generic_risk", "hypothetical_risk"}:
            reason = "HYPOTHETICAL_ONLY"
        if reason:
            raw = {"decision": "reject", "event_type": None,
                "subject_type": meta.get("subject_type", "unknown"),
                "event_status": "hypothetical" if reason in {"GENERIC_RISK", "HYPOTHETICAL_ONLY"} else "ambiguous",
                "scope": None, "evidence_supported": False, "exact_support_span": None,
                "reason_code": reason, "short_reason": "The supplied span does not directly establish the proposed target-company event."}
        elif len(span) < 25 or not re.search(r"[.!?]$", span.strip()):
            raw = {"decision": "ambiguous", "event_type": None,
                "subject_type": meta.get("subject_type", "unknown"), "event_status": "ambiguous",
                "scope": meta.get("entity_scope"), "evidence_supported": False,
                "exact_support_span": None, "reason_code": "SOURCE_FRAGMENT_AMBIGUOUS",
                "short_reason": "The fragment lacks enough complete syntax for a direct event decision."}
        else:
            status = meta.get("event_status", "current")
            raw = {"decision": "accept", "event_type": candidate.candidate_event_type,
                "subject_type": meta.get("subject_type", "target_company"),
                "event_status": status if status in STATUSES else "current",
                "scope": meta.get("entity_scope"), "evidence_supported": True,
                "exact_support_span": span, "reason_code": (
                    "DIRECT_SEGMENT_EVENT" if meta.get("subject_type") == "target_segment"
                    else "DIRECT_SUBSIDIARY_EVENT" if meta.get("subject_type") == "target_subsidiary"
                    else "DIRECT_PLANNED_EVENT" if status == "planned"
                    else "DIRECT_CURRENT_EVENT"),
                "short_reason": "The supplied span directly states the proposed event for a target-relevant subject."}
        return SemanticDecision.from_dict(raw, provider=self.provider, model_version=self.model_version,
            prompt_version=self.prompt_version, candidate=candidate,
            latency_ms=int((time.perf_counter() - started) * 1000))


class OpenAIResponsesSemanticVerifier:
    provider = "openai"
    prompt_version = "semantic-event-v0.3.4"

    def __init__(self, api_key: str, *, model: str = "gpt-5-mini", timeout: float = 30,
                 prompt_path: Path | None = None, max_output_tokens: int = 500,
                 max_retries: int = 2, client: object | None = None,
                 batch_size: int = 20, batch_max_output_tokens: int = 16000):
        self.api_key = api_key; self.model_version = model; self.timeout = timeout
        self.max_output_tokens = max_output_tokens
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.batch_max_output_tokens = batch_max_output_tokens
        self.prompt = (prompt_path or Path("config/evidence/semantic_event_prompt_v0_3_4.txt")).read_text()
        batch_path = Path("config/evidence/semantic_batch_transport_v0_3_4_1.txt")
        self.batch_prompt = batch_path.read_text() if batch_path.exists() else (
            "Evaluate each indexed candidate independently and return one indexed decision per candidate.")
        self.client = client or OpenAI(api_key=api_key, timeout=timeout, max_retries=0)
        self.last_call_record: dict | None = None
        self.last_batch_records: list[dict] = []

    @staticmethod
    def _safe_provider_error(exc: Exception) -> dict:
        if not isinstance(exc, APIStatusError):
            return {"status": None, "type": type(exc).__name__, "code": None,
                "param": None, "message": str(exc)[:500]}
        body = exc.body if isinstance(exc.body, dict) else {}
        error = body.get("error", body) if isinstance(body, dict) else {}
        return {"status": exc.status_code, "type": error.get("type"),
            "code": error.get("code"), "param": error.get("param"),
            "message": str(error.get("message", ""))[:500]}

    @staticmethod
    def _transient(exc: Exception) -> bool:
        if isinstance(exc, (APITimeoutError, APIConnectionError)):
            return True
        if not isinstance(exc, APIStatusError) or exc.status_code not in {429, 500, 502, 503}:
            return False
        safe = OpenAIResponsesSemanticVerifier._safe_provider_error(exc)
        message = (safe.get("message") or "").lower()
        return not (exc.status_code == 429 and ("requests per day" in message or "rpd" in message))

    def verify(self, candidate: SemanticCandidate) -> SemanticDecision:
        started = time.perf_counter()
        requested_at = datetime.now(UTC).isoformat()
        request_payload = {"model": self.model_version,
            "max_output_tokens": self.max_output_tokens,
            "input": [{"role": "system", "content": self.prompt},
                      {"role": "user", "content": json.dumps(asdict(candidate), sort_keys=True)}],
            "text": {"format": {"type": "json_schema", "name": "semantic_event_decision",
                "strict": True, "schema": semantic_json_schema()}}}
        retry_count = 0
        try:
            while True:
                try:
                    response = self.client.responses.create(**request_payload)
                    break
                except Exception as exc:
                    if retry_count >= self.max_retries or not self._transient(exc):
                        raise
                    time.sleep(0.25 * (2 ** retry_count)); retry_count += 1
            if response.status != "completed" or not response.output_text:
                raise ValueError(f"incomplete Responses API result: {response.status}")
            raw = json.loads(response.output_text)
            usage = response.usage
            decision = SemanticDecision.from_dict(raw, provider=self.provider,
                model_version=self.model_version, prompt_version=self.prompt_version,
                candidate=candidate, latency_ms=int((time.perf_counter() - started) * 1000),
                input_tokens=usage.input_tokens if usage else 0,
                output_tokens=usage.output_tokens if usage else 0)
            self.last_call_record = {"request_timestamp": requested_at,
                "candidate_span_hash": hashlib.sha256(candidate.exact_candidate_span.encode()).hexdigest(),
                "context_hash": hashlib.sha256(candidate.context.encode()).hexdigest(),
                "provider": self.provider, "model": self.model_version,
                "prompt_version": self.prompt_version, "schema_version": "semantic-schema-v0.3.4",
                "max_output_tokens": self.max_output_tokens, "temperature": None,
                "raw_output": raw,
                "output_hash": hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(),
                "parsed_decision": asdict(decision), "latency_ms": decision.latency_ms,
                "input_tokens": decision.input_tokens, "output_tokens": decision.output_tokens,
                "cache_hit": False, "retry_count": retry_count,
                "response_id": response.id, "response_status": response.status}
            return decision
        except Exception as exc:  # noqa: BLE001 - network/schema boundary must fail closed
            decision = fail_closed(candidate, f"semantic provider failure: {type(exc).__name__}",
                provider=self.provider, model=self.model_version, prompt=self.prompt_version)
            self.last_call_record = {"request_timestamp": requested_at,
                "candidate_span_hash": hashlib.sha256(candidate.exact_candidate_span.encode()).hexdigest(),
                "context_hash": hashlib.sha256(candidate.context.encode()).hexdigest(),
                "provider": self.provider, "model": self.model_version,
                "prompt_version": self.prompt_version, "schema_version": "semantic-schema-v0.3.4",
                "max_output_tokens": self.max_output_tokens, "temperature": None,
                "raw_output": None, "output_hash": hashlib.sha256(type(exc).__name__.encode()).hexdigest(),
                "parsed_decision": asdict(decision), "latency_ms": int((time.perf_counter() - started) * 1000),
                "input_tokens": 0, "output_tokens": 0, "cache_hit": False,
                "error_type": type(exc).__name__, "provider_error": self._safe_provider_error(exc),
                "retry_count": retry_count}
            return decision

    def verify_many(self, candidates: Sequence[SemanticCandidate]) -> list[SemanticDecision]:
        """Evaluate candidates in bounded transport batches without merging their decisions."""
        all_candidates = list(candidates)
        decisions: list[SemanticDecision] = []
        self.last_batch_records = []
        for offset in range(0, len(all_candidates), self.batch_size):
            chunk = all_candidates[offset:offset + self.batch_size]
            decisions.extend(self._verify_batch(chunk, batch_offset=offset))
        return decisions

    def _verify_batch(self, candidates: list[SemanticCandidate], *, batch_offset: int) -> list[SemanticDecision]:
        started = time.perf_counter()
        requested_at = datetime.now(UTC).isoformat()
        indexed = [{"candidate_index": index, **asdict(candidate)}
            for index, candidate in enumerate(candidates)]
        request_payload = {"model": self.model_version,
            "max_output_tokens": self.batch_max_output_tokens,
            "input": [{"role": "system", "content": self.prompt},
                      {"role": "system", "content": self.batch_prompt},
                      {"role": "user", "content": json.dumps({"candidates": indexed}, sort_keys=True)}],
            "text": {"format": {"type": "json_schema", "name": "semantic_event_batch",
                "strict": True, "schema": semantic_batch_json_schema()}}}
        retry_count = 0
        try:
            while True:
                try:
                    response = self.client.responses.create(**request_payload)
                    break
                except Exception as exc:
                    if retry_count >= self.max_retries or not self._transient(exc):
                        raise
                    time.sleep(0.25 * (2 ** retry_count)); retry_count += 1
            if response.status != "completed" or not response.output_text:
                raise ValueError(f"incomplete Responses API batch result: {response.status}")
            raw = json.loads(response.output_text)
            rows = raw.get("decisions") if isinstance(raw, dict) else None
            if not isinstance(rows, list):
                raise TypeError("batch result does not contain decisions")
            by_index: dict[int, list[dict]] = {}
            for row in rows:
                if isinstance(row, dict) and isinstance(row.get("candidate_index"), int):
                    by_index.setdefault(row["candidate_index"], []).append(row)
            usage = response.usage
            latency = int((time.perf_counter() - started) * 1000)
            parsed: list[SemanticDecision] = []
            invalid_indices: list[int] = []
            for index, candidate in enumerate(candidates):
                matches = by_index.get(index, [])
                try:
                    if len(matches) != 1:
                        raise ValueError("missing or duplicate candidate decision")
                    row = matches[0]
                    decision_raw = {key: value for key, value in row.items() if key != "candidate_index"}
                    decision = SemanticDecision.from_dict(decision_raw, provider=self.provider,
                        model_version=self.model_version, prompt_version=self.prompt_version,
                        candidate=candidate, latency_ms=latency)
                except Exception as exc:  # noqa: BLE001 - fail only the invalid candidate closed
                    invalid_indices.append(index)
                    decision = fail_closed(candidate, f"semantic batch item failure: {type(exc).__name__}",
                        provider=self.provider, model=self.model_version, prompt=self.prompt_version)
                parsed.append(decision)
            record = {"request_timestamp": requested_at, "provider": self.provider,
                "model": self.model_version, "prompt_version": self.prompt_version,
                "transport_version": "semantic-batch-v0.3.4.1",
                "schema_version": "semantic-batch-schema-v0.3.4.1",
                "batch_offset": batch_offset, "batch_size": len(candidates),
                "candidate_span_hashes": [hashlib.sha256(item.exact_candidate_span.encode()).hexdigest()
                    for item in candidates],
                "context_hashes": [hashlib.sha256(item.context.encode()).hexdigest()
                    for item in candidates],
                "max_output_tokens": self.batch_max_output_tokens, "temperature": None,
                "output_hash": hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(),
                "invalid_candidate_indices": invalid_indices, "latency_ms": latency,
                "input_tokens": usage.input_tokens if usage else 0,
                "output_tokens": usage.output_tokens if usage else 0,
                "cache_hit": False, "retry_count": retry_count,
                "response_id": response.id, "response_status": response.status}
            self.last_batch_records.append(record)
            return parsed
        except Exception as exc:  # noqa: BLE001 - batch provider boundary must fail closed
            latency = int((time.perf_counter() - started) * 1000)
            failed = [fail_closed(candidate, f"semantic batch provider failure: {type(exc).__name__}",
                provider=self.provider, model=self.model_version, prompt=self.prompt_version)
                for candidate in candidates]
            self.last_batch_records.append({"request_timestamp": requested_at,
                "provider": self.provider, "model": self.model_version,
                "prompt_version": self.prompt_version,
                "transport_version": "semantic-batch-v0.3.4.1",
                "schema_version": "semantic-batch-schema-v0.3.4.1",
                "batch_offset": batch_offset, "batch_size": len(candidates),
                "candidate_span_hashes": [hashlib.sha256(item.exact_candidate_span.encode()).hexdigest()
                    for item in candidates],
                "context_hashes": [hashlib.sha256(item.context.encode()).hexdigest()
                    for item in candidates],
                "max_output_tokens": self.batch_max_output_tokens, "temperature": None,
                "raw_output": None, "output_hash": hashlib.sha256(type(exc).__name__.encode()).hexdigest(),
                "latency_ms": latency, "input_tokens": 0, "output_tokens": 0,
                "cache_hit": False, "retry_count": retry_count,
                "error_type": type(exc).__name__, "provider_error": self._safe_provider_error(exc)})
            return failed


def semantic_json_schema() -> dict:
    return {"type": "object", "additionalProperties": False,
        "required": ["decision", "event_type", "subject_type", "event_status", "scope",
            "evidence_supported", "exact_support_span", "reason_code", "short_reason"],
        "properties": {"decision": {"enum": sorted(DECISIONS)},
            "event_type": {"type": ["string", "null"]}, "subject_type": {"type": "string"},
            "event_status": {"enum": sorted(STATUSES)}, "scope": {"type": ["string", "null"]},
            "evidence_supported": {"type": "boolean"},
            "exact_support_span": {"type": ["string", "null"]},
            "reason_code": {"enum": sorted(REASON_CODES)}, "short_reason": {"type": "string"}}}


def semantic_contract_json_schema(candidate: SemanticCandidate,
                                  evidence_pointer: str | None = None) -> dict:
    """Strict representation of the existing decision contract for one candidate.

    The wrapper allows supported nested ``anyOf`` branches while keeping every
    original decision field and meaning unchanged.
    """
    pointer = evidence_pointer or "span_" + hashlib.sha256(
        json.dumps(asdict(candidate), sort_keys=True).encode()).hexdigest()
    common = {"subject_type": {"type": "string"},
        "event_status": {"enum": sorted(STATUSES)}, "scope": {"type": ["string", "null"]},
        "short_reason": {"type": "string"}}
    required = ["decision", "event_type", "subject_type", "event_status", "scope",
        "evidence_supported", "evidence_span_id", "reason_code", "short_reason"]

    def branch(decision: str, reasons: set[str], *, accepted: bool) -> dict:
        properties = {"decision": {"enum": [decision]}, **common,
            "reason_code": {"enum": sorted(reasons)},
            "evidence_supported": {"enum": [accepted]},
            "evidence_span_id": ({"enum": [pointer]}
                if accepted else {"enum": ["span_none"]}),
            "event_type": ({"enum": sorted({candidate.candidate_event_type,
                *candidate.deterministic_metadata.get("allowed_remaps", [])})}
                if accepted else {"type": ["string", "null"]})}
        return {"type": "object", "additionalProperties": False,
            "required": required, "properties": properties}

    return {"type": "object", "additionalProperties": False, "required": ["result"],
        "properties": {"result": {"anyOf": [
            branch("accept", ACCEPT_REASONS, accepted=True),
            branch("reject", REJECT_REASONS, accepted=False),
            branch("ambiguous", AMBIGUOUS_REASONS, accepted=False)]}}}


def semantic_batch_json_schema() -> dict:
    item = semantic_json_schema()
    item = {**item, "required": ["candidate_index", *item["required"]],
        "properties": {"candidate_index": {"type": "integer", "minimum": 0},
            **item["properties"]}}
    return {"type": "object", "additionalProperties": False, "required": ["decisions"],
        "properties": {"decisions": {"type": "array", "items": item}}}


class SemanticDecisionCache:
    def __init__(self, path: Path):
        self.path = path; self.records = json.loads(path.read_text()) if path.exists() else {}

    @staticmethod
    def key(candidate: SemanticCandidate, verifier: SemanticVerifier,
            taxonomy_version: str) -> str:
        value = {"candidate_span_hash": hashlib.sha256(candidate.exact_candidate_span.encode()).hexdigest(),
            "context_hash": hashlib.sha256(candidate.context.encode()).hexdigest(),
            "taxonomy_version": taxonomy_version, "prompt_version": verifier.prompt_version,
            "schema_version": "semantic-schema-v0.3.4", "provider": verifier.provider,
            "model_version": verifier.model_version,
            "max_output_tokens": getattr(verifier, "max_output_tokens", None), "temperature": None}
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

    def get(self, key: str) -> dict | None: return self.records.get(key)

    def put(self, key: str, decision: SemanticDecision) -> None:
        self.records[key] = asdict(decision); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.records, indent=2, sort_keys=True) + "\n")
