from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.batch_api import response_output_text
from evidence_engine_v0_3_6.families import route_family

DATA = ROOT / "data/evidence_engine_v0_3_6"
POOL = DATA / "fresh_candidate_pool.jsonl"
CONTRACTS = ROOT / "config/evidence/event_family_contracts_v0_3_6.json"
RUN = ROOT / "data/derived/evidence_engine_v0_3_6_source_first_review"
MODEL = "gpt-5-mini"


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


def schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["candidate_id", "disposition", "target_entity", "temporal_state", "polarity",
                     "third_party", "historical_or_hypothetical", "severe_if_accepted",
                     "exact_support_span", "rationale"],
        "properties": {
            "candidate_id": {"type": "string"},
            "disposition": {"type": "string", "enum": ["supported", "unsupported", "ambiguous"]},
            "target_entity": {"type": "string", "enum": ["target_company", "target_subsidiary", "third_party", "unclear"]},
            "temporal_state": {"type": "string", "enum": ["current", "ongoing", "planned", "historical", "hypothetical", "unclear"]},
            "polarity": {"type": "string", "enum": ["positive", "negative", "mixed", "neutral", "unclear"]},
            "third_party": {"type": "boolean"},
            "historical_or_hypothetical": {"type": "boolean"},
            "severe_if_accepted": {"type": "boolean"},
            "exact_support_span": {"type": "string"},
            "rationale": {"type": "string"},
        },
    }


def prompt(row: dict, contract: dict) -> str:
    payload = {
        "candidate_id": row["candidate_id"], "company": row["target_company"],
        "event_type": row["candidate_event_type"], "candidate_span": row["exact_candidate_span"],
        "surrounding_context": row["context"][:3500], "publication_date": row["publication_date"],
    }
    return (
        "Perform a blinded source-first finance/operations annotation. You have not seen any PIOTW "
        "decision. SUPPORTED means the source directly establishes the proposed event for the target "
        "issuer within the supplied family contract. UNSUPPORTED includes hypothetical risk, "
        "historical-only background, third-party events without direct issuer effect, headings, "
        "definitions, metric or product names, and wrong polarity/object. AMBIGUOUS means evidence is "
        "genuinely insufficient. For SUPPORTED, exact_support_span must be a verbatim substring of "
        "surrounding_context; otherwise return an empty string. Return the supplied candidate_id exactly.\n"
        f"Contract: {json.dumps(contract, sort_keys=True)}\nCandidate: {json.dumps(payload, ensure_ascii=False)}"
    )


