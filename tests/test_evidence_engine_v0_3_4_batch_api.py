from __future__ import annotations

import json
from pathlib import Path

import pytest

from evidence_engine_v0_3_4.batch_api import (
    align_candidates_to_manifest,
    batch_line,
    candidate_key,
    parse_output_lines,
    prepare_requests,
    request_body,
    response_output_text,
    submit,
)
from evidence_engine_v0_3_4.evidence_pointer import (
    NONE_POINTER,
    build_evidence_pointer_mapping,
    evidence_pointer_id,
    resolve_evidence_pointer,
)
from evidence_engine_v0_3_4.semantic import SemanticCandidate, SemanticDecision
from scripts.run_model_backed_v034 import label_summary


def candidate(*, span: str = "Example Manufacturing closed its Sheffield facility this quarter."):
    return SemanticCandidate("Example Manufacturing plc", "site_closure", span, span, None,
        "2026-01-01", {"subject_type": "target_company", "entity_scope": "facility",
            "factual_status": "actual_current", "event_status": "current", "allowed_remaps": []})


def decision(decision_value: str) -> dict:
    if decision_value == "accept":
        return {"decision": "accept", "event_type": "site_closure",
            "subject_type": "target_company", "event_status": "current", "scope": "facility",
            "evidence_supported": True,
            "exact_support_span": "Example Manufacturing closed its Sheffield facility this quarter.",
            "reason_code": "DIRECT_CURRENT_EVENT", "short_reason": "Direct statement."}
    return {"decision": "reject", "event_type": None, "subject_type": "competitor",
        "event_status": "hypothetical", "scope": None, "evidence_supported": False,
        "exact_support_span": None, "reason_code": "THIRD_PARTY_ONLY",
        "short_reason": "The statement concerns competitors."}


def output_line(custom_id: str, raw_decision: dict) -> dict:
    return {"id": f"batch-request-{custom_id}", "custom_id": custom_id,
        "response": {"status_code": 200, "request_id": f"req-{custom_id}", "body": {
            "id": f"resp-{custom_id}", "status": "completed",
            "output": [{"type": "message", "content": [{"type": "output_text",
                "text": json.dumps(raw_decision)}]}],
            "usage": {"input_tokens": 100, "output_tokens": 50}}}, "error": None}


def test_single_candidate_request_preserves_frozen_contract():
    body = request_body(candidate())
    assert body["model"] == "gpt-5-mini"
    assert body["max_output_tokens"] == 2000
    assert body["text"]["format"]["name"] == "semantic_event_contract_decision"
    assert body["text"]["format"]["strict"] is True
    assert "anyOf" in body["text"]["format"]["schema"]["properties"]["result"]
    schema_text = json.dumps(body["text"]["format"]["schema"])
    assert candidate().exact_candidate_span not in schema_text
    assert "span_" in schema_text
    assert "candidates" not in json.dumps(body)
    assert batch_line(candidate(), "candidate-1")["url"] == "/v1/responses"


def test_prepare_jsonl_is_stable_and_custom_ids_are_unique(tmp_path: Path):
    candidates = [candidate(), candidate(span="We closed the Bristol facility during the year.")]
    first = prepare_requests(candidates, tmp_path / "one")
    second = prepare_requests(candidates, tmp_path / "two")
    assert first["input_jsonl_sha256"] == second["input_jsonl_sha256"]
    manifest = json.loads(Path(first["manifest_path"]).read_text())
    custom_ids = [row["custom_id"] for row in manifest["requests"]]
    assert len(custom_ids) == len(set(custom_ids)) == 2
    assert all(row["request_hash"] for row in manifest["requests"])
    assert manifest["outcomes_accessed"] is False


def test_scientific_candidates_align_to_preserved_manifest_order_without_content_change():
    first = candidate(span="First factual sentence.")
    second = candidate(span="Second factual sentence.")
    manifest = {"requests": [
        {"candidate_key": candidate_key(second)},
        {"candidate_key": candidate_key(first)}]}
    aligned = align_candidates_to_manifest([first, second], manifest)
    assert aligned == [second, first]
    assert {candidate_key(item) for item in aligned} == {
        candidate_key(first), candidate_key(second)}


def test_scientific_candidate_alignment_rejects_membership_drift():
    first = candidate(span="First factual sentence.")
    second = candidate(span="Second factual sentence.")
    manifest = {"requests": [{"candidate_key": candidate_key(first)}]}
    with pytest.raises(RuntimeError, match="membership differs"):
        align_candidates_to_manifest([first, second], manifest)


