from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import httpx2
import pytest
from openai import APIStatusError

from evidence_engine_v0_3_4.events import extract_event_pipeline
from evidence_engine_v0_3_4.semantic import (
    DeterministicSemanticVerifier,
    MockSemanticVerifier,
    OpenAIResponsesSemanticVerifier,
    SemanticCandidate,
    SemanticDecision,
    SemanticDecisionCache,
    semantic_batch_json_schema,
    semantic_json_schema,
)


def candidate(**changes):
    values = {"target_company": "Example plc", "candidate_event_type": "restructuring",
        "exact_candidate_span": "We initiated a restructuring programme during the year.",
        "context": "Results. We initiated a restructuring programme during the year.",
        "heading": "Results", "publication_date": "2024-03-01",
        "deterministic_metadata": {"subject_type": "target_company", "entity_scope": "group",
            "event_status": "current", "factual_status": "actual_current", "allowed_remaps": []}}
    values.update(changes)
    return SemanticCandidate(**values)


def accepted_raw(**changes):
    values = {"decision": "accept", "event_type": "restructuring", "subject_type": "target_company",
        "event_status": "current", "scope": "group", "evidence_supported": True,
        "exact_support_span": "We initiated a restructuring programme during the year.",
        "reason_code": "DIRECT_CURRENT_EVENT", "short_reason": "Direct statement."}
    values.update(changes)
    return values


def test_strict_schema_and_exact_span():
    decision = SemanticDecision.from_dict(accepted_raw(), provider="test", model_version="m1",
        prompt_version="p1", candidate=candidate())
    assert decision.decision == "accept"
    with pytest.raises(ValueError):
        SemanticDecision.from_dict(accepted_raw(exact_support_span="invented"), provider="test",
            model_version="m1", prompt_version="p1", candidate=candidate())
    assert semantic_json_schema()["additionalProperties"] is False


def test_reject_and_ambiguous_fail_closed():
    verifier = DeterministicSemanticVerifier()
    legal = candidate(exact_candidate_span="Claims arising from restructurings and litigation.",
        context="Claims arising from restructurings and litigation.")
    assert verifier.verify(legal).reason_code == "LEGAL_REFERENCE"
    fragment = candidate(exact_candidate_span="restructuring costs", context="restructuring costs")
    assert verifier.verify(fragment).decision == "reject"  # heading-only precedes fragment ambiguity


def test_mock_failure_becomes_ambiguous_in_pipeline():
    output = extract_event_pipeline("We initiated a restructuring programme during the year.",
        target_company="Example plc", verifier=MockSemanticVerifier(error=TimeoutError()))
    assert not output["accepted_events"]
    assert output["semantic_ambiguous"]
    assert output["semantic_ambiguous"][0]["semantic_reason_code"] == "SOURCE_FRAGMENT_AMBIGUOUS"


def test_cache_key_invalidates_on_prompt_and_model(tmp_path: Path):
    cache = SemanticDecisionCache(tmp_path / "cache.json")
    one = MockSemanticVerifier([accepted_raw()])
    key_one = cache.key(candidate(), one, "taxonomy-v1")
    decision = one.verify(candidate()); cache.put(key_one, decision)
    assert cache.get(key_one)
    two = MockSemanticVerifier([accepted_raw()]); two.model_version = "mock-v2"
    assert cache.key(candidate(), two, "taxonomy-v1") != key_one
    two.model_version = "mock-v1"; two.prompt_version = "p2"
    assert cache.key(candidate(), two, "taxonomy-v1") != key_one


def test_optional_remap_is_constrained():
    remapped = accepted_raw(event_type="cost_reduction")
    with pytest.raises(ValueError):
        SemanticDecision.from_dict(remapped, provider="test", model_version="m", prompt_version="p",
            candidate=candidate())
    allowed = candidate(deterministic_metadata={"subject_type": "target_company", "entity_scope": "group",
        "event_status": "current", "allowed_remaps": ["cost_reduction"]})
    assert SemanticDecision.from_dict(remapped, provider="test", model_version="m", prompt_version="p",
        candidate=allowed).event_type == "cost_reduction"


class FakeResponses:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes); self.calls = 0

    def create(self, **_kwargs):
        self.calls += 1; outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def fake_client(*outcomes):
    return SimpleNamespace(responses=FakeResponses(outcomes))


def sdk_response(raw):
    return SimpleNamespace(status="completed", output_text=__import__("json").dumps(raw),
        usage=SimpleNamespace(input_tokens=11, output_tokens=7), id="resp_synthetic")


