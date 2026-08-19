from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.semantic import SemanticCandidate
from evidence_engine_v0_3_6.families import route_family, verify_candidate

LABELS = ROOT / "data/evidence_engine_v0_3_5/fresh_ai_source_first_labels.csv"
PARSED = ROOT / "data/derived/evidence_engine_v0_3_5_fresh_gate/parsed_results.json"
OUT_CSV = ROOT / "data/derived/evidence_engine_v0_3_6_failure_matrix.csv"
OUT_JSON = ROOT / "data/derived/evidence_engine_v0_3_6_architecture_results.json"

SEVERE_ROOTS = {
    "6036eda230c1b93edb55bb45": "polarity_cost_growth_not_demand_growth",
    "fb9446ab670a4b499dade11f": "polarity_cost_growth_not_demand_growth",
    "4017487a6d1666dd65c10680": "polarity_cost_growth_not_demand_growth",
    "ba0802bd67067965e0b8f699": "polarity_cost_growth_not_demand_growth",
    "c07b3d38c39a2597d37ed219": "polarity_cost_growth_not_demand_growth",
    "01e245467a73afe75734d700": "taxonomy_identity_product_or_programme_name",
    "8dd70afd69453d89aa0c341c": "target_attribution_third_party_customer",
}


def _bool(value: str) -> bool:
    return value.lower() == "true"


def _root(label: dict[str, str], decision: dict | None, failure: str) -> str:
    candidate_id = label["candidate_id"]
    if candidate_id in SEVERE_ROOTS:
        return SEVERE_ROOTS[candidate_id]
    if _bool(label["third_party_attribution"]):
        return "target_attribution"
    if _bool(label["hypothetical_or_historical"]):
        return "actuality_or_timing"
    if failure == "false_negative":
        reason = (decision or {}).get("reason_code", "provider_failure").lower()
        return f"over_rejection_{reason}"
    return "taxonomy_identity_or_insufficient_context"


def main() -> None:
    labels = list(csv.DictReader(LABELS.open()))
    parsed = json.loads(PARSED.read_text())
    decisions = {row["candidate_id"]: row["parsed_decision"] for row in parsed["successful"]}
    matrix: list[dict[str, str]] = []
    proof = Counter()
    proof_by_family: dict[str, Counter] = {}
    for label in labels:
        candidate_id = label["candidate_id"]
        decision = decisions.get(candidate_id)
        accepted = bool(decision and decision["decision"] == "accept")
        supported = label["independent_disposition"] == "supported"
        if accepted and not supported:
            failure = "false_positive"
        elif supported and not accepted:
            failure = "false_negative"
        else:
            failure = "correct"
        if failure != "correct":
            matrix.append({
                "candidate_id": candidate_id,
                "document_id": label["document_id"],
                "event_type": label["event_type"],
                "source_span": label["source_span"],
                "diagnostic_label": label["independent_disposition"],
                "v0_3_5_decision": (decision or {}).get("decision", "provider_failure"),
                "v0_3_5_reason": (decision or {}).get("reason_code", "provider_failure"),
                "failure_class": failure,
                "root_cause": _root(label, decision, failure),
                "severe": str(candidate_id in SEVERE_ROOTS).lower(),
                "formal_gold": "false",
                "contamination_status": "DEVELOPMENT_CONTAMINATED_NOT_VALIDATION",
            })

        family = route_family(label["event_type"])
        if family is None:
            continue
        subject = "third_party" if _bool(label["third_party_attribution"]) else "target_company"
        candidate = SemanticCandidate(
            target_company=label["target_company"],
            candidate_event_type=label["event_type"],
            exact_candidate_span=label["source_span"],
            context=label["source_span"],
            heading=None,
            publication_date=None,
            deterministic_metadata={"subject_type": subject},
        )
        result = verify_candidate(candidate)
        bucket = proof_by_family.setdefault(family, Counter())
        proof["cases"] += 1
        bucket["cases"] += 1
        if result.disposition == "accept" and supported:
            outcome = "true_positive"
        elif result.disposition == "accept" and not supported:
            outcome = "false_positive"
        elif result.disposition != "accept" and supported:
            outcome = "missed_supported"
        else:
            outcome = "true_rejection"
        proof[outcome] += 1
        bucket[outcome] += 1

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(matrix[0]))
        writer.writeheader()
        writer.writerows(matrix)
    output = {
        "version": "evidence-engine-v0.3.6-architecture-phase",
        "scientific_status": "DEVELOPMENT_CONTAMINATED_NOT_VALIDATION",
        "source_label_sha256": hashlib.sha256(LABELS.read_bytes()).hexdigest(),
        "failure_matrix_sha256": hashlib.sha256(OUT_CSV.read_bytes()).hexdigest(),
        "v0_3_5_failure_counts": dict(Counter(row["failure_class"] for row in matrix)),
        "v0_3_5_root_causes": dict(Counter(row["root_cause"] for row in matrix)),
        "representative_family_proof": {
            "overall": dict(proof),
            "by_family": {name: dict(counts) for name, counts in proof_by_family.items()},
        },
        "fresh_validation_run": False,
        "model2_trained": False,
        "outcomes_accessed": False,
        "official_model2_readiness": "NOT READY",
    }
    OUT_JSON.write_text(json.dumps(output, indent=2) + "\n")
    print(OUT_JSON)


if __name__ == "__main__":
    main()
