from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SLICE = ROOT / "data/derived/evidence_engine_v0_3_6_human_review_slice.csv"
LABELS = ROOT / "data/evidence_engine_v0_3_6/fresh_ai_source_first_labels.csv"
RESULTS = ROOT / "data/derived/evidence_engine_v0_3_6_fresh_validation_results.json"
CORPUS = ROOT / "data/evidence_engine_v0_3_6/fresh_candidate_manifest.csv"
PACK = ROOT / "reviewer_pack_human_ambiguity_v1"
INTERNAL = PACK / "internal_do_not_share"
COMMON = PACK / "common"
REVIEWERS = {"A": PACK / "reviewer_A", "B": PACK / "reviewer_B"}
MEMBERSHIP = INTERNAL / "frozen_36_case_membership.json"
SCHEMA = ROOT / "config/evidence/human_observation_review_response_v1.schema.json"
SEEDS = {"A": "piotw-human-review-v1-reviewer-a-order", "B": "piotw-human-review-v1-reviewer-b-order"}
FROZEN_AT = datetime.now(UTC).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def redact_issuer(text: str, company: str) -> str:
    variants = {company, company.replace(", INC.", ""), company.replace(" INC", ""), company.title()}
    result = text
    for variant in sorted((item for item in variants if len(item) >= 4), key=len, reverse=True):
        result = re.sub(re.escape(variant), "[ISSUER]", result, flags=re.IGNORECASE)
    return result.strip()


def categories(row: dict[str, str], label: dict[str, str]) -> list[str]:
    text = f"{row['source_span']} {row['surrounding_context']}".lower()
    found = {"event_identity_ambiguity"}
    if label["event_timing_status"] in {"historical", "current", "ongoing"} or re.search(r"\bfiscal 20\d\d\b", text):
        found.add("historical_vs_current")
    if label["event_timing_status"] == "hypothetical" or re.search(r"\b(?:may|might|could|risk of|possibility)\b", text):
        found.add("hypothetical_vs_actual")
    if re.search(r"\b(?:plan|planned|will|expect|committed|initiated|completed|ongoing)\b", text):
        found.add("planned_vs_realised")
    if re.search(r"\b(?:customer|supplier|competitor|industry|market participants?)\b", text):
        found.add("issuer_vs_third_party")
    if label["polarity"] in {"positive", "negative", "neutral", "unclear"}:
        found.add("polarity_ambiguity")
    if re.search(r"\b(?:appointed|named|resigned|stepped down|chief executive|chief financial)\b", text):
        found.add("executive_appointments")
    family_categories = {
        "restructuring_cost_action": "restructuring_cost_action",
        "demand_growth": "demand_growth",
        "supply_chain_resilience": "supply_chain",
        "workforce": "workforce",
        "delivery_capacity_sites": "capacity_sites",
        "quality_regulatory": "quality_regulatory",
        "leadership_change_execution": "change_leadership",
    }
    found.add(family_categories[row["event_family"]])
    return sorted(found)


def blank_response(case_id: str) -> dict[str, str]:
    return {
        "case_id": case_id,
        "factual_observation": "",
        "subject": "",
        "action_or_state": "",
        "object": "",
        "timing": "",
        "polarity": "",
        "scope": "",
        "entity_relationship": "",
        "exact_evidence_span": "",
        "reviewer_confidence": "",
        "reviewer_notes": "",
    }


