from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.semantic import SemanticCandidate
from evidence_engine_v0_3_6.families import route_family, verify_candidate

LABELS = ROOT / "data/evidence_engine_v0_3_5/fresh_ai_source_first_labels.csv"
OUT_CSV = ROOT / "data/derived/evidence_engine_v0_3_6_known_failure_register.csv"
OUT_JSON = ROOT / "data/derived/evidence_engine_v0_3_6_final_hardening_results.json"

FALSE_ACCEPTS_BEFORE = {
    "d1041434880d20ce98d35969",
    "814f0960a7337764a01bdda8",
    "edadea641c2b31fae28945c3",
    "df2482ec0921b8e6a1a7b1f6",
    "3924161d7e2a60d592dddc9d",
}
MISSES_BEFORE = {
    "7b2cd12bf72194a3eaad5aff",
    "bd1a14e916f23c3116da4f70",
    "a3a2423f647318d0ba80ef94",
    "295634ff4162bff6ad74ef07",
    "6172fda86b93901d4372618d",
    "050417badd1c5f0623a646fe",
    "cc6d86909c10b087c96d4ebf",
    "494538ef771bb0b93e81f33d",
    "a5380b92f5356c6cfb7ccd17",
    "a3e3c0cf90876614616ee8ac",
    "1f06297fff3fd807f39b9581",
    "ebb5147404167026f7c424da",
    "0550812c3578675dc111f232",
    "fd9c61ae4b342db3e928a8cf",
    "f7b14e22fe454f9a67133d3d",
}


def _diagnosis(row: dict[str, str]) -> tuple[str, str, str, str]:
    span = row["source_span"].lower()
    event = row["event_type"]
    if row["candidate_id"] in FALSE_ACCEPTS_BEFORE:
        if "past" in span:
            return ("historical_context", "shared", "Reject completed or past-only conditions without a current anchor.", "low")
        if "could" in span or "failure to" in span:
            return ("hypothetical_risk", "shared", "Reject conditional risk language without realised impact.", "low")
        if "backlog" in span:
            return ("metric_description", "family", "Require observed backlog movement, not a metric description.", "low")
        return ("wrong_growth_object", "family", "Constrain growth to demand, revenue, sales, orders, backlog or volume.", "low")
    if event in {"restructuring", "cost_reduction"} and ("accrual" in span or "liability" in span):
        return ("active_plan_accounting_evidence", "family+source", "Accept only dated active-plan balances or payment/action evidence; keep definitions ambiguous.", "medium")
    if event in {"restructuring", "cost_reduction"}:
        return ("indirect_intervention_language", "family", "Recognise implemented structural action while rejecting generic capability language.", "medium")
    if event in {"site_closure", "capacity_reduction"}:
        return ("indirect_site_action", "family", "Recognise closures tied to current charges/actions without treating provisions alone as events.", "medium")
    if event in {"workforce_reduction", "redundancy"}:
        return ("implemented_workforce_action", "family", "Recognise initiated or ongoing reductions with target attribution.", "low")
    if event in {"transformation", "leadership_change"}:
        return ("ongoing_programme_execution", "family", "Recognise continuing multi-year execution with deployed action, not aspiration alone.", "medium")
    return ("realised_supply_condition", "family+shared", "Recognise current issuer impact and mitigation/persistence while rejecting third-party, hypothetical and historical-only text.", "medium")


def main() -> None:
    labels = {row["candidate_id"]: row for row in csv.DictReader(LABELS.open())}
    known_ids = FALSE_ACCEPTS_BEFORE | MISSES_BEFORE
    records: list[dict[str, str]] = []
    unresolved: list[str] = []
    for index, candidate_id in enumerate(sorted(known_ids), start=1):
        row = labels[candidate_id]
        family = route_family(row["event_type"])
        subject = "third_party" if row["third_party_attribution"].lower() == "true" else "target_company"
        candidate = SemanticCandidate(
            row["target_company"], row["event_type"], row["source_span"], row["source_span"],
            None, None, {"subject_type": subject},
        )
        decision = verify_candidate(candidate)
        expected = "accept" if row["independent_disposition"] == "supported" else "reject"
        failure_type, logic, proposed_fix, risk = _diagnosis(row)
        post_resolved = decision.disposition == expected
        if not post_resolved:
            unresolved.append(candidate_id)
        records.append({
            "case_id": candidate_id,
            "family": family or "unrouted",
            "candidate_event_type": row["event_type"],
            "expected_classification": expected,
            "pre_hardening_actual": "accept" if candidate_id in FALSE_ACCEPTS_BEFORE else "ambiguous",
            "post_hardening_actual": decision.disposition,
            "post_hardening_reason": decision.reason,
            "evidence_span": row["source_span"],
            "surrounding_context": row["source_span"],
            "target_entity": row["target_company"],
            "entity_scope": subject,
            "polarity": "negative" if any(word in row["source_span"].lower() for word in ("decline", "decrease", "shortage", "closure", "reduction")) else "neutral_or_positive",
            "temporal_status": row["event_timing_status"],
            "failure_type": "false_accept" if candidate_id in FALSE_ACCEPTS_BEFORE else "missed_supported",
            "root_cause": failure_type,
            "deterministic_shared_logic_relevant": str(logic in {"shared", "family+shared"}).lower(),
            "family_specific_logic_relevant": str("family" in logic).lower(),
            "source_extraction_relevant": str("source" in logic).lower(),
            "proposed_general_fix": proposed_fix,
            "overfitting_risk": risk,
            "regression_test_id": f"v036-known-{index:02d}",
            "resolved": str(post_resolved).lower(),
            "formal_gold": "false",
            "contamination_status": "DEVELOPMENT_CONTAMINATED_NOT_VALIDATION",
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    output = {
        "version": "evidence-engine-v0.3.6-final-development-hardening-v1",
        "status": "DEVELOPMENT_ONLY_NOT_VALIDATION",
        "known_failure_cases": len(records),
        "known_false_accepts_before": len(FALSE_ACCEPTS_BEFORE),
        "known_misses_before": len(MISSES_BEFORE),
        "known_failures_resolved": sum(row["resolved"] == "true" for row in records),
        "known_failures_remaining": len(unresolved),
        "unresolved_case_ids": unresolved,
        "failure_register_sha256": hashlib.sha256(OUT_CSV.read_bytes()).hexdigest(),
        "fresh_gate_executed": False,
        "fresh_corpus_constructed": False,
        "outcomes_accessed": False,
        "model2_trained": False,
        "official_model2_readiness": "NOT READY",
        "fresh_gate_authorisation_status": (
            "EVIDENCE_ENGINE_0_3_6_READY_FOR_FRESH_GATE_AUTHORISATION"
            if not unresolved else "EVIDENCE_ENGINE_0_3_6_NOT_READY_FOR_FRESH_GATE_AUTHORISATION"
        ),
    }
    OUT_JSON.write_text(json.dumps(output, indent=2) + "\n")
    print(OUT_JSON)


if __name__ == "__main__":
    main()
