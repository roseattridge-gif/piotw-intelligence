from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "config/conditions/multifamily_review_extension_protocol_v0_2.json"
RESULTS = ROOT / "data/derived/piotw_multifamily_condition_review_extension_v0_2_results.json"


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text())
    result = json.loads(RESULTS.read_text())
    gate = protocol["readiness_gate"]
    rates = result["combined_rates"]
    metrics = result["combined_metrics"]
    if (metrics["severe_false_positives"] > gate["severe_false_positives_max"]
            or rates["precision"] < gate["qualified_condition_precision_min"]):
        status = "NOT_READY_FALSE_POSITIVE_RISK"
    elif rates["false_negative"] > gate["false_negative_rate_max"]:
        status = "NOT_READY_FALSE_NEGATIVE_RISK"
    elif rates["entity"] < gate["entity_scope_accuracy_min"]:
        status = "NOT_READY_ENTITY_RESOLUTION"
    elif (rates["factual"] < gate["factual_observation_accuracy_min"]
          or rates["provenance"] < gate["provenance_completeness_min"]
          or rates["ambiguous"] > gate["ambiguous_case_rate_max"]
          or len(metrics["stable_family_policies"]) < gate["minimum_stable_family_policies"]
          or len(metrics["retired_family_policies"]) > gate["retired_family_policies_max"]
          or metrics["unhandled_contradictions"] > gate["unhandled_contradictions_max"]):
        status = "NOT_READY_POLICY_INSTABILITY"
    elif result["summary"]["combined_decisions"] < protocol["selection_rules"]["minimum_combined_decisions"]:
        status = "NOT_READY_INSUFFICIENT_REVIEW_SCOPE"
    else:
        status = "READY_FOR_COMPARE"
    previous = result["summary"]["readiness_status"]
    result["summary"]["readiness_status"] = status
    result["gate_application_audit"] = {
        "condition_engine_rerun": False,
        "previous_reported_status": previous,
        "corrected_status": status,
        "correction_reason": "The initial reporting code omitted the frozen ambiguous-case-rate check; preserved engine outputs were not rerun or changed.",
        "ambiguity_observed": rates["ambiguous"],
        "ambiguity_max": gate["ambiguous_case_rate_max"],
    }
    RESULTS.write_text(json.dumps(result, indent=2) + "\n")
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
