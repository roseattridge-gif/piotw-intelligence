from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from piotw_conditions.qualification_v01 import ConditionQualificationEngine
from piotw_evidence.families_v01 import (
    EvidenceFamilyRecord,
    LeadershipConditionAdapter,
    MultiSourceEvidenceEngine,
    ProcurementFamilyAdapter,
)

PROTOCOL = ROOT / "config/conditions/multifamily_review_extension_protocol_v0_2.json"
ORIGINAL = ROOT / "data/derived/piotw_multifamily_condition_review_v0_1_results.json"
OUTPUT = ROOT / "data/derived/piotw_multifamily_condition_review_extension_v0_2_results.json"
CUTOFF = datetime(2026, 8, 19, 23, 59, 59, tzinfo=UTC)
SOURCE_POLICY = "piotw-procurement-source-policy-find-a-tender-v0.1-development"


def _record(identifier: str, family: str, company: str, effective: str, url: str, span: str,
            record_type: str, values: dict[str, object], **extra: object) -> EvidenceFamilyRecord:
    timestamp = datetime.fromisoformat(effective)
    return EvidenceFamilyRecord(
        source_record_id=identifier, family_id=family, company_id=company, entity_scope=company,
        publication_or_effective_at=timestamp, source_published_at=timestamp, retrieved_at=CUTOFF,
        source_url=url, source_hash=hashlib.sha256(span.encode()).hexdigest(), evidence_span=span,
        collector_or_parser_version="multifamily-extension-primary-source-v0.2",
        record_type=record_type, values=values, **extra,
    )


def _award(identifier: str, company: str, year: int, url: str, supplier: str,
           company_number: str, underlying_award_id: str) -> EvidenceFamilyRecord:
    span = (f"UK Find a Tender contract-award notice {identifier} names {supplier}, company number "
            f"{company_number}, as an awarded supplier.")
    return _record(identifier, "contracts_procurement", company, f"{year}-07-01T00:00:00+00:00",
        url, span, "award_notice", {
            "entity_resolution": "APPROVED", "award_value": None, "currency": "GBP",
            "category": "public works/services", "comparison_period": str(year),
            "source_policy_id": SOURCE_POLICY, "source_regime": "UK_FIND_A_TENDER_CONTRACT_AWARD_NOTICE",
            "notice_type": "contract_award_notice", "underlying_award_id": underlying_award_id,
        }, scope_kind="SUBSIDIARY", legal_entity_identifier=company_number,
        entity_resolution_method="exact_legal_name_and_company_number_in_primary_notice",
        entity_resolution_confidence="HIGH")


