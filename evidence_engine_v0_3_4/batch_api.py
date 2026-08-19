from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_3.ai_finops import compare_events, count_classes, validate_import
from evidence_engine_v0_3_4.events import extract_contextual_events_v034
from evidence_engine_v0_3_4.evidence_pointer import (
    build_evidence_pointer_mapping,
    evidence_pointer_id,
    provider_pointer_options,
    resolve_evidence_pointer,
)
from evidence_engine_v0_3_4.semantic import (
    SemanticCandidate,
    SemanticDecision,
    fail_closed,
    semantic_contract_json_schema,
)
from scripts.run_model_backed_v034 import (
    GM_TICKERS,
    INPUT_PRICE_PER_M,
    MODEL,
    NEW_TICKERS,
    OUTPUT_PRICE_PER_M,
    PROMPT_VERSION,
    ROOT,
    CollectingVerifier,
    benchmark_run,
    label_summary,
    run_documents,
    sha,
)

ENDPOINT = "/v1/responses"
COMPLETION_WINDOW = "24h"
SCHEMA_VERSION = "semantic-schema-v0.3.4"
EXECUTION_VERSION = "batch-api-execution-v0.3.4"
PROMPT_PATH = ROOT / "config/evidence/semantic_event_prompt_v0_3_4.txt"
CONFIG_PATH = ROOT / "config/evidence/semantic_verifier_v0_3_4.yaml"
BATCH_EXECUTION_CONFIG_PATH = ROOT / "config/evidence/semantic_batch_execution_v0_3_4.yaml"
EVIDENCE_POINTER_CONFIG_PATH = ROOT / "config/evidence/evidence_pointer_v0_3_4_1.yaml"
EVIDENCE_POINTER_TRANSPORT_PATH = ROOT / "config/evidence/semantic_evidence_pointer_transport_v0_3_4_1.txt"
TAXONOMY_PATH = ROOT / "config/evidence/event_taxonomy_v0_1.yaml"
RUN_DIR = ROOT / "data/derived/evidence_engine_v0_3_4_batch"
SCIENTIFIC_RERUN_DIR = RUN_DIR / "scientific_rerun_pointer_v1"
SCIENTIFIC_RERUN_ID = "SCIENTIFIC_SEMANTIC_GATE_RERUN_AFTER_MECHANICAL_CONTRACT_REPAIR"
PRIOR_SCIENTIFIC_BATCH_ID = "batch_6a83017941f481909f300700dd40f935"
MAX_OUTPUT_TOKENS = 2000
BATCH_COST_GUARD_USD = 5.0
TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: object) -> str:
    payload = value if isinstance(value, bytes) else canonical(value).encode()
    return hashlib.sha256(payload).hexdigest()


def tree_digest(paths: list[Path]) -> str:
    records = []
    for path in paths:
        if path.is_dir():
            files = sorted(item for item in path.rglob("*") if item.is_file())
        elif path.is_file():
            files = [path]
        else:
            raise FileNotFoundError(path)
        for item in files:
            records.append({"path": str(item.relative_to(ROOT)),
                "sha256": hashlib.sha256(item.read_bytes()).hexdigest()})
    return digest(records)


def repository_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True).stdout.strip()


def candidate_key(candidate: SemanticCandidate) -> str:
    return digest(asdict(candidate))


def align_candidates_to_manifest(candidates: list[SemanticCandidate],
                                 manifest: dict) -> list[SemanticCandidate]:
    by_key = {candidate_key(candidate): candidate for candidate in candidates}
    prior_keys = [row["candidate_key"] for row in manifest["requests"]]
    if len(by_key) != len(candidates):
        raise RuntimeError("rebuilt scientific candidates contain duplicate identities")
    if len(prior_keys) != len(set(prior_keys)):
        raise RuntimeError("preserved scientific manifest contains duplicate identities")
    if set(by_key) != set(prior_keys):
        raise RuntimeError("scientific candidate membership differs from preserved manifest")
    return [by_key[key] for key in prior_keys]


def candidate_id(candidate: SemanticCandidate) -> str:
    value = f"{candidate.target_company}|{candidate.candidate_event_type}|{candidate.exact_candidate_span}"
    return hashlib.sha256(value.encode()).hexdigest()[:20]


