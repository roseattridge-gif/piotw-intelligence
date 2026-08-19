from __future__ import annotations

import json
import math
import re
import statistics
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.batch_api import response_output_text

RUN = ROOT / "data/derived/evidence_engine_v0_3_4_batch/scientific_2000"


def visible(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("\\u2022", "•")
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    text = "".join(char for char in text if not unicodedata.category(char).startswith("C"))
    return re.sub(r"\s+", " ", text).strip()


def percentile(values: list[int], quantile: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position); upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def usage(rows: list[dict]) -> dict:
    result = {}
    for field in ("input_tokens", "output_tokens", "reasoning_tokens"):
        values = [int(row.get(field) or 0) for row in rows]
        result[field] = {"count": len(values), "total": sum(values),
            "median": statistics.median(values) if values else 0,
            "p90": percentile(values, .90), "p95": percentile(values, .95),
            "max": max(values, default=0)}
    return result


def classify(row: dict, raw: dict | None, candidate: dict) -> tuple[str, str]:
    details = row.get("incomplete_details") or {}
    error = row.get("error") or {}
    message = error.get("message", "")
    if details.get("reason") == "max_output_tokens":
        return "OUTPUT_TRUNCATED_MAX_OUTPUT_TOKENS", "MODEL_OUTPUT_FAILURE"
    if error.get("type") == "JSONDecodeError":
        return "MALFORMED_OR_TRUNCATED_JSON", "MODEL_OUTPUT_FAILURE"
    if "accepted decision requires an exact supplied evidence span" in message:
        output = json.loads(response_output_text(raw["response"]["body"]))
        support = visible(output.get("exact_support_span")); context = visible(candidate["context"])
        if support and support in context:
            return "LOCAL_UNICODE_EXACT_SPAN_MATCH_BUG", "LOCAL_VALIDATOR_BUG"
        return "ACCEPT_EVIDENCE_SPAN_NOT_IN_CONTEXT", "MODEL_OUTPUT_FAILURE"
    mapping = {
        "accept decision requires an accept reason": "ACCEPT_REASON_CODE_INCONSISTENT",
        "non-accepted decision cannot assert direct support": "NON_ACCEPT_ASSERTS_DIRECT_SUPPORT",
        "ambiguous decision requires an ambiguous reason": "AMBIGUOUS_REASON_CODE_INCONSISTENT",
        "unsupported event remap": "UNSUPPORTED_EVENT_REMAP",
    }
    for fragment, category in mapping.items():
        if fragment in message:
            return category, "MODEL_OUTPUT_FAILURE"
    return "OTHER_CONTRACT_FAILURE", "UNRESOLVED"


def main() -> None:
    manifest = json.loads((RUN / "request_manifest.json").read_text())
    requests = {row["custom_id"]: row for row in manifest["requests"]}
    raw_rows = {}
    for line in (RUN / "raw_output.jsonl").read_text().splitlines():
        row = json.loads(line); raw_rows[row["custom_id"]] = row
    parsed = json.loads((RUN / "parsed_results.json").read_text())
    details = []
    for row in parsed["failed"]:
        request = requests[row["custom_id"]]
        category, origin = classify(row, raw_rows.get(row["custom_id"]), request["candidate"])
        details.append({"custom_id": row["custom_id"], "candidate_id": row["candidate_id"],
            "failure_type": category, "failure_origin": origin,
            "response_status": row.get("response_status"),
            "incomplete_reason": (row.get("incomplete_details") or {}).get("reason"),
            "input_tokens": row.get("input_tokens", 0), "output_tokens": row.get("output_tokens", 0),
            "reasoning_tokens": row.get("reasoning_tokens", 0), "error": row.get("error"),
            "raw_response_hash": row.get("raw_response_hash")})
    counts = Counter(row["failure_type"] for row in details)
    origins = Counter(row["failure_origin"] for row in details)
    valid = parsed["successful"]
    contract_invalid = [row for row in parsed["failed"]
        if (row.get("incomplete_details") or {}).get("reason") != "max_output_tokens"]
    truncated = [row for row in parsed["failed"]
        if (row.get("incomplete_details") or {}).get("reason") == "max_output_tokens"]
    result = {"version": "0.3.4-contract-diagnosis-1", "source_batch_id":
        "batch_6a83017941f481909f300700dd40f935", "invalid_total": len(details),
        "failure_counts": {key: {"count": value, "total": len(details),
            "rate": value / len(details)} for key, value in sorted(counts.items())},
        "origin_counts": {key: {"count": value, "total": len(details),
            "rate": value / len(details)} for key, value in sorted(origins.items())},
        "token_usage": {"valid": usage(valid), "contract_invalid": usage(contract_invalid),
            "truncated": usage(truncated)}, "failures": details,
        "formal_gold": False, "admissible_for_model2_gate": False,
        "outcomes_accessed": False, "model2_trained": False}
    out = ROOT / "data/derived/evidence_engine_v0_3_4_contract_failures.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    regression = ROOT / "data/evidence_engine_v0_3_4/semantic_contract_regression_cases.jsonl"
    with regression.open("w") as handle:
        for detail in details:
            request = requests[detail["custom_id"]]
            raw = raw_rows.get(detail["custom_id"])
            record = {"case_id": detail["custom_id"], "candidate": request["candidate"],
                "original_raw_response": raw, "failure_type": detail["failure_type"],
                "failure_origin": detail["failure_origin"],
                "expected_structural_behaviour": "return a provider-schema-valid and locally contract-valid decision",
                "development_only": True, "formal_gold": False}
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({"invalid": len(details), "counts": counts, "origins": origins}, default=dict))


if __name__ == "__main__":
    main()
