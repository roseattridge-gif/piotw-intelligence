from __future__ import annotations

import argparse
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
from evidence_engine_v0_3_6.families import verify_candidate

DATA = ROOT / "data/evidence_engine_v0_3_6"
RUN = ROOT / "data/derived/evidence_engine_v0_3_6_fresh_gate"
LEDGER = RUN / "execution_ledger.json"
STATE = RUN / "provider_state.json"
RESULT = ROOT / "data/derived/evidence_engine_v0_3_6_fresh_validation_results.json"
PROMPT = ROOT / "config/evidence/semantic_event_prompt_v0_3_5_development.txt"
POINTER_PROMPT = ROOT / "config/evidence/semantic_evidence_pointer_transport_v0_3_4_1.txt"
CONTRACTS = ROOT / "config/evidence/event_family_contracts_v0_3_6.json"
PROTOCOL = ROOT / "config/evidence/fresh_validation_protocol_v0_3_6.json"
TAXONOMY = ROOT / "config/evidence/event_taxonomy_v0_1.yaml"
MODEL = "gpt-5-mini"
MAX_OUTPUT_TOKENS = 2000
INPUT_PRICE_PER_M = 0.25
OUTPUT_PRICE_PER_M = 2.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_key() -> None:
    if os.environ.get("OPENAI_API_KEY"):
        return
    env = Path.home() / ".codex/.env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
                break
    if not os.environ.get("OPENAI_API_KEY") or os.environ["OPENAI_API_KEY"] == "PASTE_KEY_HERE":
        raise RuntimeError("OPENAI_API_KEY is not available")


def frozen_inputs() -> tuple[list[dict], list[dict]]:
    freeze = json.loads((DATA / "fresh_label_candidate_freeze.json").read_text())
    candidates_path = DATA / "fresh_frozen_candidates.jsonl"
    labels_path = DATA / "fresh_ai_source_first_labels.csv"
    if sha(candidates_path) != freeze["candidate_sha256"] or sha(labels_path) != freeze["label_sha256"]:
        raise RuntimeError("fresh candidate/label freeze mismatch")
    if freeze["candidate_count"] != 210 or freeze["semantic_v036_executed"]:
        raise RuntimeError("fresh candidate freeze is not eligible")
    if any(counts != {"ambiguous": 6, "supported": 12, "unsupported": 12}
           for counts in freeze["family_counts"].values()):
        raise RuntimeError("fresh family balance differs from preregistration")
    source_freeze = json.loads((DATA / "fresh_source_pool_freeze.json").read_text())
    contamination = source_freeze["contamination"]
    if contamination["status"] != "PASS" or contamination["candidate_rows"] != 14:
        raise RuntimeError(f"frozen fresh contamination check failed: {contamination}")
    if sha(DATA / "fresh_candidate_manifest.csv") != source_freeze["manifest_sha256"]:
        raise RuntimeError("fresh corpus manifest changed after contamination freeze")
    candidates = [json.loads(line) for line in candidates_path.read_text().splitlines() if line.strip()]
    labels = list(csv.DictReader(labels_path.open()))
    if {row["candidate_id"] for row in candidates} != {row["candidate_id"] for row in labels}:
        raise RuntimeError("fresh label membership mismatch")
    return candidates, labels


def prepare() -> dict:
    candidates, _ = frozen_inputs()
    RUN.mkdir(parents=True, exist_ok=True)
    lines = []
    requests = []
    for index, row in enumerate(candidates):
        candidate_data = {key: row[key] for key in (
            "target_company", "candidate_event_type", "exact_candidate_span", "context",
            "heading", "publication_date", "deterministic_metadata")}
        candidate = SemanticCandidate(**candidate_data)
        evidence_id = "evidence-" + hashlib.sha256(candidate.context.encode()).hexdigest()[:20]
        mapping = build_evidence_pointer_mapping(candidate, evidence_id)
        pointer = evidence_pointer_id(mapping)
        payload = {**asdict(candidate), "evidence_span_options": provider_pointer_options(mapping)}
        body = {
            "model": MODEL, "max_output_tokens": MAX_OUTPUT_TOKENS,
            "input": [
                {"role": "system", "content": PROMPT.read_text()},
                {"role": "system", "content": POINTER_PROMPT.read_text()},
                {"role": "user", "content": json.dumps(payload, sort_keys=True)},
            ],
            "text": {"format": {"type": "json_schema", "name": "semantic_event_contract_decision",
                                 "strict": True, "schema": semantic_contract_json_schema(candidate, pointer)}},
        }
        custom_id = f"v036-{index:04d}-{row['candidate_id']}"
        line = {"custom_id": custom_id, "method": "POST", "url": "/v1/responses", "body": body}
        lines.append(line)
        requests.append({
            "custom_id": custom_id, "candidate_id": row["candidate_id"],
            "candidate_key": hashlib.sha256(json.dumps(candidate_data, sort_keys=True).encode()).hexdigest(),
            "request_hash": hashlib.sha256(json.dumps(line, sort_keys=True).encode()).hexdigest(),
            "context_hash": hashlib.sha256(candidate.context.encode()).hexdigest(),
            "source_evidence_id": evidence_id, "source_span": candidate.exact_candidate_span,
            "evidence_pointer_mapping": mapping, "candidate": candidate_data,
        })
    input_path = RUN / "input.jsonl"
    input_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in lines))
    manifest = {
        "execution_version": "evidence-engine-v0.3.6-fresh-gate-v1",
        "model": MODEL, "max_output_tokens": MAX_OUTPUT_TOKENS,
        "prompt_version": "semantic-event-v0.3.5-frozen-local-v0.3.6-family-contract",
        "prompt_sha256": sha(PROMPT), "pointer_transport_sha256": sha(POINTER_PROMPT),
        "family_contract_sha256": sha(CONTRACTS), "protocol_sha256": sha(PROTOCOL),
        "taxonomy_sha256": sha(TAXONOMY), "candidate_sha256": sha(DATA / "fresh_frozen_candidates.jsonl"),
        "label_freeze_sha256": sha(DATA / "fresh_label_candidate_freeze.json"),
        "candidate_count": len(requests), "input_jsonl_sha256": sha(input_path),
        "outcomes_accessed": False, "model2_trained": False, "requests": requests,
    }
    manifest_path = RUN / "request_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return {**manifest, "manifest_sha256": sha(manifest_path)}


