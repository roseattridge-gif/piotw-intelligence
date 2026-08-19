from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_3_4.semantic import SemanticCandidate
from evidence_engine_v0_3_6.families import verify_candidate

DATA = ROOT / "data/evidence_engine_v0_3_6"
DERIVED = ROOT / "data/derived"
RESULTS = DERIVED / "evidence_engine_v0_3_6_fresh_validation_results.json"
DECOMPOSITION = DERIVED / "evidence_engine_v0_3_6_failure_decomposition.csv"
SUMMARY = DERIVED / "evidence_engine_v0_3_6_stage_failure_analysis.json"
HUMAN_SLICE = DERIVED / "evidence_engine_v0_3_6_human_review_slice.csv"

SHARED_SAFETY_REASONS = {
    "missing_exact_provenance",
    "heading_only",
    "accounting_table_only",
    "wrong_entity",
    "negated_event",
    "hypothetical_only",
    "historical_only",
}


def load() -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
    candidates = {
        row["candidate_id"]: row
        for row in map(json.loads, (DATA / "fresh_frozen_candidates.jsonl").read_text().splitlines())
    }
    with (DATA / "fresh_ai_source_first_labels.csv").open(newline="") as stream:
        labels = {row["candidate_id"]: row for row in csv.DictReader(stream)}
    results = json.loads(RESULTS.read_text())
    final = {row["candidate_id"]: row for row in results["final_rows"]}
    return list(candidates.values()), labels, final


def local_decision(candidate: dict) -> dict[str, str]:
    semantic = SemanticCandidate(
        **{
            key: candidate[key]
            for key in (
                "target_company",
                "candidate_event_type",
                "exact_candidate_span",
                "context",
                "heading",
                "publication_date",
                "deterministic_metadata",
            )
        }
    )
    decision = verify_candidate(semantic)
    return {"family": decision.family, "disposition": decision.disposition, "reason": decision.reason}


def failure_stage(label: dict, local: dict, result: dict | None) -> tuple[str, str]:
    expected = label["independent_disposition"]
    final = result["final_disposition"] if result else "provider_incomplete"
    if expected == "supported" and final != "accept":
        if result is None:
            return "provider_execution", "provider_incomplete"
        if local["disposition"] != "accept":
            if local["reason"] in SHARED_SAFETY_REASONS:
                return "shared_safety_rules", local["reason"]
            return "family_contract", local["reason"]
        return "semantic_adjudication", result["parsed_decision"]["reason_code"]
    if expected != "supported" and final == "accept":
        if label["event_timing_status"] == "historical":
            return "joint_contract_and_semantic", "historical_event_accepted"
        if label["polarity"] not in {"", "neutral", "unclear"} and label["event_type"] == "growth_language":
            return "candidate_identity_and_semantic", "growth_identity_or_polarity_overreach"
        return "joint_contract_and_semantic", "unsupported_candidate_accepted"
    if final == "ambiguous":
        return "ambiguity_handling", local["reason"]
    return "correct_or_not_in_failure_scope", "none"


def ambiguity_risk(label: dict, local: dict, result: dict | None) -> tuple[str, str]:
    reasons: list[str] = []
    if label["independent_disposition"] == "ambiguous":
        reasons.append("source_first_label_is_ambiguous")
    if label["independent_disposition"] == "supported" and label["event_timing_status"] in {
        "historical",
        "hypothetical",
    }:
        reasons.append("supported_label_conflicts_with_accepted_time")
    if label["independent_disposition"] == "supported" and label["hypothetical_or_historical"] == "true":
        reasons.append("supported_label_has_historical_or_hypothetical_flag")
    if result and result["provider_disposition"] != local["disposition"]:
        reasons.append("deterministic_and_semantic_disagree")
    if label["event_type"] == "growth_language" and label["polarity"] == "negative":
        reasons.append("candidate_event_identity_conflicts_with_polarity")
    return ("high" if reasons else "low", ";".join(reasons))


def human_question(label: dict, root_cause: str) -> str:
    if "historical" in root_cause or label["event_timing_status"] == "historical":
        return "Relative to the report publication date, is this an in-scope current/ongoing event, or historical background only?"
    if label["event_type"] == "growth_language":
        return "What factual metric changed, in which direction, and does it evidence demand rather than an assumption, price, production or accounting movement?"
    if label["independent_disposition"] == "ambiguous":
        return "Does this exact source context establish a target-company factual observation; if so, what subject, action/state, timing and polarity are supported?"
    return "Does the source directly support the proposed factual event under the written contract, and which contract element is decisive?"


