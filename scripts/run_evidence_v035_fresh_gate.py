from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_3_4.batch_api import collect, submit, wait_for_terminal
from evidence_engine_v0_3_4.evidence_pointer import (
    build_evidence_pointer_mapping,
    evidence_pointer_id,
    provider_pointer_options,
)
from evidence_engine_v0_3_4.semantic import SemanticCandidate, semantic_contract_json_schema

DATA = ROOT / "data/evidence_engine_v0_3_5"
RUN_DIR = ROOT / "data/derived/evidence_engine_v0_3_5_fresh_gate"
LEDGER = RUN_DIR / "execution_ledger.json"
PROMPT = ROOT / "config/evidence/semantic_event_prompt_v0_3_5_development.txt"
POINTER_PROMPT = ROOT / "config/evidence/semantic_evidence_pointer_transport_v0_3_4_1.txt"
MODEL = "gpt-5-mini"
MAX_OUTPUT_TOKENS = 2000
INPUT_PRICE_PER_M = 0.25
OUTPUT_PRICE_PER_M = 2.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_key() -> None:
    if os.environ.get("OPENAI_API_KEY"):
        return
    env_path = Path.home() / ".codex/.env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
                break
    if not os.environ.get("OPENAI_API_KEY") or os.environ["OPENAI_API_KEY"] == "PASTE_KEY_HERE":
        raise RuntimeError("OPENAI_API_KEY is not available")


def assert_frozen_inputs() -> tuple[list[dict], list[dict]]:
    source = json.loads((DATA / "fresh_source_candidate_freeze.json").read_text())
    gold = json.loads((DATA / "fresh_gold_freeze.json").read_text())
    if sha(DATA / "fresh_candidates.jsonl") != source["candidate_manifest_sha256"]:
        raise RuntimeError("fresh candidate freeze mismatch")
    if sha(DATA / "fresh_corpus_manifest.csv") != source["manifest_sha256"]:
        raise RuntimeError("fresh corpus freeze mismatch")
    if sha(DATA / "fresh_ai_source_first_labels.csv") != gold["label_sha256"]:
        raise RuntimeError("fresh label freeze mismatch")
    if sha(DATA / "fresh_annotation_schema.json") != gold["schema_sha256"]:
        raise RuntimeError("fresh schema freeze mismatch")
    candidates = [json.loads(row) for row in (DATA / "fresh_candidates.jsonl").read_text().splitlines()]
    labels = list(csv.DictReader((DATA / "fresh_ai_source_first_labels.csv").open()))
    if len(candidates) != len(labels) or {r["candidate_id"] for r in candidates} != {r["candidate_id"] for r in labels}:
        raise RuntimeError("candidate/label membership mismatch")
    return candidates, labels


def ensure_one_run() -> None:
    if LEDGER.exists():
        raise RuntimeError("fresh 0.3.5 gate already started; the frozen protocol prohibits rerun")


