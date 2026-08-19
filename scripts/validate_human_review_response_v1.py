from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "reviewer_pack_human_ambiguity_v1"

ENUMS = {
    "factual_observation": {"YES", "NO", "AMBIGUOUS"},
    "timing": {"CURRENT", "ONGOING", "PLANNED_COMMITTED", "COMPLETED_RECENT", "HISTORICAL", "HYPOTHETICAL", "UNCLEAR"},
    "polarity": {"INCREASE", "DECREASE", "POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "NOT_APPLICABLE", "UNCLEAR"},
    "entity_relationship": {"ISSUER", "SUBSIDIARY", "CUSTOMER", "SUPPLIER", "COMPETITOR", "INDUSTRY", "OTHER", "UNCLEAR"},
    "reviewer_confidence": {"HIGH", "MEDIUM", "LOW"},
}
FIELDS = ["case_id", "factual_observation", "subject", "action_or_state", "object", "timing", "polarity", "scope", "entity_relationship", "exact_evidence_span", "reviewer_confidence", "reviewer_notes"]


def validate(path: Path, cases_path: Path, allow_blank: bool = False) -> list[dict[str, str]]:
    answers = json.loads(path.read_text())
    cases = json.loads(cases_path.read_text())
    contexts = {row["case_id"]: row["bounded_evidence_context"] for row in cases}
    if not isinstance(answers, list) or len(answers) != 36:
        raise ValueError("response must contain exactly 36 rows")
    if {row.get("case_id") for row in answers} != set(contexts):
        raise ValueError("response case IDs do not match the frozen reviewer pack")
    for row in answers:
        if set(row) != set(FIELDS):
            raise ValueError(f"{row.get('case_id')}: fields do not match schema")
        if allow_blank and not row["factual_observation"]:
            if any(row[field] for field in FIELDS if field != "case_id"):
                raise ValueError(f"{row['case_id']}: blank template row is partially populated")
            continue
        for field, values in ENUMS.items():
            if row[field] not in values:
                raise ValueError(f"{row['case_id']}: invalid {field}")
        if row["factual_observation"] == "YES":
            required = ["subject", "action_or_state", "object", "timing", "polarity", "scope", "entity_relationship", "exact_evidence_span", "reviewer_confidence"]
            if any(not row[field].strip() for field in required):
                raise ValueError(f"{row['case_id']}: YES response lacks a mandatory atomic-observation field")
            span = " ".join(row["exact_evidence_span"].split())
            context = " ".join(contexts[row["case_id"]].split())
            if span not in context:
                raise ValueError(f"{row['case_id']}: evidence span is not an exact supplied-context substring")
        elif not row["reviewer_confidence"]:
            raise ValueError(f"{row['case_id']}: confidence is required")
    return answers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("response", type=Path)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--allow-blank-template", action="store_true")
    args = parser.parse_args()
    validate(args.response, args.cases, args.allow_blank_template)
    print("HUMAN_REVIEW_RESPONSE_VALID")


if __name__ == "__main__":
    main()
