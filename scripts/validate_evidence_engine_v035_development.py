from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_3_4.evidence_pointer import (
    build_evidence_pointer_mapping,
    evidence_pointer_id,
    resolve_evidence_pointer,
)
from evidence_engine_v0_3_4.semantic import SemanticCandidate
from evidence_engine_v0_3_5.semantic import DeterministicSemanticVerifierV035

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    fixture_path = ROOT / "data/evidence_engine_v0_3_5/semantic_regression_cases.yaml"
    rows = yaml.safe_load(fixture_path.read_text())["cases"]
    verifier = DeterministicSemanticVerifierV035()
    results = []
    severe = attribution = provenance_failures = 0
    for row in rows:
        candidate = SemanticCandidate(row["company"], row["event_type"], row["span"], row["span"],
            "development regression", "2026-08-17", {"subject_type": row["subject_type"],
            "entity_scope": "group", "factual_status": "actual", "event_status": "current", "allowed_remaps": []})
        decision = verifier.verify(candidate)
        pointer = build_evidence_pointer_mapping(candidate, f"dev-{row['id']}")
        if decision.decision == "accept":
            try:
                resolve_evidence_pointer(evidence_pointer_id(pointer), pointer, candidate, decision="accept")
            except ValueError:
                provenance_failures += 1
        passed = decision.decision == row["expected"]
        if not passed and row["expected"] == "reject" and decision.decision == "accept":
            severe += row["failure_class"] in {"legal_reference", "third_party_attribution"}
            attribution += row["failure_class"] == "third_party_attribution"
        results.append({"case_id": row["id"], "expected": row["expected"], "actual": decision.decision,
            "reason": decision.reason_code, "passed": passed})
    protected = len(verify_frozen_isolation(ROOT))
    passed_count = sum(row["passed"] for row in results)
    gate_pass = passed_count == len(results) and severe == attribution == provenance_failures == 0 and protected == 12
    payload = {"engine_version": "0.3.5-development", "scientific_validation": False,
        "status": "DEVELOPMENT_GATE_PASSED" if gate_pass else "DEVELOPMENT_GATE_FAILED",
        "regressions": {"passed": passed_count, "total": len(results)},
        "severe_false_positives": severe, "attribution_errors": attribution,
        "provenance": {"complete": len(results) - provenance_failures, "total": len(results)},
        "protected_artifacts": protected, "cases": results,
        "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest()}
    target = ROOT / "data/derived/evidence_engine_v0_3_5_development_results.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2))
    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