def sdk_batch_response(*rows):
    return sdk_response({"decisions": list(rows)})


def status_error(status, code, message="provider error"):
    request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx2.Response(status, request=request)
    return APIStatusError(message, response=response,
        body={"error": {"type": "requests", "code": code, "param": None, "message": message}})


def test_official_sdk_response_shape_is_parsed():
    verifier = OpenAIResponsesSemanticVerifier("unused", client=fake_client(sdk_response(accepted_raw())))
    decision = verifier.verify(candidate())
    assert decision.decision == "accept"
    assert decision.input_tokens == 11
    assert verifier.last_call_record["response_id"] == "resp_synthetic"


def test_batch_schema_and_candidate_level_parsing():
    first = {"candidate_index": 0, **accepted_raw()}
    second = {"candidate_index": 1, **accepted_raw(decision="reject", event_type=None,
        subject_type="competitor", event_status="hypothetical", scope=None,
        evidence_supported=False, exact_support_span=None, reason_code="THIRD_PARTY_ONLY")}
    candidates = [candidate(), candidate(target_company="Second plc")]
    client = fake_client(sdk_batch_response(first, second))
    verifier = OpenAIResponsesSemanticVerifier("unused", client=client, batch_size=18)
    decisions = verifier.verify_many(candidates)
    assert [item.decision for item in decisions] == ["accept", "reject"]
    assert client.responses.calls == 1
    assert verifier.last_batch_records[0]["batch_size"] == 2
    assert semantic_batch_json_schema()["properties"]["decisions"]["type"] == "array"


def test_batch_missing_item_fails_only_missing_candidate_closed():
    first = {"candidate_index": 0, **accepted_raw()}
    client = fake_client(sdk_batch_response(first))
    verifier = OpenAIResponsesSemanticVerifier("unused", client=client, batch_size=18)
    decisions = verifier.verify_many([candidate(), candidate(target_company="Second plc")])
    assert decisions[0].decision == "accept"
    assert decisions[1].decision == "ambiguous"
    assert verifier.last_batch_records[0]["invalid_candidate_indices"] == [1]


def test_batch_transport_chunks_without_dropping_candidates():
    rows = [{"candidate_index": index, **accepted_raw()} for index in range(2)]
    client = fake_client(sdk_batch_response(*rows), sdk_batch_response({"candidate_index": 0,
        **accepted_raw()}))
    verifier = OpenAIResponsesSemanticVerifier("unused", client=client, batch_size=2)
    decisions = verifier.verify_many([candidate(), candidate(), candidate()])
    assert len(decisions) == 3
    assert client.responses.calls == 2
    assert [record["batch_size"] for record in verifier.last_batch_records] == [2, 1]


@pytest.mark.parametrize("status", [400, 401, 403])
def test_permanent_http_errors_fail_closed_without_retry(status):
    client = fake_client(status_error(status, "bad_request"))
    verifier = OpenAIResponsesSemanticVerifier("unused", client=client, max_retries=2)
    assert verifier.verify(candidate()).decision == "ambiguous"
    assert client.responses.calls == 1
    assert verifier.last_call_record["provider_error"]["status"] == status


def test_daily_429_does_not_retry():
    client = fake_client(status_error(429, "rate_limit_exceeded", "requests per day RPD reached"))
    verifier = OpenAIResponsesSemanticVerifier("unused", client=client, max_retries=2)
    assert verifier.verify(candidate()).decision == "ambiguous"
    assert client.responses.calls == 1


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_transient_provider_errors_retry(monkeypatch, status):
    monkeypatch.setattr("evidence_engine_v0_3_4.semantic.time.sleep", lambda _seconds: None)
    error = status_error(status, "rate_limit_exceeded" if status == 429 else "server_error")
    client = fake_client(error, sdk_response(accepted_raw()))
    verifier = OpenAIResponsesSemanticVerifier("unused", client=client, max_retries=2)
    assert verifier.verify(candidate()).decision == "accept"
    assert client.responses.calls == 2
    assert verifier.last_call_record["retry_count"] == 1


def test_incomplete_response_fails_closed():
    response = SimpleNamespace(status="incomplete", output_text="", usage=None, id="resp_incomplete")
    verifier = OpenAIResponsesSemanticVerifier("unused", client=fake_client(response))
    assert verifier.verify(candidate()).decision == "ambiguous"
