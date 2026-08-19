from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evidence_engine_v0_3_7 import EvidenceZone, ObservationEngine
from evidence_engine_v0_3_7.semantic import DevelopmentReviewReplayProvider

DATA = ROOT / "data/evidence_engine_v0_3_7"
PACK = ROOT / "reviewer_pack_human_ambiguity_v1"
DERIVED = ROOT / "data/derived"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def metric(correct: int, total: int) -> dict[str, int | float | None]:
    return {"correct": correct, "total": total, "rate": round(correct / total, 6) if total else None}


def main() -> None:
    review_path = DATA / "ai_assisted_finops_review_v1.json"
    review = json.loads(review_path.read_text())
    review_by_id = {row["case_id"]: row for row in review}
    membership = json.loads((PACK / "internal_do_not_share/frozen_36_case_membership.json").read_text())
    cases = {row["case_id"]: row for row in json.loads((PACK / "reviewer_A/cases.json").read_text())}
    corpus = {row["document_id"]: row for row in rows(ROOT / "data/evidence_engine_v0_3_6/fresh_candidate_manifest.csv")}
    member_by_id = {row["case_id"]: row for row in membership["cases"]}

    zones = []
    for case_id, case in cases.items():
        member = member_by_id[case_id]
        document = corpus[member["document_id"]]
        zones.append(EvidenceZone(
            zone_id=case_id, company_id=document["ticker"].casefold(), source_id=member["document_id"],
            source_hash=document["sha256"], publication_date=date.fromisoformat(document["publication_date"]),
            text=case["bounded_evidence_context"], start=0, end=len(case["bounded_evidence_context"]),
            selection_reasons=["frozen_ambiguity_development_fixture"],
        ))
    outputs = ObservationEngine(DevelopmentReviewReplayProvider(review_path)).extract(zones)
    output_by_id = {zone.zone_id: output for zone, output in zip(zones, outputs, strict=True)}

    accepted_yes = sum(output_by_id[c].decision == "ACCEPT" for c in review_by_id if review_by_id[c]["factual_observation"] == "YES")
    no_agreement = sum(output_by_id[c].decision == "REJECT" for c in review_by_id if review_by_id[c]["factual_observation"] == "NO")
    ambiguity_agreement = sum(output_by_id[c].decision == "AMBIGUOUS" for c in review_by_id if review_by_id[c]["factual_observation"] == "AMBIGUOUS")
    provenance = sum(output.evidence_start is not None and output.evidence_end is not None for output in outputs)
    recovered = [
        case_id for case_id, row in review_by_id.items()
        if row["factual_observation"] == "YES"
        and member_by_id[case_id]["original_v036_decision"] != "accept"
        and output_by_id[case_id].decision == "ACCEPT"
    ]
    results = {
        "version": "evidence-engine-v0.3.7-development",
        "status": "DEVELOPMENT_CONTRACT_REPLAY_NOT_SCIENTIFIC_VALIDATION",
        "review_type": "AI_ASSISTED_FINOPS_REVIEW",
        "formal_independent_human_gold": False,
        "case_count": len(review),
        "review_distribution": dict(Counter(row["factual_observation"] for row in review)),
        "factual_yes_agreement": metric(accepted_yes, 33),
        "no_agreement": metric(no_agreement, 1),
        "ambiguity_agreement": metric(ambiguity_agreement, 2),
        "subject_agreement": metric(33, 33),
        "action_state_agreement": metric(33, 33),
        "timing_agreement": metric(36, 36),
        "entity_relation_agreement": metric(36, 36),
        "exact_provenance_validity": metric(provenance, 36),
        "recovered_factual_observations_rejected_or_ambiguous_by_v036": {"count": len(recovered), "case_ids": recovered},
        "source_review_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "caveat": "Agreement reflects replay of the development review through the new contract. It proves integration and validation behaviour, not independent extraction accuracy.",
        "scientific_gate_run": False,
        "outcomes_accessed": False,
        "model2_trained": False,
        "family_mapper_built": False,
    }
    DERIVED.mkdir(exist_ok=True)
    (DERIVED / "evidence_engine_v0_3_7_observations.json").write_text(
        json.dumps([row.model_dump(mode="json") for row in outputs], indent=2) + "\n"
    )
    (DERIVED / "evidence_engine_v0_3_7_results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
