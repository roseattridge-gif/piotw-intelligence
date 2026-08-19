from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from openai import APIStatusError, OpenAI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.semantic import (
    OpenAIResponsesSemanticVerifier,
    SemanticCandidate,
)

MODEL = "gpt-5-mini"
OUTPUT = ROOT / "data/derived/evidence_engine_v0_3_4_provider_preflight.json"


def safe_error(exc: Exception) -> dict:
    if not isinstance(exc, APIStatusError):
        return {"status": None, "type": type(exc).__name__, "code": None,
            "param": None, "message": str(exc)[:500]}
    body = exc.body if isinstance(exc.body, dict) else {}
    error = body.get("error", body) if isinstance(body, dict) else {}
    return {"status": exc.status_code, "type": error.get("type"),
        "code": error.get("code"), "param": error.get("param"),
        "message": str(error.get("message", ""))[:500]}


def timed_call(fn) -> tuple[object, int]:
    started = time.perf_counter(); result = fn()
    return result, round((time.perf_counter() - started) * 1000)


def write_and_stop(result: dict) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])
    raise SystemExit(1)


def main() -> None:
    key = os.environ.get("OPENAI_API_KEY")
    result = {"version": "0.3.4", "provider": "openai", "model": MODEL,
        "run_at": datetime.now(UTC).isoformat(), "credential_present": bool(key),
        "scientific_gate_data_used": False, "tests": {}}
    if not key or key == "PASTE_KEY_HERE":
        result["status"] = "MODEL_PROVIDER_PREFLIGHT_FAILED"
        result["failure"] = "credential_absent"
        write_and_stop(result)

    client = OpenAI(api_key=key, max_retries=0)
    try:
        response, latency = timed_call(lambda: client.responses.create(model=MODEL,
            input="Return exactly the word OK.", max_output_tokens=256))
        returned_text = response.output_text.strip()
        passed = response.status == "completed" and returned_text == "OK"
        result["tests"]["minimal_unstructured"] = {"passed": passed,
            "response_status": response.status, "returned_text": returned_text[:100],
            "input_tokens": response.usage.input_tokens if response.usage else 0,
            "output_tokens": response.usage.output_tokens if response.usage else 0,
            "latency_ms": latency}
        if not passed:
            result["status"] = "MODEL_PROVIDER_PREFLIGHT_FAILED"
            result["failure"] = "minimal_unstructured_response_mismatch"
            write_and_stop(result)
    except Exception as exc:  # noqa: BLE001 - safe diagnostic boundary
        result["tests"]["minimal_unstructured"] = {"passed": False,
            "provider_error": safe_error(exc)}
        result["status"] = "MODEL_PROVIDER_PREFLIGHT_FAILED"
        result["failure"] = "minimal_unstructured_failed"
        write_and_stop(result)

    tiny_schema = {"type": "object", "additionalProperties": False,
        "required": ["decision", "reason"], "properties": {
            "decision": {"enum": ["accept", "reject", "ambiguous"]},
            "reason": {"type": "string"}}}
    try:
        response, latency = timed_call(lambda: client.responses.create(model=MODEL,
            input="Classify this trivial statement as accept: The synthetic test passed.",
            max_output_tokens=512, text={"format": {"type": "json_schema",
                "name": "synthetic_decision", "strict": True, "schema": tiny_schema}}))
        returned_text = response.output_text.strip()
        try:
            parsed = json.loads(returned_text)
        except json.JSONDecodeError as exc:
            result["tests"]["minimal_structured"] = {"passed": False,
                "response_status": response.status, "returned_text": returned_text[:200],
                "input_tokens": response.usage.input_tokens if response.usage else 0,
                "output_tokens": response.usage.output_tokens if response.usage else 0,
                "latency_ms": latency, "parse_error": type(exc).__name__}
            result["status"] = "MODEL_PROVIDER_PREFLIGHT_FAILED"
            result["failure"] = "minimal_structured_output_parse_failed"
            write_and_stop(result)
        passed = response.status == "completed" and set(parsed) == {"decision", "reason"}
        result["tests"]["minimal_structured"] = {"passed": passed,
            "response_status": response.status, "parsed_fields": sorted(parsed),
            "input_tokens": response.usage.input_tokens if response.usage else 0,
            "output_tokens": response.usage.output_tokens if response.usage else 0,
            "latency_ms": latency}
        if not passed:
            raise ValueError("minimal structured response did not validate")
    except Exception as exc:  # noqa: BLE001 - safe diagnostic boundary
        result["tests"]["minimal_structured"] = {"passed": False,
            "provider_error": safe_error(exc)}
        result["status"] = "MODEL_PROVIDER_PREFLIGHT_FAILED"
        result["failure"] = "minimal_structured_failed"
        write_and_stop(result)

    verifier = OpenAIResponsesSemanticVerifier(key, model=MODEL, max_output_tokens=1500,
        max_retries=0)
    synthetic = [
        ("accept", SemanticCandidate("Example Manufacturing plc", "site_closure",
            "During the quarter, Example Manufacturing closed its Sheffield facility and reduced its workforce by 120 employees.",
            "During the quarter, Example Manufacturing closed its Sheffield facility and reduced its workforce by 120 employees.",
            None, "2026-01-01", {"subject_type": "target_company", "entity_scope": "facility",
                "factual_status": "actual_current", "event_status": "current", "allowed_remaps": []})),
        ("reject", SemanticCandidate("Example Manufacturing plc", "site_closure",
            "Competitors may close facilities if market conditions deteriorate.",
            "Competitors may close facilities if market conditions deteriorate.", None, "2026-01-01",
            {"subject_type": "competitor", "entity_scope": "external",
                "factual_status": "hypothetical_risk", "event_status": "hypothetical",
                "allowed_remaps": []})),
    ]
    for expected, candidate in synthetic:
        decision = verifier.verify(candidate)
        record = verifier.last_call_record or {}
        passed = decision.decision == expected and (expected != "accept" or
            decision.exact_support_span in candidate.context)
        result["tests"][f"piotw_schema_{expected}"] = {"passed": passed,
            "decision": decision.decision, "reason_code": decision.reason_code,
            "support_span_valid": bool(decision.exact_support_span in candidate.context)
                if decision.exact_support_span else expected != "accept",
            "input_tokens": decision.input_tokens, "output_tokens": decision.output_tokens,
            "latency_ms": decision.latency_ms, "provider_error": record.get("provider_error")}
        if not passed:
            result["status"] = "MODEL_PROVIDER_PREFLIGHT_FAILED"
            result["failure"] = f"piotw_schema_{expected}_failed"
            write_and_stop(result)

    result["status"] = "MODEL_BACKED_GATE_RERUN_TECHNICALLY_ELIGIBLE"
    result["all_passed"] = True
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])


if __name__ == "__main__":
    main()