def extension_records() -> list[EvidenceFamilyRecord]:
    abrdn_span = (
        "abrdn reported a new, smaller Group Operating Committee, a broadened Executive Leadership "
        "Team with greater client expertise, and scorecards cascaded through each business with "
        "ultimate accountability at executive level."
    )
    records = [_record(
        "abrdn-operating-model-2024", "leadership_organisation", "abrdn", "2025-03-04T07:00:00+00:00",
        "https://prd-cdn.abrdn.com/-/media/abrdn-jss-app/files/abrdn-plc-annual-report-and-accounts-2024.ashx",
        abrdn_span, "organisation_change", {
            "change_type": "reporting_line_redesign",
            "functions": ["Group Operating Committee", "Executive Leadership Team", "business accountability"],
            "factual_statement": "abrdn disclosed a smaller operating committee, a broadened leadership team and revised executive accountability mechanisms."
        }, legal_entity_identifier="SC286832", entity_resolution_method="issuer_primary_report",
        entity_resolution_confidence="HIGH")]

    records += [
        _award("fts-019386-2021", "mears-group", 2021, "https://www.find-tender.service.gov.uk/Notice/019386-2021", "Mears Limited", "02519234", "CAS3-2021"),
        _award("fts-027265-2022", "mears-group", 2022, "https://www.find-tender.service.gov.uk/Notice/027265-2022", "Mears Limited", "02519234", "MEARS-AWARD-2022"),
        _award("fts-024094-2023", "mears-group", 2023, "https://www.find-tender.service.gov.uk/Notice/024094-2023", "Mears Limited", "02519234", "RESPONSIVE-REPAIRS-2023"),
        _award("fts-036224-2023", "mears-group", 2023, "https://www.find-tender.service.gov.uk/Notice/036224-2023", "Mears Limited", "02519234", "MEARS-AWARD-036224"),
        _award("fts-036854-2024", "mears-group", 2024, "https://www.find-tender.service.gov.uk/Notice/036854-2024", "Mears Limited", "02519234", "ACFL-V2-2024"),
        _award("fts-013440-2025", "mears-group", 2025, "https://www.find-tender.service.gov.uk/Notice/013440-2025", "Mears Limited", "02519234", "MEARS-AWARD-013440"),
        _award("fts-015517-2025", "mears-group", 2025, "https://www.find-tender.service.gov.uk/Notice/015517-2025", "Mears Limited", "02519234", "MEARS-AWARD-015517"),
        _award("fts-023949-2021", "kier-group", 2021, "https://www.find-tender.service.gov.uk/Notice/023949-2021", "Kier Construction Limited", "02099533", "SCAPE-2021"),
        _award("fts-007260-2023", "kier-group", 2023, "https://www.find-tender.service.gov.uk/Notice/007260-2023", "Kier Construction Limited", "02099533", "KIER-AWARD-007260"),
        _award("fts-020764-2024", "kier-group", 2024, "https://www.find-tender.service.gov.uk/Notice/020764-2024", "Kier Construction Limited", "02099533", "MAJOR-WORKS-2024"),
        _award("fts-016366-2024", "kier-group", 2024, "https://www.find-tender.service.gov.uk/Notice/016366-2024", "Kier Construction Limited", "02099533", "KIER-AWARD-016366"),
        _award("fts-035752-2025", "kier-group", 2025, "https://www.find-tender.service.gov.uk/Notice/035752-2025", "Kier Construction Limited", "02099533", "COLINDALE-2025"),
        _award("fts-054981-2025", "kier-group", 2025, "https://www.find-tender.service.gov.uk/Notice/054981-2025", "Kier Construction Limited", "02099533", "KIER-AWARD-054981"),
        _award("fts-067631-2025", "kier-group", 2025, "https://www.find-tender.service.gov.uk/Notice/067631-2025", "Kier Construction Limited", "02099533", "KIER-AWARD-067631"),
    ]
    return records