def test_batch_output_order_is_irrelevant_and_spans_validate(tmp_path: Path):
    accept = candidate()
    reject = candidate(span="Competitors may close facilities if demand declines.")
    prepared = prepare_requests([accept, reject], tmp_path)
    manifest = json.loads(Path(prepared["manifest_path"]).read_text())
    ids = [row["custom_id"] for row in manifest["requests"]]
    lines = [output_line(ids[1], decision("reject")), output_line(ids[0], decision("accept"))]
    parsed = parse_output_lines("\n".join(json.dumps(row) for row in lines), manifest)
    assert len(parsed["successful"]) == 2
    assert not parsed["failed"]
    assert {row["candidate_key"] for row in parsed["successful"]} == {
        candidate_key(accept), candidate_key(reject)}


def test_wrapped_strict_contract_output_parses(tmp_path: Path):
    prepared = prepare_requests([candidate()], tmp_path)
    manifest = json.loads(Path(prepared["manifest_path"]).read_text())
    custom_id = manifest["requests"][0]["custom_id"]
    parsed = parse_output_lines(json.dumps(output_line(custom_id,
        {"result": decision("accept")})), manifest)
    assert parsed["successful"][0]["parsed_decision"]["decision"] == "accept"


def test_pdf_control_character_span_is_resolved_to_exact_source():
    source = "The Company’s plant closed during the year."
    item = candidate(span=source)
    raw = decision("accept")
    raw["exact_support_span"] = "\x0bThe Company's plant closed during the year."
    raw["event_type"] = "site_closure"
    parsed = SemanticDecision.from_dict(raw, provider="test", model_version="test",
        prompt_version="test", candidate=item)
    assert parsed.exact_support_span == source


@pytest.mark.parametrize("mutation", [
    lambda raw: raw.pop("reason_code"),
    lambda raw: raw.update(decision="invalid"),
    lambda raw: raw.update(evidence_supported="true"),
    lambda raw: raw.update(extra_field="extra prose"),
])
def test_local_validator_rejects_structural_contract_failures(mutation):
    raw = decision("accept")
    mutation(raw)
    with pytest.raises(ValueError):
        SemanticDecision.from_dict(raw, provider="test", model_version="test",
            prompt_version="test", candidate=candidate())


@pytest.mark.parametrize(("decision_value", "reason", "evidence", "span"), [
    ("accept", "HISTORICAL_ONLY", True,
     "Example Manufacturing closed its Sheffield facility this quarter."),
    ("reject", "THIRD_PARTY_ONLY", True,
     "Example Manufacturing closed its Sheffield facility this quarter."),
    ("ambiguous", "DIRECT_CURRENT_EVENT", False, None),
])
def test_local_validator_rejects_cross_field_contract_failures(
        decision_value, reason, evidence, span):
    raw = decision("accept")
    raw.update(decision=decision_value, reason_code=reason,
        evidence_supported=evidence, exact_support_span=span)
    with pytest.raises(ValueError):
        SemanticDecision.from_dict(raw, provider="test", model_version="test",
            prompt_version="test", candidate=candidate())


@pytest.mark.parametrize("span", [
    'A "straight quote" and a backslash \\\\.',
    "Curly ‘quotes’ and an em—dash.",
    "Line one\nLine two\tTabbed.",
    "Control \x00 \x0b artefacts and a non\u00a0breaking space.",
    "Currency £ € ¥ and café Łódź.",
    "Malformed PDF \\u2022 marker " + "very long evidence " * 300,
])
def test_evidence_pointer_schema_is_source_safe(span: str):
    item = candidate(span=span)
    body = request_body(item)
    pointer = (body["text"]["format"]["schema"]["properties"]["result"]["anyOf"][0]
        ["properties"]["evidence_span_id"]["enum"][0])
    schema_text = json.dumps(body["text"]["format"]["schema"], ensure_ascii=False)
    assert span not in schema_text
    assert pointer in schema_text
    assert pointer.isascii()


def test_provider_pointer_output_resolves_before_local_contract_validation(tmp_path: Path):
    item = candidate()
    prepared = prepare_requests([item], tmp_path)
    manifest = json.loads(Path(prepared["manifest_path"]).read_text())
    request = manifest["requests"][0]
    pointer = evidence_pointer_id(request["evidence_pointer_mapping"])
    raw = decision("accept")
    raw.pop("exact_support_span")
    raw["evidence_span_id"] = pointer
    parsed = parse_output_lines(json.dumps(output_line(request["custom_id"],
        {"result": raw})), manifest)
    assert not parsed["failed"]
    assert parsed["successful"][0]["parsed_decision"]["exact_support_span"] == (
        item.exact_candidate_span)


def test_evidence_pointer_is_deterministic_and_provenance_is_exact():
    item = candidate()
    first = build_evidence_pointer_mapping(item, "evidence-test")
    second = build_evidence_pointer_mapping(item, "evidence-test")
    assert first == second
    pointer = evidence_pointer_id(first)
    assert resolve_evidence_pointer(pointer, first, item, decision="accept") == item.exact_candidate_span
    assert resolve_evidence_pointer(NONE_POINTER, first, item, decision="reject") is None
    assert first["pointers"][pointer]["exact_source_sha256"]


