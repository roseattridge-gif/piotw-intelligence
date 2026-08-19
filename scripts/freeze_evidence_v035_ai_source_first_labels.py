from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/evidence_engine_v0_3_5"

# Source-first review completed from the candidate evidence spans without running or viewing 0.3.5.
# These row numbers are review aids only; candidate IDs are the frozen identities written to the file.
UNSUPPORTED = {1, 3, 4, 5, 6, 8, 19, 43, 44, 47, 48, 49, 53, 54, 59, 60, 65, 66,
               70, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 96, 110, 121, 136, 137,
               138, 141, 143, 146, 148, 149, 150, 151, 153, 156}
AMBIGUOUS = {50}
SEVERE = {59, 77, 78, 79, 80, 81, 143, 148, 156}
ATTRIBUTION = {43, 44, 148}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source_freeze = json.loads((DATA / "fresh_source_candidate_freeze.json").read_text())
    candidate_path = DATA / "fresh_candidates.jsonl"
    if sha(candidate_path) != source_freeze["candidate_manifest_sha256"]:
        raise RuntimeError("candidate manifest changed after source/candidate freeze")
    candidates = [json.loads(line) for line in candidate_path.read_text().splitlines()]
    rows = []
    for index, candidate in enumerate(candidates, 1):
        disposition = "ambiguous" if index in AMBIGUOUS else "unsupported" if index in UNSUPPORTED else "supported"
        metadata = candidate["deterministic_metadata"]
        rows.append({"candidate_id": candidate["candidate_id"], "document_id": candidate["document_id"],
            "event_type": candidate["candidate_event_type"], "target_company": candidate["target_company"],
            "source_span": candidate["exact_candidate_span"], "independent_disposition": disposition,
            "event_timing_status": metadata.get("event_status") or "ambiguous",
            "third_party_attribution": str(index in ATTRIBUTION).lower(),
            "hypothetical_or_historical": str(index in UNSUPPORTED and index in {1, 3, 4, 5, 43, 44, 47, 48, 49, 53, 60, 65, 66, 82, 83, 84, 85, 86, 110, 136, 137, 138, 141, 146, 149, 150, 153}).lower(),
            "severe_if_accepted": str(index in SEVERE).lower(),
            "review_notes": ("Direct factual source support for the proposed target-company event."
                if disposition == "supported" else "Source-first review found insufficient, wrong-polarity, historical, generic, accounting-only or non-target support."
                if disposition == "unsupported" else "The supplied span does not resolve the event status sufficiently."),
            "reviewer_type": "AI_ASSISTED_FINOPS_REVIEW", "reviewer_identity": "OpenAI Codex GPT-5",
            "formal_independent_human_gold": "false", "admissible_for_model2_gate": "false",
            "annotation_timestamp": "2026-08-18"})
    label_path = DATA / "fresh_ai_source_first_labels.csv"
    with label_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    schema = {"version": "v0.3.5-ai-source-first-v1", "statuses": ["supported", "unsupported", "ambiguous"],
        "reviewer_type": "AI_ASSISTED_FINOPS_REVIEW", "formal_independent_human_gold": False,
        "admissible_for_model2_gate": False,
        "method": "source evidence to independent label; 0.3.5 decisions unavailable during annotation"}
    schema_path = DATA / "fresh_annotation_schema.json"
    schema_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    freeze = {"freeze_version": "evidence-engine-v0.3.5-ai-source-first-gold-v1",
        "frozen_at": "2026-08-18", "labels": len(rows), "label_sha256": sha(label_path),
        "schema_sha256": sha(schema_path), "source_candidate_freeze_sha256": sha(DATA / "fresh_source_candidate_freeze.json"),
        "semantic_v035_executed_before_label_freeze": False, "formal_independent_human_gold": False,
        "admissible_for_model2_gate": False}
    (DATA / "fresh_gold_freeze.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    print(json.dumps(freeze, indent=2))


if __name__ == "__main__":
    main()
