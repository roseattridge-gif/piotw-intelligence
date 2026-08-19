from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_6.families import route_family

DATA = ROOT / "data/evidence_engine_v0_3_6"
POOL = DATA / "fresh_candidate_pool.jsonl"
CONTRACTS = ROOT / "config/evidence/event_family_contracts_v0_3_6.json"
RAW = DATA / "fresh_source_first_reviewer_raw.json"
LABELS = DATA / "fresh_ai_source_first_labels.csv"
CANDIDATES = DATA / "fresh_frozen_candidates.jsonl"
FREEZE = DATA / "fresh_label_candidate_freeze.json"
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


def schema(count: int) -> dict:
    item = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "candidate_id", "disposition", "target_entity", "temporal_state", "polarity",
            "third_party", "historical_or_hypothetical", "severe_if_accepted",
            "exact_support_span", "rationale",
        ],
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
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["labels"],
        "properties": {"labels": {"type": "array", "items": item, "minItems": count, "maxItems": count}},
    }


def main() -> None:
    if FREEZE.exists():
        raise RuntimeError("source-first labels are already frozen; do not regenerate")
    load_key()
    rows = [json.loads(line) for line in POOL.read_text().splitlines() if line.strip()]
    by_family: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        family = route_family(row["candidate_event_type"])
        if family:
            by_family[family].append(row)
    contracts = json.loads(CONTRACTS.read_text())["families"]
    client = OpenAI(max_retries=2)
    raw_results: dict[str, dict] = {}
    all_labels: dict[str, dict] = {}
    usage = {"input_tokens": 0, "output_tokens": 0}
    for family in sorted(by_family):
        candidates = sorted(by_family[family], key=lambda row: row["candidate_id"])
        family_chunks = []
        for offset in range(0, len(candidates), 20):
            chunk = candidates[offset:offset + 20]
            payload = [{
                "candidate_id": row["candidate_id"],
                "company": row["target_company"],
                "event_type": row["candidate_event_type"],
                "candidate_span": row["exact_candidate_span"],
                "surrounding_context": row["context"][:3500],
                "publication_date": row["publication_date"],
            } for row in chunk]
            prompt = (
            "You are performing a blinded, source-first finance/operations annotation. "
            "You have not seen and must not infer any PIOTW model decision. Classify every supplied "
            "candidate against only the supplied family contract and evidence. SUPPORTED means the "
            "source directly establishes the proposed event for the target issuer within the family "
            "definition. UNSUPPORTED includes hypothetical risk, historical-only background, third-party "
            "events without direct issuer effect, headings/definitions, metric names, product names and "
            "wrong polarity/object. AMBIGUOUS means the supplied evidence is genuinely insufficient. "
            "For supported rows exact_support_span must be a verbatim substring of surrounding_context; "
            "otherwise use an empty string. Return exactly one label for every candidate_id.\n\n"
            f"Family: {family}\nContract: {json.dumps(contracts[family], sort_keys=True)}\n\n"
                f"Candidates: {json.dumps(payload, ensure_ascii=False)}"
            )
            response = client.responses.create(
                model=MODEL,
                max_output_tokens=12000,
                input=prompt,
                text={"format": {"type": "json_schema", "name": "source_first_labels", "strict": True, "schema": schema(len(chunk))}},
            )
            parsed = json.loads(response.output_text)
            labels = parsed["labels"]
            expected = {row["candidate_id"] for row in chunk}
            returned = [row["candidate_id"] for row in labels]
            if len(returned) != len(expected) or set(returned) != expected:
                raise RuntimeError(f"reviewer membership mismatch for {family} chunk {offset // 20}")
            for label in labels:
                candidate = next(row for row in chunk if row["candidate_id"] == label["candidate_id"])
                if label["disposition"] == "supported" and label["exact_support_span"] not in candidate["context"]:
                    raise RuntimeError(f"non-verbatim reviewer evidence for {label['candidate_id']}")
                all_labels[label["candidate_id"]] = label
            usage["input_tokens"] += response.usage.input_tokens
            usage["output_tokens"] += response.usage.output_tokens
            family_chunks.append({
                "response_id": response.id,
                "candidate_count": len(chunk),
                "labels": labels,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            })
        raw_results[family] = {"candidate_count": len(candidates), "chunks": family_chunks}

    selected: list[dict] = []
    label_rows: list[dict[str, str]] = []
    for family in sorted(by_family):
        family_rows = sorted(by_family[family], key=lambda row: row["candidate_id"])
        buckets = defaultdict(list)
        for row in family_rows:
            buckets[all_labels[row["candidate_id"]]["disposition"]].append(row)
        required = {"supported": 12, "unsupported": 12, "ambiguous": 6}
        short = {name: amount - len(buckets[name]) for name, amount in required.items() if len(buckets[name]) < amount}
        if short:
            raise RuntimeError(f"insufficient source-first labels for {family}: {short}")
        for disposition, amount in required.items():
            for row in buckets[disposition][:amount]:
                label = all_labels[row["candidate_id"]]
                selected.append(row)
                label_rows.append({
                    "candidate_id": row["candidate_id"],
                    "document_id": row["document_id"],
                    "event_family": family,
                    "event_type": row["candidate_event_type"],
                    "target_company": row["target_company"],
                    "source_span": row["exact_candidate_span"],
                    "independent_disposition": disposition,
                    "target_entity": label["target_entity"],
                    "event_timing_status": label["temporal_state"],
                    "polarity": label["polarity"],
                    "third_party_attribution": str(label["third_party"]).lower(),
                    "hypothetical_or_historical": str(label["historical_or_hypothetical"]).lower(),
                    "severe_if_accepted": str(label["severe_if_accepted"]).lower(),
                    "exact_support_span": label["exact_support_span"],
                    "review_notes": label["rationale"],
                    "reviewer_type": "AI_ASSISTED_FINOPS_REVIEW",
                    "reviewer_identity": "OpenAI gpt-5-mini source-first reviewer",
                    "formal_independent_human_gold": "false",
                    "admissible_for_model2_gate": "false",
                    "annotation_timestamp": datetime.now(UTC).isoformat(),
                })

    RAW.write_text(json.dumps({"model": MODEL, "usage": usage, "families": raw_results}, indent=2, sort_keys=True) + "\n")
    CANDIDATES.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in selected))
    with LABELS.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(label_rows[0]))
        writer.writeheader()
        writer.writerows(label_rows)
    freeze = {
        "freeze_version": "evidence-engine-v0.3.6-source-first-label-candidate-v1",
        "reviewer_type": "AI_ASSISTED_FINOPS_REVIEW",
        "formal_independent_human_gold": False,
        "admissible_for_model2_gate": False,
        "candidate_count": len(selected),
        "candidate_sha256": sha(CANDIDATES),
        "label_sha256": sha(LABELS),
        "raw_reviewer_sha256": sha(RAW),
        "source_pool_freeze_sha256": sha(DATA / "fresh_source_pool_freeze.json"),
        "family_contract_sha256": sha(CONTRACTS),
        "family_counts": {
            family: {name: sum(row["event_family"] == family and row["independent_disposition"] == name for row in label_rows)
                     for name in ("supported", "unsupported", "ambiguous")}
            for family in sorted(by_family)
        },
        "semantic_v036_executed": False,
        "outcomes_accessed": False,
        "usage": usage,
    }
    FREEZE.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps(freeze, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