def evaluate(parsed: dict, labels: list[dict], protected_before: dict) -> dict:
    label_by_id = {row["candidate_id"]: row for row in labels}
    candidates = {row["candidate_id"]: row for row in json.loads(
        "[" + ",".join((DATA / "fresh_frozen_candidates.jsonl").read_text().splitlines()) + "]")}
    final_rows = []
    for row in parsed["successful"]:
        candidate = SemanticCandidate(**{key: candidates[row["candidate_id"]][key] for key in (
            "target_company", "candidate_event_type", "exact_candidate_span", "context",
            "heading", "publication_date", "deterministic_metadata")})
        local = verify_candidate(candidate)
        provider = row["parsed_decision"]["decision"]
        final = "accept" if local.disposition == "accept" and provider == "accept" else (
            "reject" if local.disposition == "reject" or provider == "reject" else "ambiguous"
        )
        final_rows.append({**row, "family": local.family, "local_disposition": local.disposition,
                           "local_reason": local.reason, "provider_disposition": provider,
                           "final_disposition": final})
    accepted = [row for row in final_rows if row["final_disposition"] == "accept"]
    accepted_supported = [row for row in accepted if label_by_id[row["candidate_id"]]["independent_disposition"] == "supported"]
    false_positives = [row for row in accepted if label_by_id[row["candidate_id"]]["independent_disposition"] != "supported"]
    supported_total = sum(row["independent_disposition"] == "supported" for row in labels)
    severe = [row for row in false_positives if label_by_id[row["candidate_id"]]["severe_if_accepted"] == "true"]
    attribution = [row for row in false_positives if label_by_id[row["candidate_id"]]["third_party_attribution"] == "true"]
    precision = len(accepted_supported) / max(len(accepted), 1)
    retention = len(accepted_supported) / supported_total
    provenance = sum(bool(row["parsed_decision"].get("exact_support_span")) for row in accepted) / max(len(accepted), 1)
    provider_valid = parsed["successful_count"] / parsed["expected"]
    by_family = {}
    for family in sorted({row["event_family"] for row in labels}):
        family_labels = [row for row in labels if row["event_family"] == family]
        family_results = [row for row in final_rows if row["family"] == family]
        family_accepted = [row for row in family_results if row["final_disposition"] == "accept"]
        family_supported = [row for row in family_accepted if label_by_id[row["candidate_id"]]["independent_disposition"] == "supported"]
        supported_count = sum(row["independent_disposition"] == "supported" for row in family_labels)
        by_family[family] = {
            "labelled": len(family_labels), "accepted": len(family_accepted),
            "accepted_supported": len(family_supported),
            "false_positives": len(family_accepted) - len(family_supported),
            "precision": len(family_supported) / max(len(family_accepted), 1),
            "supported_retained": len(family_supported), "supported_total": supported_count,
            "retention": len(family_supported) / supported_count,
            "ambiguous_decisions": sum(row["final_disposition"] == "ambiguous" for row in family_results),
        }
    input_tokens = sum(row.get("input_tokens", 0) for row in parsed["successful"] + parsed["failed"])
    output_tokens = sum(row.get("output_tokens", 0) for row in parsed["successful"] + parsed["failed"])
    thresholds = json.loads(PROTOCOL.read_text())["frozen_thresholds"]
    passed = bool(
        provider_valid >= thresholds["provider_schema_contract_completeness_minimum"]
        and precision >= thresholds["accepted_event_precision_minimum"]
        and retention >= thresholds["supported_event_retention_minimum"]
        and len(severe) <= thresholds["severe_false_positives_maximum"]
        and len(attribution) <= thresholds["attribution_errors_maximum"]
        and provenance >= thresholds["provenance_completeness_minimum"]
    )
    status = "EVIDENCE_ENGINE_0_3_6_FRESH_VALIDATION_PASSED" if passed else "EVIDENCE_ENGINE_0_3_6_FRESH_VALIDATION_FAILED"
    return {
        "version": "0.3.6", "status": status, "gate_passed": passed,
        "companies": 7, "documents": 14, "total_labelled_candidates": len(labels),
        "label_method": {"reviewer_type": "AI_ASSISTED_FINOPS_REVIEW",
                         "formal_independent_human_gold": False, "admissible_for_model2_gate": False},
        "provider": {"expected": parsed["expected"], "received": parsed["received"],
                     "completed": parsed["successful_count"], "failed": parsed["failed_count"],
                     "completion_rate": provider_valid, "schema_and_local_contract_valid": parsed["successful_count"],
                     "model": MODEL, "input_tokens": input_tokens, "output_tokens": output_tokens,
                     "total_tokens": input_tokens + output_tokens,
                     "estimated_batch_cost_usd": (input_tokens * INPUT_PRICE_PER_M + output_tokens * OUTPUT_PRICE_PER_M) / 2_000_000},
        "metrics": {"accepted": len(accepted), "accepted_supported": len(accepted_supported),
                    "false_positives": len(false_positives), "precision": precision,
                    "supported_retained": len(accepted_supported), "supported_total": supported_total,
                    "retention": retention, "severe_false_positives": len(severe),
                    "attribution_errors": len(attribution), "provenance_completeness": provenance,
                    "ambiguous_decisions": sum(row["final_disposition"] == "ambiguous" for row in final_rows)},
        "per_family": by_family, "false_positive_candidate_ids": [row["candidate_id"] for row in false_positives],
        "severe_candidate_ids": [row["candidate_id"] for row in severe],
        "attribution_candidate_ids": [row["candidate_id"] for row in attribution],
        "final_rows": final_rows, "thresholds": thresholds,
        "protected_artifacts_unchanged": protected_before == verify_frozen_isolation(ROOT),
        "outcomes_accessed": False, "model2_trained": False, "official_model2_readiness": "NOT READY",
    }