def main() -> None:
    candidates, labels, final = load()
    rows = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        label = labels[candidate_id]
        result = final.get(candidate_id)
        local = local_decision(candidate)
        stage, root = failure_stage(label, local, result)
        risk, risk_reasons = ambiguity_risk(label, local, result)
        scopes = []
        final_disposition = result["final_disposition"] if result else "provider_incomplete"
        if label["independent_disposition"] == "supported" and final_disposition != "accept":
            scopes.append("missed_supported_event")
        if label["independent_disposition"] != "supported" and final_disposition == "accept":
            scopes.append("false_positive")
        if final_disposition == "ambiguous":
            scopes.append("ambiguous_decision")
        if not scopes:
            continue
        provider_decision = result["provider_disposition"] if result else "provider_incomplete"
        provider_reason = result["parsed_decision"]["reason_code"] if result else "provider_incomplete"
        row = {
            "candidate_id": candidate_id,
            "company": candidate["target_company"],
            "document_id": candidate["document_id"],
            "event_family": label["event_family"],
            "candidate_event_type": candidate["candidate_event_type"],
            "failure_scope": ";".join(scopes),
            "source_span": candidate["exact_candidate_span"],
            "surrounding_context": candidate["context"],
            "source_first_expected_label": label["independent_disposition"],
            "candidate_generated": "true",
            "candidate_family": local["family"],
            "family_routing_wrong": str(local["family"] != label["event_family"]).lower(),
            "candidate_generation_decision": "surfaced_by_fresh_broad_source_locator_v1",
            "family_contract_decision": local["disposition"],
            "family_contract_reason": local["reason"],
            "semantic_adjudication_decision": provider_decision,
            "semantic_reason": provider_reason,
            "final_decision": final_disposition,
            "timing_label": label["event_timing_status"],
            "polarity_label": label["polarity"],
            "third_party_label": label["third_party_attribution"],
            "label_ambiguity_risk": risk,
            "label_ambiguity_reasons": risk_reasons,
            "primary_failure_stage": stage,
            "root_cause_category": root,
            "review_notes": label["review_notes"],
        }
        rows.append(row)

    DECOMPOSITION.parent.mkdir(parents=True, exist_ok=True)
    with DECOMPOSITION.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    missed = [row for row in rows if "missed_supported_event" in row["failure_scope"]]
    false_positive = [row for row in rows if "false_positive" in row["failure_scope"]]
    ambiguous = [row for row in rows if "ambiguous_decision" in row["failure_scope"]]
    miss_stages = Counter(row["primary_failure_stage"] for row in missed)
    fp_stages = Counter(row["primary_failure_stage"] for row in false_positive)
    label_rows = list(labels.values())
    summary = {
        "scientific_status": "SPENT_0_3_6_CORPUS_DEVELOPMENT_ONLY",
        "candidate_generation_recall_measurable": False,
        "candidate_generation_recall_caveat": "All frozen labels were selected from surfaced candidates; unsurfaced source facts were not independently annotated.",
        "failure_rows": len(rows),
        "missed_supported_events": len(missed),
        "false_positives": len(false_positive),
        "ambiguous_decisions": len(ambiguous),
        "miss_stage_counts": dict(miss_stages),
        "miss_stage_rates": {key: value / len(missed) for key, value in miss_stages.items()},
        "false_positive_stage_counts": dict(fp_stages),
        "false_positive_stage_rates": {key: value / len(false_positive) for key, value in fp_stages.items()},
        "supported_label_timing": dict(Counter(
            row["event_timing_status"] for row in label_rows if row["independent_disposition"] == "supported"
        )),
        "supported_with_historical_or_hypothetical_flag": sum(
            row["independent_disposition"] == "supported" and row["hypothetical_or_historical"] == "true"
            for row in label_rows
        ),
        "family_routing_mismatches_in_failure_rows": sum(row["family_routing_wrong"] == "true" for row in rows),
        "outcomes_accessed": False,
        "model2_trained": False,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    # Highest-value review slice: every false positive, then contract/label conflicts,
    # then deterministic-versus-semantic disagreements, balanced across families.
    def priority(row: dict) -> tuple[int, int, str]:
        scope = row["failure_scope"]
        score = 0
        if "false_positive" in scope:
            score += 100
        if "supported_label_conflicts_with_accepted_time" in row["label_ambiguity_reasons"]:
            score += 60
        if "deterministic_and_semantic_disagree" in row["label_ambiguity_reasons"]:
            score += 40
        if "ambiguous_decision" in scope:
            score += 20
        return (-score, -len(row["source_span"]), row["candidate_id"])

    selected_rows: list[dict] = []
    selected_ids: set[str] = set()
    family_counts: Counter[str] = Counter()
    ranked = sorted(rows, key=priority)
    for family in sorted({row["event_family"] for row in rows}):
        for row in [item for item in ranked if item["event_family"] == family][:4]:
            selected_rows.append(row)
            selected_ids.add(row["candidate_id"])
            family_counts[family] += 1
    for row in ranked:
        if len(selected_rows) >= 36:
            break
        if row["candidate_id"] in selected_ids or family_counts[row["event_family"]] >= 6:
            continue
        selected_rows.append(row)
        selected_ids.add(row["candidate_id"])
        family_counts[row["event_family"]] += 1

    selected: list[dict] = []
    for row in selected_rows:
        selected.append({
            "review_order": len(selected) + 1,
            "candidate_id": row["candidate_id"],
            "company": row["company"],
            "document_id": row["document_id"],
            "event_family": row["event_family"],
            "candidate_event_type": row["candidate_event_type"],
            "source_span": row["source_span"],
            "surrounding_context": row["surrounding_context"],
            "why_selected": row["label_ambiguity_reasons"] or row["root_cause_category"],
            "reviewer_question": human_question(labels[row["candidate_id"]], row["root_cause_category"]),
            "required_expertise": "qualified financial-reporting reviewer with operational-disclosure experience",
            "adjudication_rule": "two blinded reviewers; disagreements resolved by a third reviewer against the frozen written contract",
        })
    with HUMAN_SLICE.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)
    print(json.dumps({**summary, "human_review_rows": len(selected)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