def request_body(candidate: SemanticCandidate) -> dict:
    context_hash = hashlib.sha256(candidate.context.encode()).hexdigest()
    mapping = build_evidence_pointer_mapping(candidate, f"evidence-{context_hash[:20]}")
    pointer = evidence_pointer_id(mapping)
    user_payload = {**asdict(candidate),
        "evidence_span_options": provider_pointer_options(mapping)}
    return {"model": MODEL, "max_output_tokens": MAX_OUTPUT_TOKENS,
        "input": [{"role": "system", "content": PROMPT_PATH.read_text()},
                  {"role": "system", "content": EVIDENCE_POINTER_TRANSPORT_PATH.read_text()},
                  {"role": "user", "content": json.dumps(user_payload, sort_keys=True)}],
        "text": {"format": {"type": "json_schema", "name": "semantic_event_contract_decision",
            "strict": True, "schema": semantic_contract_json_schema(candidate, pointer)}}}


def batch_line(candidate: SemanticCandidate, custom_id: str) -> dict:
    return {"custom_id": custom_id, "method": "POST", "url": ENDPOINT,
        "body": request_body(candidate)}


def _gate_rows() -> tuple[list[dict], list[dict], list[dict], dict]:
    imported = validate_import(ROOT)
    manifest_v3 = imported["corpus"]
    manifest_v2 = list(csv.DictReader((ROOT / "data/evidence_engine_v0_2/corpus_manifest.csv").open()))
    prior_ids = {row["document_id"] for row in csv.DictReader(
        (ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv").open())}
    prior_rows = [row for row in manifest_v3 if row["document_id"] in prior_ids]
    gm_rows = [row for row in manifest_v2 if row["ticker"] in GM_TICKERS]
    unseen_rows = [row for row in manifest_v2 if row["ticker"] in NEW_TICKERS]
    return prior_rows, gm_rows, unseen_rows, imported


def collect_frozen_candidates() -> list[SemanticCandidate]:
    collector = CollectingVerifier()
    benchmark_run(collector)
    prior_rows, gm_rows, unseen_rows, imported = _gate_rows()
    extractor = lambda text, **kwargs: extract_contextual_events_v034(
        text, verifier=collector, cache=None, **kwargs)
    compare_events(ROOT, imported, extractor=extractor)
    run_documents(prior_rows, "source_artifact", collector, None)
    run_documents(gm_rows, "local_artifact", collector, None)
    run_documents(unseen_rows, "local_artifact", collector, None)
    unique = {candidate_key(item): item for item in collector.candidates}
    return list(unique.values())


def prepare_requests(candidates: list[SemanticCandidate], output_dir: Path,
                     *, prefix: str = "piotw") -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "input.jsonl"
    manifest_path = output_dir / "request_manifest.json"
    rows: list[dict] = []
    manifest_rows: list[dict] = []
    custom_ids: set[str] = set()
    for index, candidate in enumerate(candidates):
        base_id = candidate_id(candidate)
        custom_id = f"{prefix}-{index:04d}-{base_id}"
        if custom_id in custom_ids:
            raise ValueError(f"duplicate batch custom_id: {custom_id}")
        custom_ids.add(custom_id)
        line = batch_line(candidate, custom_id)
        rows.append(line)
        context_hash = hashlib.sha256(candidate.context.encode()).hexdigest()
        source_evidence_id = f"evidence-{context_hash[:20]}"
        pointer_mapping = build_evidence_pointer_mapping(candidate, source_evidence_id)
        manifest_rows.append({"sequence": index, "candidate_id": base_id,
            "candidate_key": candidate_key(candidate), "custom_id": custom_id,
            "request_hash": digest(line), "context_hash": context_hash,
            "source_evidence_id": source_evidence_id,
            "source_span": candidate.exact_candidate_span,
            "evidence_pointer_mapping": pointer_mapping,
            "candidate": asdict(candidate)})
    jsonl_bytes = ("\n".join(canonical(row) for row in rows) + "\n").encode()
    jsonl_path.write_bytes(jsonl_bytes)
    manifest = {"execution_version": EXECUTION_VERSION, "endpoint": ENDPOINT,
        "completion_window": COMPLETION_WINDOW, "model": MODEL,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "prompt_version": PROMPT_VERSION, "schema_version": SCHEMA_VERSION,
        "candidate_count": len(rows), "input_jsonl_sha256": digest(jsonl_bytes),
        "prompt_sha256": sha(PROMPT_PATH),
        "schema_sha256": digest([semantic_contract_json_schema(candidate,
            evidence_pointer_id(build_evidence_pointer_mapping(candidate,
                f"evidence-{hashlib.sha256(candidate.context.encode()).hexdigest()[:20]}")))
            for candidate in candidates]),
        "taxonomy_sha256": sha(TAXONOMY_PATH), "config_sha256": sha(CONFIG_PATH),
        "batch_execution_config_sha256": sha(BATCH_EXECUTION_CONFIG_PATH),
        "evidence_pointer_config_sha256": sha(EVIDENCE_POINTER_CONFIG_PATH),
        "evidence_pointer_transport_sha256": sha(EVIDENCE_POINTER_TRANSPORT_PATH),
        "repository_commit": repository_commit(),
        "outcomes_accessed": False, "model2_trained": False, "requests": manifest_rows}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    manifest["manifest_sha256"] = sha(manifest_path)
    return {"jsonl_path": str(jsonl_path), "manifest_path": str(manifest_path), **manifest}


def prepare_scientific() -> dict:
    protected_before = verify_frozen_isolation(ROOT)
    candidates = collect_frozen_candidates()
    prior_manifest_path = RUN_DIR / "scientific_2000/request_manifest.json"
    prior_manifest = json.loads(prior_manifest_path.read_text())
    prior_keys = [row["candidate_key"] for row in prior_manifest["requests"]]
    candidates = align_candidates_to_manifest(candidates, prior_manifest)
    current_keys = [candidate_key(candidate) for candidate in candidates]
    if len(current_keys) != 685 or current_keys != prior_keys:
        raise RuntimeError("scientific candidate set differs from the frozen prior execution")
    prepared = prepare_requests(candidates, SCIENTIFIC_RERUN_DIR)
    input_chars = sum(len(canonical(row)) for row in prepared["requests"])
    conservative_input_tokens = (input_chars + 3) // 4
    estimated_cost = ((conservative_input_tokens * INPUT_PRICE_PER_M)
        + (prepared["candidate_count"] * MAX_OUTPUT_TOKENS * OUTPUT_PRICE_PER_M)) / 2_000_000
    if estimated_cost > BATCH_COST_GUARD_USD:
        raise RuntimeError(f"scientific Batch cost guard exceeded: ${estimated_cost:.4f}")
    if len(protected_before) != 12 or protected_before != verify_frozen_isolation(ROOT):
        raise RuntimeError("protected artefacts changed during batch preparation")
    prepared["scientific_execution_type"] = SCIENTIFIC_RERUN_ID
    prepared["prior_scientific_batch_id"] = PRIOR_SCIENTIFIC_BATCH_ID
    prepared["prior_candidate_manifest_sha256"] = sha(prior_manifest_path)
    prepared["candidate_set_exact_match_to_prior"] = True
    prepared["scientific_gate_threshold_config_sha256"] = sha(CONFIG_PATH)
    prepared["formal_human_gold_sha256"] = tree_digest([
        ROOT / "data/evidence_engine_v0_3/gold_observations.csv",
        ROOT / "data/evidence_engine_v0_3/gold_events.csv"])
    prepared["blinded_reviewer_packs_sha256"] = tree_digest([
        ROOT / "reviewer_pack_v0_3", ROOT / "reviewer_pack_v0_3_1"])
    prepared["prepared_at"] = datetime.now(UTC).isoformat()
    prepared["conservative_max_cost_usd"] = estimated_cost
    prepared["cost_guard_usd"] = BATCH_COST_GUARD_USD
    summary_path = SCIENTIFIC_RERUN_DIR / "preparation.json"
    summary_path.write_text(json.dumps({key: value for key, value in prepared.items()
        if key != "requests"}, indent=2, sort_keys=True) + "\n")
    return prepared


def synthetic_candidates() -> list[SemanticCandidate]:
    return [
        SemanticCandidate("Example Manufacturing plc", "site_closure",
            "Example Manufacturing closed its Sheffield facility this quarter.",
            "Example Manufacturing closed its Sheffield facility this quarter.", None,
            "2026-01-01", {"subject_type": "target_company", "entity_scope": "facility",
                "factual_status": "actual_current", "event_status": "current", "allowed_remaps": []}),
        SemanticCandidate("Example Manufacturing plc", "site_closure",
            "Competitors may close facilities if demand declines.",
            "Competitors may close facilities if demand declines.", None, "2026-01-01",
            {"subject_type": "competitor", "entity_scope": "external",
                "factual_status": "hypothetical_risk", "event_status": "hypothetical",
                "allowed_remaps": []}),
    ]


def contract_smoke_candidates() -> list[SemanticCandidate]:
    cases = [
        ("site_closure", "Example Manufacturing closed its Sheffield facility this quarter.",
         "target_company", "current"),
        ("site_closure", "Competitors may close facilities if demand declines.",
         "competitor", "hypothetical"),
        ("restructuring", "The wording does not establish who undertook the restructuring.",
         "unknown", "ambiguous"),
        ("cost_reduction", "The Group reduced discretionary expenditure during the year.",
         "target_company", "current"),
        ("restructuring", "No restructuring is planned by the Company.",
         "target_company", "planned"),
        ("supply_chain_constraint", "A supplier said its own factory may face disruption.",
         "supplier", "hypothetical"),
        ("labour_constraint", "The strike paused production at the Group's main plant.",
         "target_company", "current"),
        ("investment", "The Company invested £12m in R&D — including AI/data systems.",
         "target_company", "current"),
        ("growth", 'The Group reported “strong” demand in Europe and Asia.',
         "target_company", "current"),
        ("new_facility", "The Company opened the O'Brien facility in Łódź.",
         "target_company", "current"),
        ("operational_disruption", "The passage says only: \\\"disruption\\\".",
         "unknown", "ambiguous"),
        ("invalid_candidate_type", "The Company announced an action during the period. " * 40,
         "target_company", "current"),
    ]
    return [SemanticCandidate("Example Manufacturing plc", event_type, span, span, None,
        "2026-01-01", {"subject_type": subject, "entity_scope": "group",
            "factual_status": ("hypothetical_risk" if status == "hypothetical" else
                "actual_current"), "event_status": status, "allowed_remaps": []})
        for event_type, span, subject, status in cases]


def _safe_batch(batch: Any) -> dict:
    counts = getattr(batch, "request_counts", None)
    return {"batch_id": batch.id, "status": batch.status,
        "input_file_id": batch.input_file_id, "output_file_id": batch.output_file_id,
        "error_file_id": batch.error_file_id, "created_at": batch.created_at,
        "in_progress_at": batch.in_progress_at, "completed_at": batch.completed_at,
        "failed_at": batch.failed_at, "expired_at": batch.expired_at,
        "request_counts": {"total": getattr(counts, "total", 0),
            "completed": getattr(counts, "completed", 0), "failed": getattr(counts, "failed", 0)}}


def _download_text(client: OpenAI, file_id: str) -> str:
    response = client.files.content(file_id)
    if hasattr(response, "text"):
        return response.text
    content = response.read() if hasattr(response, "read") else bytes(response)
    return content.decode()


def submit(prepared_dir: Path, state_path: Path, *, metadata: dict[str, str]) -> dict:
    if state_path.exists():
        existing = json.loads(state_path.read_text())
        if existing.get("batch_id"):
            return existing
    client = OpenAI(max_retries=0)
    input_path = prepared_dir / "input.jsonl"
    with input_path.open("rb") as handle:
        uploaded = client.files.create(file=handle, purpose="batch")
    batch = client.batches.create(input_file_id=uploaded.id, endpoint=ENDPOINT,
        completion_window=COMPLETION_WINDOW, metadata=metadata)
    state = {**_safe_batch(batch), "submitted_at": datetime.now(UTC).isoformat(),
        "input_jsonl_sha256": sha(input_path), "provider": "openai", "model": MODEL}
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    return state


def refresh_status(state_path: Path) -> dict:
    state = json.loads(state_path.read_text())
    batch = OpenAI(max_retries=0).batches.retrieve(state["batch_id"])
    current = {**state, **_safe_batch(batch), "checked_at": datetime.now(UTC).isoformat()}
    state_path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
    return current


def response_output_text(body: dict) -> str:
    direct = body.get("output_text")
    if isinstance(direct, str) and direct:
        return direct
    parts: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if isinstance(content, dict) and content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    return "".join(parts)


def parse_output_lines(text: str, manifest: dict) -> dict:
    expected = {row["custom_id"]: row for row in manifest["requests"]}
    seen: set[str] = set()
    successes: list[dict] = []
    failures: list[dict] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        custom_id = raw.get("custom_id")
        if custom_id not in expected or custom_id in seen:
            raise ValueError(f"unexpected or duplicate custom_id: {custom_id}")
        seen.add(custom_id)
        manifest_row = expected[custom_id]
        response = raw.get("response") or {}
        error = raw.get("error")
        status_code = response.get("status_code")
        body = response.get("body") or {}
        usage = body.get("usage") or {}
        output_details = usage.get("output_tokens_details") or {}
        base = {"custom_id": custom_id, "candidate_id": manifest_row["candidate_id"],
            "candidate_key": manifest_row["candidate_key"], "request_hash": manifest_row["request_hash"],
            "context_hash": manifest_row["context_hash"], "source_evidence_id": manifest_row["source_evidence_id"],
            "source_span": manifest_row["source_span"], "response_status_code": status_code,
            "provider_request_id": response.get("request_id"), "raw_response_hash": digest(raw),
            "response_status": body.get("status"),
            "incomplete_details": body.get("incomplete_details"),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "reasoning_tokens": output_details.get("reasoning_tokens", 0)}
        if error or status_code != 200:
            failures.append({**base, "error": error or body.get("error") or {"status_code": status_code}})
            continue
        try:
            parsed = json.loads(response_output_text(body))
            if set(parsed) == {"result"} and isinstance(parsed["result"], dict):
                parsed = parsed["result"]
            candidate = SemanticCandidate(**manifest_row["candidate"])
            if "evidence_span_id" in parsed:
                resolved_span = resolve_evidence_pointer(parsed.pop("evidence_span_id"),
                    manifest_row["evidence_pointer_mapping"], candidate,
                    decision=parsed.get("decision"))
                parsed["exact_support_span"] = resolved_span
            decision = SemanticDecision.from_dict(parsed, provider="openai", model_version=MODEL,
                prompt_version=PROMPT_VERSION, candidate=candidate,
                input_tokens=usage.get("input_tokens", 0), output_tokens=usage.get("output_tokens", 0))
            successes.append({**base, "parsed_decision": asdict(decision),
                "input_tokens": decision.input_tokens, "output_tokens": decision.output_tokens})
        except Exception as exc:  # noqa: BLE001 - candidate-level parse boundary
            failures.append({**base, "error": {"type": type(exc).__name__, "message": str(exc)[:300]}})
    for custom_id in sorted(set(expected) - seen):
        row = expected[custom_id]
        failures.append({"custom_id": custom_id, "candidate_id": row["candidate_id"],
            "candidate_key": row["candidate_key"], "request_hash": row["request_hash"],
            "error": {"type": "MISSING_BATCH_RESULT"}})
    return {"expected": len(expected), "received": len(seen), "successful": successes,
        "failed": failures}


def collect(state_path: Path, prepared_dir: Path, output_dir: Path) -> dict:
    status = refresh_status(state_path)
    if status["status"] not in TERMINAL_STATUSES:
        return {"terminal": False, **status}
    client = OpenAI(max_retries=0)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_text = _download_text(client, status["output_file_id"]) if status.get("output_file_id") else ""
    error_text = _download_text(client, status["error_file_id"]) if status.get("error_file_id") else ""
    (output_dir / "raw_output.jsonl").write_text(output_text)
    (output_dir / "raw_errors.jsonl").write_text(error_text)
    manifest = json.loads((prepared_dir / "request_manifest.json").read_text())
    parsed = parse_output_lines("\n".join(part for part in [output_text, error_text] if part), manifest)
    result = {"terminal": True, "batch": status, "expected": parsed["expected"],
        "received": parsed["received"], "successful_count": len(parsed["successful"]),
        "failed_count": len(parsed["failed"]), "successful": parsed["successful"],
        "failed": parsed["failed"]}
    (output_dir / "parsed_results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


class ReplayVerifier:
    provider = "openai_batch_replay"
    model_version = MODEL
    prompt_version = PROMPT_VERSION

    def __init__(self, rows: list[dict]):
        self.records = {row["candidate_key"]: SemanticDecision(**row["parsed_decision"]) for row in rows}
        self.last_batch_records: list[dict] = []

    def verify_many(self, candidates: list[SemanticCandidate]) -> list[SemanticDecision]:
        return [self.records.get(candidate_key(candidate)) or fail_closed(candidate,
            "missing Batch API result", provider=self.provider, model=self.model_version,
            prompt=self.prompt_version) for candidate in candidates]

    def verify(self, candidate: SemanticCandidate) -> SemanticDecision:
        return self.verify_many([candidate])[0]


def evaluate(parsed_path: Path) -> dict:
    parsed = json.loads(parsed_path.read_text())
    verifier = ReplayVerifier(parsed["successful"])
    benchmark = benchmark_run(verifier)
    prior_rows, gm_rows, unseen_rows, imported = _gate_rows()
    extractor = lambda text, **kwargs: extract_contextual_events_v034(
        text, verifier=verifier, cache=None, **kwargs)
    six = compare_events(ROOT, imported, extractor=extractor)
    six_classes = Counter(row["classification"] for row in six)
    prior_totals, prior_accepted = run_documents(prior_rows, "source_artifact", verifier, None)
    prior = {**dict(prior_totals), **label_summary(prior_accepted,
        ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv",
        classification_field="manual_sanity_classification")}
    gm_totals, gm_accepted = run_documents(gm_rows, "local_artifact", verifier, None)
    gm = {**dict(gm_totals), **label_summary(gm_accepted,
        ROOT / "data/evidence_engine_v0_3_3/new_unseen_inspected_events.csv",
        classification_field="manual_sanity_classification")}
    unseen_totals, unseen_accepted = run_documents(unseen_rows, "local_artifact", verifier, None)
    unseen = {**dict(unseen_totals), **label_summary(unseen_accepted,
        ROOT / "data/evidence_engine_v0_3_4/new_unseen_semantic_inspection.csv",
        classification_field="diagnostic_classification")}
    all_provider_rows = parsed["successful"] + parsed["failed"]
    input_tokens = sum(row.get("input_tokens", 0) for row in all_provider_rows)
    output_tokens = sum(row.get("output_tokens", 0) for row in all_provider_rows)
    reasoning_tokens = sum(row.get("reasoning_tokens", 0) for row in all_provider_rows)
    cost = (input_tokens * INPUT_PRICE_PER_M + output_tokens * OUTPUT_PRICE_PER_M) / 2_000_000
    sufficiently_complete = parsed["failed_count"] == 0
    gate_passed = bool(sufficiently_complete and unseen["precision"] is not None
        and unseen["precision"] >= .85 and unseen["severe_false_positives"] == 0
        and unseen["attribution_errors"] == 0 and unseen["supported_retention"] >= .85
        and unseen["provenance_completeness"] == 1 and six_classes["PIOTW_MISSED_EVENT"] == 0
        and six_classes["PIOTW_FALSE_POSITIVE"] == 0 and benchmark["supported_retention"] >= .85)
    technical_status = ("TECHNICALLY READY FOR BLINDED CROSS-REVIEW" if gate_passed else
        "MODEL_PROVIDER_EXECUTION_FAILURE_BATCH" if not sufficiently_complete else "NOT TECHNICALLY READY")
    results = {"version": "0.3.4", "execution": EXECUTION_VERSION,
        "provider": "openai", "model": MODEL, "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION, "benchmark": benchmark,
        "six_document_ai_diagnostic": {"classifications": count_classes(six),
            "missed_ai_events": six_classes["PIOTW_MISSED_EVENT"],
            "likely_false_positives": six_classes["PIOTW_FALSE_POSITIVE"],
            "duplicates": six_classes["DUPLICATE_EVENT"]},
        "previous_unseen": prior, "gm_honeywell_hp": gm, "brand_new_unseen": unseen,
        "provider_results": {"total": parsed["expected"],
            "successful": parsed["successful_count"], "failed": parsed["failed_count"],
            "provider_request_failures": 0,
            "incomplete_max_output_tokens": sum(
                (row.get("incomplete_details") or {}).get("reason") == "max_output_tokens"
                for row in parsed["failed"]),
            "schema_or_semantic_validation_failures": sum(
                (row.get("error") or {}).get("type") == "ValueError" for row in parsed["failed"])},
        "live_costs": {"input_tokens": input_tokens, "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "total_tokens": input_tokens + output_tokens, "total_cost_usd": cost,
            "cost_per_candidate_usd": cost / max(parsed["successful_count"], 1)},
        "gate": {"passed": gate_passed, "technical_status": technical_status},
        "extractor_frozen": False, "cross_review_pack_created": False,
        "official_model2_readiness": "NOT READY", "outcomes_accessed": False,
        "model2_trained": False, "protected_artifacts": len(verify_frozen_isolation(ROOT))}
    output = ROOT / "data/derived/evidence_engine_v0_3_4_batch_results.json"
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    return results


def wait_for_terminal(state_path: Path, *, timeout_seconds: int = 900,
                      poll_seconds: int = 10) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while True:
        status = refresh_status(state_path)
        if status["status"] in TERMINAL_STATUSES or time.monotonic() >= deadline:
            return status
        time.sleep(poll_seconds)