def main() -> None:
    freeze_path = DATA / "fresh_label_candidate_freeze.json"
    if freeze_path.exists():
        raise RuntimeError("source-first labels already frozen")
    load_key()
    RUN.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in POOL.read_text().splitlines() if line.strip()]
    by_id = {row["candidate_id"]: row for row in rows}
    contracts = json.loads(CONTRACTS.read_text())["families"]
    input_path = RUN / "input.jsonl"
    lines = []
    for row in rows:
        family = route_family(row["candidate_event_type"])
        custom_id = f"source-first-{row['candidate_id']}"
        body = {
            "model": MODEL,
            "max_output_tokens": 1500,
            "input": prompt(row, contracts[family]),
            "text": {"format": {"type": "json_schema", "name": "source_first_label", "strict": True, "schema": schema()}},
        }
        lines.append({"custom_id": custom_id, "method": "POST", "url": "/v1/responses", "body": body})
    input_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in lines))
    state_path = RUN / "state.json"
    client = OpenAI(max_retries=0)
    if state_path.exists():
        state = json.loads(state_path.read_text())
        batch_id = state["batch_id"]
    else:
        with input_path.open("rb") as handle:
            uploaded = client.files.create(file=handle, purpose="batch")
        batch = client.batches.create(input_file_id=uploaded.id, endpoint="/v1/responses",
                                      completion_window="24h", metadata={"purpose": "piotw-v036-source-first-review"})
        batch_id = batch.id
        state_path.write_text(json.dumps({"batch_id": batch_id, "input_file_id": uploaded.id,
                                          "input_sha256": sha(input_path), "submitted_at": datetime.now(UTC).isoformat()},
                                         indent=2, sort_keys=True) + "\n")
    while True:
        batch = client.batches.retrieve(batch_id)
        if batch.status in {"completed", "failed", "expired", "cancelled"}:
            break
        time.sleep(10)
    if batch.status != "completed" or not batch.output_file_id:
        raise RuntimeError(f"source-first review batch failed: {batch.status}")
    raw = client.files.content(batch.output_file_id).text
    (RUN / "raw_output.jsonl").write_text(raw)
    parsed: dict[str, dict] = {}
    failed_review_ids: list[str] = []
    usage = {"input_tokens": 0, "output_tokens": 0}
    for line in raw.splitlines():
        item = json.loads(line)
        candidate_id = item["custom_id"].removeprefix("source-first-")
        body = item["response"]["body"]
        output_text = response_output_text(body)
        if body.get("status") != "completed" or not output_text:
            failed_review_ids.append(candidate_id)
            continue
        label = json.loads(output_text)
        if label["candidate_id"] != candidate_id or candidate_id in parsed:
            raise RuntimeError(f"source-first membership error: {candidate_id}")
        candidate = by_id[candidate_id]
        if label["disposition"] == "supported" and label["exact_support_span"] not in candidate["context"]:
            failed_review_ids.append(candidate_id)
            continue
        parsed[candidate_id] = label
        usage["input_tokens"] += (body.get("usage") or {}).get("input_tokens", 0)
        usage["output_tokens"] += (body.get("usage") or {}).get("output_tokens", 0)
    if set(parsed) | set(failed_review_ids) != set(by_id):
        raise RuntimeError(f"source-first batch membership incomplete: {len(parsed)}/{len(by_id)}")
    (RUN / "parsed_labels.json").write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n")

    selected = []
    label_rows = []
    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["candidate_id"] not in parsed:
            continue
        grouped[route_family(row["candidate_event_type"])][parsed[row["candidate_id"]]["disposition"]].append(row)
    for family in sorted(grouped):
        for disposition, amount in (("supported", 12), ("unsupported", 12), ("ambiguous", 6)):
            available = sorted(grouped[family][disposition], key=lambda row: row["candidate_id"])
            if len(available) < amount:
                raise RuntimeError(f"insufficient {disposition} labels for {family}: {len(available)}/{amount}")
            for row in available[:amount]:
                label = parsed[row["candidate_id"]]
                selected.append(row)
                label_rows.append({
                    "candidate_id": row["candidate_id"], "document_id": row["document_id"],
                    "event_family": family, "event_type": row["candidate_event_type"],
                    "target_company": row["target_company"], "source_span": row["exact_candidate_span"],
                    "independent_disposition": disposition, "target_entity": label["target_entity"],
                    "event_timing_status": label["temporal_state"], "polarity": label["polarity"],
                    "third_party_attribution": str(label["third_party"]).lower(),
                    "hypothetical_or_historical": str(label["historical_or_hypothetical"]).lower(),
                    "severe_if_accepted": str(label["severe_if_accepted"]).lower(),
                    "exact_support_span": label["exact_support_span"], "review_notes": label["rationale"],
                    "reviewer_type": "AI_ASSISTED_FINOPS_REVIEW",
                    "reviewer_identity": "OpenAI gpt-5-mini source-first reviewer",
                    "formal_independent_human_gold": "false", "admissible_for_model2_gate": "false",
                    "annotation_timestamp": datetime.now(UTC).isoformat(),
                })
    candidate_path = DATA / "fresh_frozen_candidates.jsonl"
    label_path = DATA / "fresh_ai_source_first_labels.csv"
    candidate_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in selected))
    with label_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(label_rows[0]))
        writer.writeheader(); writer.writerows(label_rows)
    freeze = {
        "freeze_version": "evidence-engine-v0.3.6-source-first-label-candidate-v1",
        "reviewer_type": "AI_ASSISTED_FINOPS_REVIEW", "formal_independent_human_gold": False,
        "admissible_for_model2_gate": False, "candidate_count": len(selected),
        "candidate_sha256": sha(candidate_path), "label_sha256": sha(label_path),
        "review_batch_id": batch_id, "review_raw_sha256": sha(RUN / "raw_output.jsonl"),
        "review_completed": len(parsed), "review_incomplete": len(failed_review_ids),
        "review_incomplete_candidate_ids": sorted(failed_review_ids),
        "source_pool_freeze_sha256": sha(DATA / "fresh_source_pool_freeze.json"),
        "family_contract_sha256": sha(CONTRACTS),
        "family_counts": {family: {name: sum(row["event_family"] == family and row["independent_disposition"] == name
                                                    for row in label_rows)
                                   for name in ("supported", "unsupported", "ambiguous")}
                          for family in sorted(grouped)},
        "semantic_v036_executed": False, "outcomes_accessed": False, "usage": usage,
    }
    freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps(freeze, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