def test_evidence_pointer_changes_with_context_and_cannot_cross_resolve():
    first_item = candidate()
    second_item = SemanticCandidate(**{**first_item.__dict__,
        "context": "Prefix. " + first_item.context})
    first = build_evidence_pointer_mapping(first_item, "evidence-test")
    second = build_evidence_pointer_mapping(second_item, "evidence-test")
    assert evidence_pointer_id(first) != evidence_pointer_id(second)
    with pytest.raises(ValueError, match="unknown evidence pointer"):
        resolve_evidence_pointer(evidence_pointer_id(first), second, second_item, decision="accept")


def test_evidence_pointer_unknown_and_invalid_decision_usage_fail_closed():
    item = candidate()
    mapping = build_evidence_pointer_mapping(item, "evidence-test")
    with pytest.raises(ValueError, match="unknown evidence pointer"):
        resolve_evidence_pointer("span_" + "0" * 64, mapping, item, decision="accept")
    with pytest.raises(ValueError, match="requires a source evidence pointer"):
        resolve_evidence_pointer(NONE_POINTER, mapping, item, decision="accept")
    with pytest.raises(ValueError, match="non-accept"):
        resolve_evidence_pointer(evidence_pointer_id(mapping), mapping, item, decision="ambiguous")


def test_duplicate_source_occurrences_are_deduplicated_to_first_offset():
    span = "Repeated source sentence."
    item = SemanticCandidate(**{**candidate(span=span).__dict__,
        "context": f"{span} Middle. {span}"})
    mapping = build_evidence_pointer_mapping(item, "evidence-test")
    record = mapping["pointers"][evidence_pointer_id(mapping)]
    assert record["source_start"] == 0
    assert record["occurrence_count"] == 2


def test_partial_failure_is_retained_candidate_by_candidate(tmp_path: Path):
    prepared = prepare_requests([candidate(), candidate(span="Another factual sentence.")], tmp_path)
    manifest = json.loads(Path(prepared["manifest_path"]).read_text())
    custom_id = manifest["requests"][0]["custom_id"]
    parsed = parse_output_lines(json.dumps(output_line(custom_id, decision("accept"))), manifest)
    assert len(parsed["successful"]) == 1
    assert len(parsed["failed"]) == 1
    assert parsed["failed"][0]["error"]["type"] == "MISSING_BATCH_RESULT"


def test_truncated_output_retains_provider_completion_details(tmp_path: Path):
    prepared = prepare_requests([candidate()], tmp_path)
    manifest = json.loads(Path(prepared["manifest_path"]).read_text())
    custom_id = manifest["requests"][0]["custom_id"]
    row = output_line(custom_id, decision("accept"))
    row["response"]["body"]["output"][0]["content"][0]["text"] = '{"decision":"reject"'
    row["response"]["body"]["status"] = "incomplete"
    row["response"]["body"]["incomplete_details"] = {"reason": "max_output_tokens"}
    row["response"]["body"]["usage"]["output_tokens_details"] = {"reasoning_tokens": 41}
    parsed = parse_output_lines(json.dumps(row), manifest)
    assert not parsed["successful"]
    failure = parsed["failed"][0]
    assert failure["response_status"] == "incomplete"
    assert failure["incomplete_details"]["reason"] == "max_output_tokens"
    assert failure["reasoning_tokens"] == 41


def test_response_output_text_uses_responses_content_contract():
    body = {"output": [{"type": "message", "content": [
        {"type": "output_text", "text": "{\"decision\":\"accept\"}"}]}]}
    assert response_output_text(body) == '{"decision":"accept"}'


def test_existing_submission_is_restart_safe_and_does_not_resubmit(tmp_path: Path):
    state = {"batch_id": "batch-existing", "status": "in_progress"}
    state_path = tmp_path / "submission.json"
    state_path.write_text(json.dumps(state))
    assert submit(tmp_path, state_path, metadata={}) == state


def test_manifest_and_jsonl_do_not_contain_api_key(tmp_path: Path, monkeypatch):
    secret = "sk-proj-test-secret-never-write"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    prepared = prepare_requests([candidate()], tmp_path)
    assert secret not in Path(prepared["jsonl_path"]).read_text()
    assert secret not in Path(prepared["manifest_path"]).read_text()


def test_label_summary_uses_live_support_span_when_old_label_has_none(tmp_path: Path):
    labelled = tmp_path / "labels.csv"
    labelled.write_text("document_id,event_type,source_span,label\n"
        "doc-1,site_closure,The company closed the site.,supported\n")
    accepted = [{"document_id": "doc-1", "event_type": "site_closure",
        "source_span": "The company closed the site.", "support_span": "closed the site"}]
    result = label_summary(accepted, labelled, classification_field="label")
    assert result["provenance_completeness"] == 1
