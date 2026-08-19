from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.batch_api import (
    RUN_DIR,
    SCIENTIFIC_RERUN_DIR,
    SCIENTIFIC_RERUN_ID,
    collect,
    contract_smoke_candidates,
    evaluate,
    prepare_requests,
    prepare_scientific,
    refresh_status,
    submit,
    synthetic_candidates,
    wait_for_terminal,
)


def require_key() -> None:
    key = os.environ.get("OPENAI_API_KEY")
    if not key or key == "PASTE_KEY_HERE":
        raise SystemExit("MODEL_BATCH_PROVIDER_PREFLIGHT_FAILED: credential_absent")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def preflight() -> int:
    require_key()
    directory = RUN_DIR / "preflight_2000"
    prepared = prepare_requests(synthetic_candidates(), directory, prefix="synthetic")
    state_path = directory / "submission.json"
    submit(directory, state_path, metadata={"purpose": "piotw-semantic-batch-preflight",
        "scientific_data": "false"})
    status = wait_for_terminal(state_path)
    if status["status"] not in {"completed", "failed", "expired", "cancelled"}:
        result = {"status": "MODEL_BATCH_PROVIDER_PREFLIGHT_FAILED",
            "failure": "batch_did_not_reach_terminal_state", "batch": status,
            "scientific_data_used": False}
        write_json(directory / "preflight_result.json", result)
        print(result["status"])
        return 1
    collected = collect(state_path, directory, directory)
    decisions = {row["custom_id"]: row["parsed_decision"]["decision"]
        for row in collected.get("successful", [])}
    expected = {"synthetic-0000-": "accept", "synthetic-0001-": "reject"}
    passed = collected.get("failed_count") == 0 and all(
        next((decision for custom_id, decision in decisions.items() if custom_id.startswith(prefix)), None)
        == wanted for prefix, wanted in expected.items())
    result = {"status": "MODEL_BATCH_PROVIDER_PREFLIGHT_PASSED" if passed
        else "MODEL_BATCH_PROVIDER_PREFLIGHT_FAILED", "scientific_data_used": False,
        "input_jsonl_sha256": prepared["input_jsonl_sha256"], "batch": status,
        "successful": collected.get("successful_count", 0),
        "failed": collected.get("failed_count", 0), "decisions": decisions}
    write_json(directory / "preflight_result.json", result)
    print(result["status"])
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "preflight", "submit", "status", "collect",
        "contract-smoke"])
    args = parser.parse_args()
    scientific = SCIENTIFIC_RERUN_DIR
    state_path = scientific / "submission.json"
    if args.command == "prepare":
        result = prepare_scientific()
        print(json.dumps({"status": "SEMANTIC_BATCH_PREPARED",
            "candidate_count": result["candidate_count"],
            "input_jsonl_sha256": result["input_jsonl_sha256"],
            "manifest_sha256": result["manifest_sha256"]}))
        return 0
    if args.command == "preflight":
        return preflight()
    if args.command == "contract-smoke":
        require_key()
        directory = RUN_DIR / "contract_smoke_v2_pointer"
        prepared = prepare_requests(contract_smoke_candidates(), directory, prefix="contract-smoke")
        smoke_state = directory / "submission.json"
        submit(directory, smoke_state, metadata={"purpose": "piotw-contract-reliability-smoke",
            "scientific_data": "false"})
        status = wait_for_terminal(smoke_state)
        if status["status"] not in {"completed", "failed", "expired", "cancelled"}:
            result = {"status": "SEMANTIC_CONTRACT_RELIABILITY_FAILED",
                "reason": "batch_did_not_reach_terminal_state", "batch": status}
        else:
            parsed = collect(smoke_state, directory, directory)
            total = prepared["candidate_count"]
            provider_completed = status["request_counts"]["completed"]
            valid = parsed.get("successful_count", 0)
            schema_valid = valid + sum(
                row.get("response_status_code") == 200
                and row.get("response_status") == "completed"
                and (row.get("error") or {}).get("type") != "JSONDecodeError"
                for row in parsed.get("failed", []))
            truncated = sum((row.get("incomplete_details") or {}).get("reason") == "max_output_tokens"
                for row in parsed.get("failed", []))
            unknown_pointers = sum("unknown evidence pointer" in
                (row.get("error") or {}).get("message", "") for row in parsed.get("failed", []))
            accepted = [row for row in parsed.get("successful", [])
                if row["parsed_decision"]["decision"] == "accept"]
            resolved = sum(bool(row["parsed_decision"].get("exact_support_span")) for row in accepted)
            passed = (provider_completed == total and schema_valid / total >= .99
                and valid / total >= .98 and truncated == 0 and unknown_pointers == 0
                and bool(accepted) and resolved == len(accepted))
            input_tokens = sum(row.get("input_tokens", 0)
                for row in parsed.get("successful", []) + parsed.get("failed", []))
            output_tokens = sum(row.get("output_tokens", 0)
                for row in parsed.get("successful", []) + parsed.get("failed", []))
            result = {"status": ("SEMANTIC_CONTRACT_RELIABILITY_PASSED" if passed
                else "SEMANTIC_CONTRACT_RELIABILITY_FAILED"), "development_only": True,
                "scientific_gate_candidates_used": False, "total": total,
                "provider_completed": provider_completed,
                "provider_completion_rate": provider_completed / total,
                "schema_valid": schema_valid, "schema_valid_rate": schema_valid / total,
                "local_contract_valid": valid, "local_contract_valid_rate": valid / total,
                "unknown_pointer_count": unknown_pointers,
                "accepted_with_evidence": resolved, "accepted_total": len(accepted),
                "evidence_resolution_rate": resolved / max(len(accepted), 1),
                "truncated": truncated, "truncation_rate": truncated / total,
                "input_tokens": input_tokens, "output_tokens": output_tokens,
                "estimated_batch_cost_usd":
                    (input_tokens * .25 + output_tokens * 2) / 2_000_000,
                "batch": status, "outcomes_accessed": False, "model2_trained": False}
        write_json(directory / "contract_reliability_result.json", result)
        print(json.dumps(result))
        return 0 if result["status"] == "SEMANTIC_CONTRACT_RELIABILITY_PASSED" else 1
    require_key()
    if args.command == "submit":
        preflight_path = RUN_DIR / "preflight_2000" / "preflight_result.json"
        if not preflight_path.exists() or json.loads(preflight_path.read_text()).get("status") != (
                "MODEL_BATCH_PROVIDER_PREFLIGHT_PASSED"):
            raise SystemExit("MODEL_BATCH_PROVIDER_PREFLIGHT_REQUIRED")
        if not (scientific / "request_manifest.json").exists():
            prepare_scientific()
        state = submit(scientific, state_path, metadata={"purpose": "piotw-semantic-gate-v0-3-4",
            "scientific_configuration": "frozen",
            "execution_type": SCIENTIFIC_RERUN_ID})
        print(json.dumps({"status": state["status"], "batch_id": state["batch_id"],
            "request_counts": state["request_counts"]}))
        return 0
    if not state_path.exists():
        raise SystemExit("SEMANTIC_BATCH_NOT_SUBMITTED")
    if args.command == "status":
        status = refresh_status(state_path)
        print(json.dumps({"status": status["status"], "batch_id": status["batch_id"],
            "request_counts": status["request_counts"]}))
        return 0
    collected = collect(state_path, scientific, scientific)
    if not collected.get("terminal"):
        print(json.dumps({"status": collected["status"], "terminal": False,
            "request_counts": collected["request_counts"]}))
        return 0
    results = evaluate(scientific / "parsed_results.json")
    print(json.dumps({"status": results["gate"]["technical_status"],
        "gate_passed": results["gate"]["passed"],
        "successful": results["provider_results"]["successful"],
        "failed": results["provider_results"]["failed"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