def main() -> None:
    if MEMBERSHIP.exists():
        raise RuntimeError("human-review membership is already frozen; rebuilding is prohibited")
    source = read_csv(SOURCE_SLICE)
    if len(source) != 36 or len({row["candidate_id"] for row in source}) != 36:
        raise RuntimeError("expected exactly 36 unique source rows")
    labels = {row["candidate_id"]: row for row in read_csv(LABELS)}
    corpus = {row["document_id"]: row for row in read_csv(CORPUS)}
    results = json.loads(RESULTS.read_text())
    final = {row["candidate_id"]: row for row in results["final_rows"]}

    INTERNAL.mkdir(parents=True, exist_ok=False)
    COMMON.mkdir(parents=True, exist_ok=False)
    for directory in REVIEWERS.values():
        directory.mkdir(parents=True, exist_ok=False)

    membership_rows = []
    public_cases = []
    for index, row in enumerate(sorted(source, key=lambda item: item["candidate_id"]), start=1):
        case_id = f"HRV1-{index:03d}"
        document = corpus[row["document_id"]]
        label = labels[row["candidate_id"]]
        category_values = categories(row, label)
        context = redact_issuer(row["surrounding_context"], row["company"])
        public_cases.append({
            "case_id": case_id,
            "document_type": document["report_type"],
            "form": document["form"],
            "publication_date": document["publication_date"],
            "reporting_period": document["reporting_period"],
            "bounded_evidence_context": context,
        })
        result = final.get(row["candidate_id"])
        membership_rows.append({
            "case_id": case_id,
            "candidate_id": row["candidate_id"],
            "document_id": row["document_id"],
            "source_context_sha256": hashlib.sha256(context.encode()).hexdigest(),
            "ambiguity_categories": category_values,
            "original_ai_label": label["independent_disposition"],
            "original_ai_timing": label["event_timing_status"],
            "original_ai_entity_relationship": "OTHER" if label["third_party_attribution"] == "true" else "ISSUER",
            "original_v036_decision": result["final_disposition"] if result else "provider_incomplete",
        })

    category_counts: dict[str, int] = {}
    for row in membership_rows:
        for category in row["ambiguity_categories"]:
            category_counts[category] = category_counts.get(category, 0) + 1
    required_categories = {
        "historical_vs_current", "hypothetical_vs_actual", "planned_vs_realised",
        "issuer_vs_third_party", "event_identity_ambiguity", "polarity_ambiguity",
        "executive_appointments", "restructuring_cost_action", "demand_growth",
        "supply_chain", "workforce", "capacity_sites", "quality_regulatory",
    }
    missing = sorted(required_categories - category_counts.keys())
    if missing:
        raise RuntimeError(f"review slice lacks required ambiguity categories: {missing}")

    membership_payload = {
        "freeze_version": "piotw-human-ambiguity-review-membership-v1",
        "frozen_at": FROZEN_AT,
        "case_count": 36,
        "source_slice_sha256": sha(SOURCE_SLICE),
        "selection_rule": "the already-designed post-0.3.6 36-row slice; no outcome-based selection",
        "category_counts": category_counts,
        "cases": membership_rows,
        "formal_gold": False,
        "answers_present": False,
        "outcomes_accessed": False,
    }
    MEMBERSHIP.write_text(json.dumps(membership_payload, indent=2, sort_keys=True) + "\n")
    membership_sha = sha(MEMBERSHIP)

    public_by_id = {row["case_id"]: row for row in public_cases}
    for reviewer, directory in REVIEWERS.items():
        ordered_ids = sorted(public_by_id)
        random.Random(SEEDS[reviewer]).shuffle(ordered_ids)
        ordered_cases = [public_by_id[case_id] for case_id in ordered_ids]
        (directory / "cases.json").write_text(json.dumps(ordered_cases, indent=2) + "\n")
        (directory / "response_template.json").write_text(
            json.dumps([blank_response(case_id) for case_id in ordered_ids], indent=2) + "\n"
        )
        (directory / "order_manifest.json").write_text(json.dumps({
            "pack_version": "piotw-human-ambiguity-review-v1",
            "reviewer": reviewer,
            "membership_sha256": membership_sha,
            "ordering_seed_sha256": hashlib.sha256(SEEDS[reviewer].encode()).hexdigest(),
            "case_ids_in_order": ordered_ids,
        }, indent=2, sort_keys=True) + "\n")

    (COMMON / "answer_schema.json").write_bytes(SCHEMA.read_bytes())
    (INTERNAL / "comparison_baseline.json").write_text(json.dumps({
        "membership_sha256": membership_sha,
        "cases": membership_rows,
        "warning": "DO NOT SHARE: contains original AI-assisted and 0.3.6 decisions",
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"cases": 36, "membership_sha256": membership_sha,
                      "category_counts": category_counts}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
