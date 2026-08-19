from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "reviewer_pack_human_ambiguity_v1"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_human_review_response_v1 import validate


def norm(value: str) -> str:
    return " ".join(value.casefold().split())


def materially_equal(a: dict[str, str], b: dict[str, str]) -> bool:
    if a["factual_observation"] != b["factual_observation"]:
        return False
    if a["factual_observation"] != "YES":
        return True
    exact = ("timing", "polarity", "entity_relationship")
    text = ("subject", "action_or_state", "object", "scope")
    return all(a[key] == b[key] for key in exact) and all(norm(a[key]) == norm(b[key]) for key in text)


def ratio(correct: int, total: int) -> dict[str, int | float | None]:
    return {"correct": correct, "total": total, "rate": round(correct / total, 6) if total else None}


def compare(a_rows: list[dict[str, str]], b_rows: list[dict[str, str]], membership: dict) -> dict:
    a = {row["case_id"]: row for row in a_rows}
    b = {row["case_id"]: row for row in b_rows}
    factual = sum(a[c]["factual_observation"] == b[c]["factual_observation"] for c in a)
    material = sum(materially_equal(a[c], b[c]) for c in a)
    joint_yes = [c for c in a if a[c]["factual_observation"] == b[c]["factual_observation"] == "YES"]
    categories: dict[str, list[str]] = defaultdict(list)
    for case in membership["cases"]:
        for category in case["ambiguity_categories"]:
            categories[category].append(case["case_id"])
    by_category = {
        category: ratio(sum(materially_equal(a[c], b[c]) for c in ids), len(ids))
        for category, ids in sorted(categories.items())
    }
    return {
        "status": "HUMAN_HUMAN_COMPARISON_ONLY",
        "case_count": len(a),
        "factual_observation_agreement": ratio(factual, len(a)),
        "material_overall_agreement": ratio(material, len(a)),
        "timing_agreement_joint_yes": ratio(sum(a[c]["timing"] == b[c]["timing"] for c in joint_yes), len(joint_yes)),
        "entity_agreement_joint_yes": ratio(sum(a[c]["entity_relationship"] == b[c]["entity_relationship"] for c in joint_yes), len(joint_yes)),
        "agreement_by_ambiguity_category": by_category,
        "material_disagreement_case_ids": [c for c in sorted(a) if not materially_equal(a[c], b[c])],
        "warning": "Human-vs-AI and human-vs-0.3.6 comparisons require separately frozen adjudication and are not populated by this tool run.",
    }


def add_adjudicated_diagnostics(result: dict, adjudicated_rows: list[dict[str, str]], membership: dict) -> None:
    human = {row["case_id"]: row for row in adjudicated_rows}
    baseline = {row["case_id"]: row for row in membership["cases"]}
    human_to_ai = {"YES": "supported", "NO": "unsupported", "AMBIGUOUS": "ambiguous"}
    human_to_engine = {"YES": "accept", "NO": "reject", "AMBIGUOUS": "ambiguous"}
    ai_matches = sum(human_to_ai[human[c]["factual_observation"]] == baseline[c]["original_ai_label"] for c in human)
    engine_matches = sum(human_to_engine[human[c]["factual_observation"]] == baseline[c]["original_v036_decision"] for c in human)
    timing = sum(human[c]["timing"].casefold() == baseline[c]["original_ai_timing"].casefold() for c in human if human[c]["factual_observation"] == "YES")
    timing_total = sum(human[c]["factual_observation"] == "YES" for c in human)
    entity = sum(human[c]["entity_relationship"] == baseline[c]["original_ai_entity_relationship"] for c in human if human[c]["factual_observation"] == "YES")
    result["adjudicated_human_vs_ai_factual_agreement"] = ratio(ai_matches, len(human))
    result["adjudicated_human_vs_v036_decision_agreement"] = ratio(engine_matches, len(human))
    result["adjudicated_human_vs_ai_timing_agreement"] = ratio(timing, timing_total)
    result["adjudicated_human_vs_ai_entity_agreement"] = ratio(entity, timing_total)
    result["status"] = "FULL_POST_ADJUDICATION_DIAGNOSTIC"
    result.pop("warning", None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewer-a", type=Path, required=True)
    parser.add_argument("--reviewer-b", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--adjudicated", type=Path)
    args = parser.parse_args()
    a = validate(args.reviewer_a, PACK / "reviewer_A/cases.json")
    b = validate(args.reviewer_b, PACK / "reviewer_B/cases.json")
    membership = json.loads((PACK / "internal_do_not_share/frozen_36_case_membership.json").read_text())
    result = compare(a, b, membership)
    if args.adjudicated:
        adjudicated = validate(args.adjudicated, PACK / "reviewer_A/cases.json")
        add_adjudicated_diagnostics(result, adjudicated, membership)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