def run() -> dict:
    if LEDGER.exists():
        raise RuntimeError("fresh 0.3.6 gate already started; rerun prohibited")
    _candidates, labels = frozen_inputs()
    protected_before = verify_frozen_isolation(ROOT)
    manifest = prepare()
    load_key()
    LEDGER.write_text(json.dumps({"status": "started", "run_count": 1,
                                  "started_at": datetime.now(UTC).isoformat(),
                                  "request_manifest_sha256": manifest["manifest_sha256"]},
                                 indent=2, sort_keys=True) + "\n")
    state = submit(RUN, STATE, metadata={"experiment": "piotw-v036-fresh-gate", "run": "one"})
    terminal = wait_for_terminal(STATE, timeout_seconds=1800, poll_seconds=10)
    if terminal["status"] not in {"completed", "failed", "expired", "cancelled"}:
        raise RuntimeError("fresh 0.3.6 batch did not reach terminal state")
    parsed = collect(STATE, RUN, RUN)
    result = evaluate(parsed, labels, protected_before)
    result["provider_batch_id"] = state["batch_id"]
    result["request_manifest_sha256"] = manifest["manifest_sha256"]
    result["source_pool_freeze_sha256"] = sha(DATA / "fresh_source_pool_freeze.json")
    result["label_candidate_freeze_sha256"] = sha(DATA / "fresh_label_candidate_freeze.json")
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    LEDGER.write_text(json.dumps({"status": "completed", "run_count": 1,
                                  "provider_batch_id": state["batch_id"],
                                  "result_sha256": sha(RESULT), "technical_status": result["status"]},
                                 indent=2, sort_keys=True) + "\n")
    if result["gate_passed"]:
        freeze_files = [
            ROOT / "evidence_engine_v0_3_6/families.py", CONTRACTS, PROTOCOL, PROMPT,
            POINTER_PROMPT, TAXONOMY, DATA / "fresh_frozen_candidates.jsonl",
            DATA / "fresh_ai_source_first_labels.csv", DATA / "fresh_source_pool_freeze.json",
            DATA / "fresh_label_candidate_freeze.json", RUN / "request_manifest.json", RESULT,
        ]
        stack_freeze = {"freeze_version": "evidence-engine-v0.3.6-fresh-pass-v1",
                        "status": result["status"], "model": MODEL,
                        "provider_batch_id": state["batch_id"],
                        "files": {str(path.relative_to(ROOT)): sha(path) for path in freeze_files},
                        "outcomes_accessed": False, "model2_trained": False}
        (DATA / "fresh_pass_stack_freeze.json").write_text(json.dumps(stack_freeze, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "run"])
    args = parser.parse_args()
    if args.command == "prepare":
        manifest = prepare()
        print(json.dumps({key: value for key, value in manifest.items() if key != "requests"}, indent=2, sort_keys=True))
    else:
        result = run()
        print(json.dumps({key: value for key, value in result.items() if key != "final_rows"}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
