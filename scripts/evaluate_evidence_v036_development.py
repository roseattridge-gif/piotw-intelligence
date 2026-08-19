from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.semantic import SemanticCandidate
from evidence_engine_v0_3_6.families import FAMILY_VERIFIERS, verify_candidate

CORPORA = [
    ROOT / "data/evidence_engine_v0_3_6/family_development_cases.json",
    ROOT / "data/evidence_engine_v0_3_6/final_hardening_cases.json",
]
CONTAMINATED = ROOT / "data/derived/evidence_engine_v0_3_6_architecture_results.json"
OUTPUT = ROOT / "data/derived/evidence_engine_v0_3_6_development_coverage.json"


def main() -> None:
    cases = [row for path in CORPORA for row in json.loads(path.read_text())["cases"]]
    family_rows: dict[str, list[dict]] = defaultdict(list)
    counts: dict[str, Counter] = defaultdict(Counter)
    for row in cases:
        metadata = {"subject_type": row["subject"], "entity_scope": "group",
                    "factual_status": "actual_current", "event_status": "current",
                    "allowed_remaps": [], "heading_only": row.get("heading_only", False),
                    "accounting_table_only": row.get("accounting_table_only", False)}
        candidate = SemanticCandidate("Example plc", row["event_type"], row["span"], row["span"],
                                      None, "2026-01-01", metadata)
        decision = verify_candidate(candidate)
        expected, actual = row["expected"], decision.disposition
        if expected == "accept" and actual == "accept": bucket = "supported_accepts"
        elif expected == "accept": bucket = "misses"
        elif expected == "reject" and actual == "reject": bucket = "correct_rejects"
        elif expected == "reject" and actual == "accept": bucket = "false_accepts"
        elif expected == "ambiguous" and actual == "ambiguous": bucket = "correct_ambiguous"
        else: bucket = "other_mismatch"
        counts[row["family"]][bucket] += 1
        counts[row["family"]]["cases"] += 1
        family_rows[row["family"]].append({**row, "actual": actual, "reason": decision.reason,
                                            "provenance_complete": decision.evidence_span == row["span"]})

    contaminated = json.loads(CONTAMINATED.read_text())["representative_family_proof"]["by_family"]
    readiness = {}
    for family in FAMILY_VERIFIERS:
        rows = family_rows[family]
        adversaries = {row["adversary"] for row in rows}
        checklist = {
            "positive_cases": any(row["expected"] == "accept" for row in rows),
            "negative_cases": any(row["expected"] == "reject" for row in rows),
            "ambiguous_cases": any(row["expected"] == "ambiguous" for row in rows),
            "attribution_adversary": "attribution" in adversaries,
            "polarity_adversary": bool(adversaries & {"polarity", "negative_polarity", "wrong_object",
                                                       "contraction", "expansion", "remediation", "quality",
                                                       "resilience_action"}),
            "temporal_adversary": bool(adversaries & {"historical", "hypothetical"}),
            "cross_family_adversary": "cross_family" in adversaries,
            "provenance_complete": all(row["provenance_complete"] for row in rows),
            "synthetic_contract_mismatches": sum(counts[family][key] for key in
                ("false_accepts", "misses", "other_mismatch")) == 0,
            "unresolved_contaminated_failure": bool(contaminated.get(family, {}).get("false_positive", 0)
                or contaminated.get(family, {}).get("missed_supported", 0)),
        }
        structural = all(
            value for key, value in checklist.items()
            if key not in {"unresolved_contaminated_failure", "cross_family_adversary"}
        ) and (checklist["cross_family_adversary"] or family == "quality_regulatory")
        if structural and not checklist["unresolved_contaminated_failure"]:
            status = "READY_FOR_FRESH_VALIDATION"
            reason = "Development checklist complete and no preserved known diagnostic defect."
        else:
            status = "NOT_READY"
            reason = "Missing checklist coverage or preserved contaminated false accepts/misses remain unresolved."
        readiness[family] = {"status": status, "reason": reason, "checklist": checklist}

    output = {
        "version": "evidence-engine-v0.3.6-development-coverage-v2",
        "status": "DEVELOPMENT_ONLY_NOT_VALIDATION",
        "synthetic_cases": len(cases),
        "synthetic_by_family": {family: dict(count) for family, count in counts.items()},
        "contaminated_diagnostics_by_family": contaminated,
        "severe_synthetic_failures": sum(count["false_accepts"] for count in counts.values()),
        "attribution_synthetic_failures": sum(1 for rows in family_rows.values() for row in rows
            if row["adversary"] == "attribution" and row["actual"] == "accept"),
        "provenance_completeness": {"complete": sum(row["provenance_complete"] for rows in family_rows.values() for row in rows),
                                    "total": len(cases)},
        "event_family_development_readiness": readiness,
        "fresh_gate_executed": False,
        "outcomes_accessed": False,
        "official_model2_readiness": "NOT READY",
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