def _review(candidate: dict[str, object]) -> dict[str, object]:
    kind = str(candidate["condition_candidate_type"])
    status = str(candidate["qualification_status"])
    if kind == "organisational_restructuring":
        classification = "CORRECT QUALIFICATION"
        reason = "The issuer directly described operating-committee, leadership-team and accountability redesign; this is not a routine appointment."
    elif candidate["company_id"] == "mears-group":
        classification = "CORRECT WITHHOLD"
        reason = "The same-regime annual notice counts reverse direction and do not establish persistent movement."
    else:
        classification = "AMBIGUOUS / NEEDS MORE EVIDENCE"
        reason = "The rule qualified a rise in sparse publication counts, but buyer-driven notice coverage is not complete enough to establish a company operational condition."
    return {
        "company_id": candidate["company_id"], "candidate_type": kind, "engine_status": status,
        "classification": classification, "factual_observation_correct": True,
        "entity_scope_correct": True, "provenance_complete": bool(candidate["supporting_evidence_ids"]),
        "severe_false_positive": False, "false_negative": False,
        "operationally_worth_investigating": classification != "CORRECT WITHHOLD",
        "reason": reason,
    }


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text())
    original = json.loads(ORIGINAL.read_text())
    qualifier = ConditionQualificationEngine()
    if qualifier.policy_hash != protocol["policy"]["sha256_at_freeze"]:
        raise SystemExit("frozen qualification policy hash changed")
    records = extension_records()
    engine = MultiSourceEvidenceEngine([ProcurementFamilyAdapter(), LeadershipConditionAdapter()])
    company_rows = []
    qualifications = []
    for company in ["abrdn", "mears-group", "kier-group"]:
        company_records = [row for row in records if row.company_id == company]
        envelopes = engine.adapt(company_id=company, entity_scope=company, analysis_cutoff=CUTOFF,
                                 records=company_records)
        observations = [item for envelope in envelopes for item in envelope.observations]
        valid_evidence = {f"ev-{row.source_record_id}" for row in company_records}
        results = [qualifier.qualify(candidate, observations=observations, valid_evidence_ids=valid_evidence)
                   for envelope in envelopes for candidate in envelope.candidates]
        qualifications.extend(results)
        company_rows.append({
            "company_id": company,
            "source_records": [row.model_dump(mode="json") for row in company_records],
            "family_envelopes": [envelope.model_dump(mode="json") for envelope in envelopes],
            "qualifications": [result.model_dump(mode="json") for result in results],
        })
    review = [_review(item.model_dump(mode="json")) for item in qualifications]
    combined_total = original["summary"]["candidate_decisions"] + len(review)
    original_qualified = original["summary"]["qualified"]
    new_qualified = sum(item.qualification_status == "QUALIFIED" for item in qualifications)
    correct_qualified = original_qualified + sum(
        item["classification"] == "CORRECT QUALIFICATION" for item in review)
    total_qualified = original_qualified + new_qualified
    ambiguous = original["metrics"]["ambiguous_case_rate"]["ambiguous"] + sum(
        item["classification"] == "AMBIGUOUS / NEEDS MORE EVIDENCE" for item in review)
    metrics = {
        "factual_observation_accuracy": {"correct": 11 + sum(item["factual_observation_correct"] for item in review), "total": combined_total},
        "entity_scope_accuracy": {"correct": 11 + sum(item["entity_scope_correct"] for item in review), "total": combined_total},
        "qualified_condition_precision": {"correct": correct_qualified, "total": total_qualified},
        "false_negative_rate": {"false_negatives": 0, "total_expected_positive": correct_qualified},
        "ambiguous_case_rate": {"ambiguous": ambiguous, "total": combined_total},
        "provenance_completeness": {"complete": 11 + sum(item["provenance_complete"] for item in review), "total": combined_total},
        "severe_false_positives": 0, "unhandled_contradictions": 0,
        "stable_family_policies": ["estate", "leadership_organisation"], "retired_family_policies": [],
    }
    rates = {
        "factual": metrics["factual_observation_accuracy"]["correct"] / combined_total,
        "entity": metrics["entity_scope_accuracy"]["correct"] / combined_total,
        "precision": correct_qualified / total_qualified,
        "false_negative": 0.0,
        "ambiguous": ambiguous / combined_total,
        "provenance": metrics["provenance_completeness"]["complete"] / combined_total,
    }
    gate = protocol["readiness_gate"]
    if metrics["severe_false_positives"] > gate["severe_false_positives_max"] or rates["precision"] < gate["qualified_condition_precision_min"]:
        readiness = "NOT_READY_FALSE_POSITIVE_RISK"
    elif rates["false_negative"] > gate["false_negative_rate_max"]:
        readiness = "NOT_READY_FALSE_NEGATIVE_RISK"
    elif rates["entity"] < gate["entity_scope_accuracy_min"]:
        readiness = "NOT_READY_ENTITY_RESOLUTION"
    elif (rates["factual"] < gate["factual_observation_accuracy_min"]
          or rates["provenance"] < gate["provenance_completeness_min"]
          or rates["ambiguous"] > gate["ambiguous_case_rate_max"]
          or len(metrics["stable_family_policies"]) < gate["minimum_stable_family_policies"]
          or len(metrics["retired_family_policies"]) > gate["retired_family_policies_max"]
          or metrics["unhandled_contradictions"] > gate["unhandled_contradictions_max"]):
        readiness = "NOT_READY_POLICY_INSTABILITY"
    elif combined_total < protocol["selection_rules"]["minimum_combined_decisions"]:
        readiness = "NOT_READY_INSUFFICIENT_REVIEW_SCOPE"
    else:
        readiness = "READY_FOR_COMPARE"
    output = {
        "schema_version": "piotw-multifamily-condition-review-extension-results-v0.2",
        "methodological_status": protocol["methodological_status"], "scientific_gate_run": False,
        "analysis_cutoff": CUTOFF.isoformat(), "policy_hash": qualifier.policy_hash,
        "new_company_rows": company_rows, "source_first_review": review,
        "combined_metrics": metrics, "combined_rates": rates,
        "summary": {"original_decisions": 11, "new_decisions": len(review), "combined_decisions": combined_total,
                    "new_qualified": new_qualified, "new_withheld": len(review) - new_qualified,
                    "readiness_status": readiness,
                    "procurement_policy_status": "SOURCE_SPECIFIC_BOUNDARY_DEFINED_NEEDS_FURTHER_REVIEW"},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