def prepare(candidates: list[dict]) -> dict:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    requests = []; lines = []
    for index, row in enumerate(candidates):
        candidate_data = {key: row[key] for key in (
            "target_company", "candidate_event_type", "exact_candidate_span", "context", "heading",
            "publication_date", "deterministic_metadata")}
        candidate = SemanticCandidate(**candidate_data)
        evidence_id = "evidence-" + hashlib.sha256(candidate.context.encode()).hexdigest()[:20]
        mapping = build_evidence_pointer_mapping(candidate, evidence_id)
        pointer = evidence_pointer_id(mapping)
        custom_id = f"v035-{index:04d}-{row['candidate_id']}"
        payload = {**asdict(candidate), "evidence_span_options": provider_pointer_options(mapping)}
        body = {"model": MODEL, "max_output_tokens": MAX_OUTPUT_TOKENS,
            "input": [{"role": "system", "content": PROMPT.read_text()},
                      {"role": "system", "content": POINTER_PROMPT.read_text()},
                      {"role": "user", "content": json.dumps(payload, sort_keys=True)}],
            "text": {"format": {"type": "json_schema", "name": "semantic_event_contract_decision",
                "strict": True, "schema": semantic_contract_json_schema(candidate, pointer)}}}
        line = {"custom_id": custom_id, "method": "POST", "url": "/v1/responses", "body": body}
        lines.append(line)
        requests.append({"custom_id": custom_id, "candidate_id": row["candidate_id"],
            "candidate_key": hashlib.sha256(json.dumps(candidate_data, sort_keys=True).encode()).hexdigest(),
            "request_hash": hashlib.sha256(json.dumps(line, sort_keys=True).encode()).hexdigest(),
            "context_hash": hashlib.sha256(candidate.context.encode()).hexdigest(),
            "source_evidence_id": evidence_id, "source_span": candidate.exact_candidate_span,
            "evidence_pointer_mapping": mapping, "candidate": candidate_data})
    input_path = RUN_DIR / "input.jsonl"
    input_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in lines))
    manifest = {"execution_version": "fresh-gate-v0.3.5-v1", "model": MODEL,
        "max_output_tokens": MAX_OUTPUT_TOKENS, "prompt_version": "semantic-event-v0.3.5-development",
        "prompt_sha256": sha(PROMPT), "pointer_transport_sha256": sha(POINTER_PROMPT),
        "candidate_count": len(requests), "input_jsonl_sha256": sha(input_path), "requests": requests}
    (RUN_DIR / "request_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def evaluate(parsed: dict, labels: list[dict], protected_before: dict) -> dict:
    label_by_id = {row["candidate_id"]: row for row in labels}
    accepted = [row for row in parsed["successful"] if row["parsed_decision"]["decision"] == "accept"]
    accepted_supported = [row for row in accepted if label_by_id[row["candidate_id"]]["independent_disposition"] == "supported"]
    accepted_unsupported = [row for row in accepted if label_by_id[row["candidate_id"]]["independent_disposition"] == "unsupported"]
    supported_total = sum(row["independent_disposition"] == "supported" for row in labels)
    severe = [row for row in accepted_unsupported if label_by_id[row["candidate_id"]]["severe_if_accepted"] == "true"]
    attribution = [row for row in accepted_unsupported if label_by_id[row["candidate_id"]]["third_party_attribution"] == "true"]
    precision = len(accepted_supported) / max(len(accepted_supported) + len(accepted_unsupported), 1)
    retention = len(accepted_supported) / max(supported_total, 1)
    provenance = sum(bool(row["parsed_decision"].get("exact_support_span")) for row in accepted) / max(len(accepted), 1)
    input_tokens = sum(row.get("input_tokens", 0) for row in parsed["successful"] + parsed["failed"])
    output_tokens = sum(row.get("output_tokens", 0) for row in parsed["successful"] + parsed["failed"])
    gate_passed = (parsed["failed_count"] == 0 and precision >= .95 and retention >= .90
                   and not severe and not attribution and provenance == 1)
    status = ("EVIDENCE_ENGINE_0_3_5_FRESH_VALIDATION_PASSED" if gate_passed
              else "EVIDENCE_ENGINE_0_3_5_FRESH_VALIDATION_FAILED")
    return {"version": "0.3.5", "status": status, "gate_passed": gate_passed,
        "companies": 5, "documents": 10, "total_candidates": len(labels),
        "labels": {"reviewer_type": "AI_ASSISTED_FINOPS_REVIEW",
            "formal_independent_human_gold": False, "admissible_for_model2_gate": False},
        "metrics": {"accepted": len(accepted), "accepted_supported": len(accepted_supported),
            "false_positives": len(accepted_unsupported), "precision": precision,
            "supported_retained": len(accepted_supported), "supported_total": supported_total,
            "retention": retention, "severe_false_positives": len(severe),
            "attribution_errors": len(attribution), "provenance_completeness": provenance},
        "provider": {"expected": parsed["expected"], "received": parsed["received"],
            "provider_completed": parsed["successful_count"], "schema_and_contract_valid": parsed["successful_count"],
            "failed": parsed["failed_count"], "model": MODEL, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "total_tokens": input_tokens + output_tokens,
            "estimated_batch_cost_usd": (input_tokens * INPUT_PRICE_PER_M + output_tokens * OUTPUT_PRICE_PER_M) / 2_000_000},
        "severe_candidate_ids": [row["candidate_id"] for row in severe],
        "attribution_candidate_ids": [row["candidate_id"] for row in attribution],
        "outcomes_accessed": False, "model2_trained": False,
        "protected_artifacts_unchanged": protected_before == verify_frozen_isolation(ROOT),
        "official_model2_readiness": "NOT READY"}


def main() -> None:
    ensure_one_run()
    candidates, labels = assert_frozen_inputs()
    protected_before = verify_frozen_isolation(ROOT)
    load_key()
    prepare(candidates)
    LEDGER.write_text(json.dumps({"status": "started", "started_at": datetime.now(UTC).isoformat(),
        "run_count": 1, "manifest_sha256": sha(RUN_DIR / "request_manifest.json")}, indent=2) + "\n")
    state_path = RUN_DIR / "provider_state.json"
    state = submit(RUN_DIR, state_path, metadata={"experiment": "piotw-v035-fresh-gate", "run": "one"})
    terminal = wait_for_terminal(state_path, timeout_seconds=1200, poll_seconds=10)
    if terminal["status"] not in {"completed", "failed", "expired", "cancelled"}:
        raise RuntimeError("fresh gate provider batch did not reach a terminal state")
    parsed = collect(state_path, RUN_DIR, RUN_DIR)
    results = evaluate(parsed, labels, protected_before)
    results["request_manifest_sha256"] = sha(RUN_DIR / "request_manifest.json")
    results["source_freeze_sha256"] = sha(DATA / "fresh_source_candidate_freeze.json")
    results["gold_freeze_sha256"] = sha(DATA / "fresh_gold_freeze.json")
    results["provider_batch_id"] = state["batch_id"]
    output = ROOT / "data/derived/evidence_engine_v0_3_5_fresh_validation_results.json"
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    LEDGER.write_text(json.dumps({"status": "completed", "run_count": 1,
        "provider_batch_id": state["batch_id"], "result_sha256": sha(output),
        "technical_status": results["status"]}, indent=2, sort_keys=True) + "\n")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
