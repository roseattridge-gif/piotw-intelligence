from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.batch_api import response_output_text
from evidence_engine_v0_3_6.families import route_family
from scripts.prepare_evidence_v036_fresh_corpus import BROAD_LOCATORS

DATA = ROOT / "data/evidence_engine_v0_3_6"
RUN = ROOT / "data/derived/evidence_engine_v0_3_6_source_first_review"
POOL = DATA / "fresh_candidate_pool.jsonl"
RAW = RUN / "raw_output.jsonl"
LABELS = DATA / "fresh_ai_source_first_labels.csv"
CANDIDATES = DATA / "fresh_frozen_candidates.jsonl"
FREEZE = DATA / "fresh_label_candidate_freeze.json"
MANUAL_UNSUPPORTED = {"a326de3c8fc760fa717f4aab"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if FREEZE.exists():
        raise RuntimeError("fresh labels already frozen")
    pool = [json.loads(line) for line in POOL.read_text().splitlines() if line.strip()]
    by_id = {row["candidate_id"]: row for row in pool}
    labels: dict[str, dict] = {}
    incomplete: list[str] = []
    usage = {"input_tokens": 0, "output_tokens": 0}
    for line in RAW.read_text().splitlines():
        item = json.loads(line)
        candidate_id = item["custom_id"].removeprefix("source-first-")
        body = item["response"]["body"]
        usage["input_tokens"] += (body.get("usage") or {}).get("input_tokens", 0)
        usage["output_tokens"] += (body.get("usage") or {}).get("output_tokens", 0)
        output = response_output_text(body)
        if body.get("status") != "completed" or not output:
            incomplete.append(candidate_id)
            continue
        label = json.loads(output)
        if label["candidate_id"] != candidate_id:
            raise RuntimeError(f"review membership mismatch: {candidate_id}")
        if label["disposition"] == "supported" and label["exact_support_span"] not in by_id[candidate_id]["context"]:
            incomplete.append(candidate_id)
            continue
        labels[candidate_id] = label

    for candidate_id in MANUAL_UNSUPPORTED:
        row = by_id[candidate_id]
        labels[candidate_id] = {
            "candidate_id": candidate_id, "disposition": "unsupported",
            "target_entity": "target_company", "temporal_state": "historical",
            "polarity": "neutral", "third_party": False,
            "historical_or_hypothetical": True, "severe_if_accepted": True,
            "exact_support_span": "",
            "rationale": "Historical executive appointment does not establish a current leadership change.",
            "reviewer_identity": "Codex GPT-5.6 Sol source-first review",
        }

    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in pool:
        if row["candidate_id"] in labels:
            grouped[route_family(row["candidate_event_type"])][labels[row["candidate_id"]]["disposition"]].append(row)

    selected: list[dict] = []
    label_rows: list[dict[str, str]] = []

    def append(row: dict, family: str, label: dict, reviewer: str) -> None:
        selected.append(row)
        label_rows.append({
            "candidate_id": row["candidate_id"], "document_id": row["document_id"],
            "event_family": family, "event_type": row["candidate_event_type"],
            "target_company": row["target_company"], "source_span": row["exact_candidate_span"],
            "independent_disposition": label["disposition"], "target_entity": label["target_entity"],
            "event_timing_status": label["temporal_state"], "polarity": label["polarity"],
            "third_party_attribution": str(label["third_party"]).lower(),
            "hypothetical_or_historical": str(label["historical_or_hypothetical"]).lower(),
            "severe_if_accepted": str(label["severe_if_accepted"]).lower(),
            "exact_support_span": label["exact_support_span"], "review_notes": label["rationale"],
            "reviewer_type": "AI_ASSISTED_FINOPS_REVIEW", "reviewer_identity": reviewer,
            "formal_independent_human_gold": "false", "admissible_for_model2_gate": "false",
            "annotation_timestamp": datetime.now(UTC).isoformat(),
        })

    for family in sorted(grouped):
        for disposition in ("supported", "unsupported"):
            available = sorted(grouped[family][disposition], key=lambda row: row["candidate_id"])
            if len(available) < 12:
                raise RuntimeError(f"insufficient {disposition} labels for {family}: {len(available)}/12")
            for row in available[:12]:
                identity = labels[row["candidate_id"]].get(
                    "reviewer_identity", "OpenAI gpt-5-mini source-first reviewer"
                )
                append(row, family, labels[row["candidate_id"]], identity)

        sparse = []
        seen_documents = set()
        for row in sorted((item for item in pool if route_family(item["candidate_event_type"]) == family),
                          key=lambda item: item["candidate_id"]):
            pattern = BROAD_LOCATORS.get(row["candidate_event_type"])
            match = re.search(pattern, row["exact_candidate_span"], re.IGNORECASE) if pattern else None
            if not match:
                continue
            fragment = match.group(0)
            key = (row["document_id"], row["candidate_event_type"], fragment.casefold())
            if key in {(item["document_id"], item["candidate_event_type"], item["exact_candidate_span"].casefold()) for item in sparse}:
                continue
            candidate = {**row, "candidate_id": hashlib.sha256(
                f"sparse|{row['document_id']}|{row['candidate_event_type']}|{fragment}".encode()
            ).hexdigest()[:24], "exact_candidate_span": fragment, "context": fragment,
                "deterministic_metadata": {**row["deterministic_metadata"],
                    "candidate_locator": "fresh_sparse_source_fragment_v1", "factual_status": "unresolved"}}
            sparse.append(candidate)
            seen_documents.add(row["document_id"])
            if len(sparse) == 6:
                break
        if len(sparse) < 6:
            raise RuntimeError(f"insufficient sparse real-source fragments for {family}")
        for row in sparse:
            append(row, family, {
                "disposition": "ambiguous", "target_entity": "unclear", "temporal_state": "unclear",
                "polarity": "unclear", "third_party": False, "historical_or_hypothetical": False,
                "severe_if_accepted": True, "exact_support_span": "",
                "rationale": "The real-source fragment lacks enough context to establish subject, actuality and timing.",
            }, "Codex GPT-5.6 Sol source-first sparse-context review")

    CANDIDATES.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in selected))
    with LABELS.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(label_rows[0])); writer.writeheader(); writer.writerows(label_rows)
    freeze = {
        "freeze_version": "evidence-engine-v0.3.6-source-first-label-candidate-v1",
        "reviewer_type": "AI_ASSISTED_FINOPS_REVIEW", "formal_independent_human_gold": False,
        "admissible_for_model2_gate": False, "candidate_count": len(selected),
        "candidate_sha256": sha(CANDIDATES), "label_sha256": sha(LABELS),
        "review_batch_id": json.loads((RUN / "state.json").read_text())["batch_id"],
        "review_raw_sha256": sha(RAW), "review_completed": len(labels),
        "review_incomplete": len(set(incomplete) - MANUAL_UNSUPPORTED),
        "source_pool_freeze_sha256": sha(DATA / "fresh_source_pool_freeze.json"),
        "family_contract_sha256": sha(ROOT / "config/evidence/event_family_contracts_v0_3_6.json"),
        "family_counts": {family: {name: sum(row["event_family"] == family and row["independent_disposition"] == name
                                                    for row in label_rows)
                                   for name in ("supported", "unsupported", "ambiguous")}
                          for family in sorted(grouped)},
        "semantic_v036_executed": False, "outcomes_accessed": False, "usage": usage,
    }
    FREEZE.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps(freeze, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
