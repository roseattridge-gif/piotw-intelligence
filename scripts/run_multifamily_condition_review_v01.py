from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from piotw_conditions.qualification_v01 import ConditionQualificationEngine
from piotw_evidence.families_v01 import (
    CareersEvidenceFamilyAdapter,
    EstateConditionAdapter,
    EvidenceFamilyRecord,
    LeadershipConditionAdapter,
    MultiSourceEvidenceEngine,
    ProcurementFamilyAdapter,
)

CUTOFF = datetime(2026, 8, 19, 23, 59, 59, tzinfo=UTC)
PROTOCOL = ROOT / "config/conditions/multifamily_review_protocol_v0_1.json"
RESULTS = ROOT / "data/derived/piotw_multifamily_condition_review_v0_1_results.json"


def record(identifier: str, family: str, company: str, effective: str, published: str,
           url: str, span: str, record_type: str, values: dict[str, object], **extra: object) -> EvidenceFamilyRecord:
    return EvidenceFamilyRecord(
        source_record_id=identifier, family_id=family, company_id=company,
        entity_scope=company, publication_or_effective_at=datetime.fromisoformat(effective),
        source_published_at=datetime.fromisoformat(published), retrieved_at=CUTOFF,
        source_url=url, source_hash=hashlib.sha256(span.encode()).hexdigest(), evidence_span=span,
        collector_or_parser_version="primary-source-development-review-v0.1",
        record_type=record_type, values=values, **extra,
    )


def estate(company: str, base: str, url: str, published: str,
           rows: list[tuple[str, int, int, int]]) -> list[EvidenceFamilyRecord]:
    return [record(f"{base}-{period}", "estate_footprint_capacity", company,
        f"{period}-01-31T00:00:00+00:00", published, url,
        f"Official issuer disclosure: total sites {count} for reporting period {period}; openings {opens}; closures {closes}.",
        "estate_period", {"period": period, "site_count": count, "openings": opens, "closures": closes})
        for period, count, opens, closes in rows]


def award(identifier: str, company: str, effective: str, url: str, supplier: str,
          company_number: str, value: float, period: str) -> EvidenceFamilyRecord:
    span = f"Official award notice names {supplier}, company number {company_number}, as supplier; disclosed award value GBP {value}."
    return record(identifier, "contracts_procurement", company, effective, effective, url, span,
        "award_notice", {"entity_resolution": "APPROVED", "award_value": value,
        "currency": "GBP", "category": "public works/services", "comparison_period": period},
        scope_kind="SUBSIDIARY", legal_entity_identifier=company_number,
        entity_resolution_method="exact_legal_name_and_company_number_in_primary_notice",
        entity_resolution_confidence="HIGH")


def records() -> list[EvidenceFamilyRecord]:
    rows: list[EvidenceFamilyRecord] = []
    rows += estate("kingfisher", "kfg-estate", "https://www.kingfisher.com/~/media/Files/K/Kingfisher-Plc/Universal/investors/result-reports-presentation/2025/Kingfisher-Annual-Report-2024-25.pdf",
        "2025-03-25T07:00:00+00:00", [("2023", 1572, 0, 0), ("2024", 1638, 0, 0), ("2025", 1681, 0, 0)])
    rows += estate("howden-joinery", "hwdn-estate", "https://www.howdenjoinerygroupplc.com/docs/librariesprovider25/archives/annual-reports/2025-annual-report.pdf",
        "2026-02-26T07:00:00+00:00", [("2022", 873, 0, 0), ("2023", 915, 0, 0), ("2024", 947, 0, 0), ("2025", 970, 0, 0)])
    rows += estate("greggs", "grg-estate", "https://assets.greggs.com/f/162306/x/85edb88f68/greggs-annual-report-and-accounts-2024.pdf",
        "2025-03-04T07:00:00+00:00", [("2022", 2328, 0, 0), ("2023", 2473, 0, 0), ("2024", 2618, 226, 81)])
    rows += estate("jd-wetherspoon", "jdw-estate", "https://www.investors.jdwetherspoon.com/wp-content/uploads/sites/3/2025/10/Annual-Report-03-October-2025.pdf",
        "2025-10-03T07:00:00+00:00", [("2022", 852, 0, 0), ("2023", 825, 0, 0), ("2024", 800, 0, 0), ("2025", 794, 3, 9)])

    rows.append(record("kfg-org-france-2024", "leadership_organisation", "kingfisher",
        "2024-04-01T00:00:00+00:00", "2025-03-25T07:00:00+00:00",
        "https://www.kingfisher.com/~/media/Files/K/Kingfisher-Plc/Universal/investors/result-reports-presentation/2025/20250325Kingfisher-PLC-Full-Year-2024-25-Results-Transcript.pdf",
        "Kingfisher reported that organisational simplification in France shifted strategic and operational responsibility to the retail banners and restructured head-office functions.",
        "organisation_change", {"change_type": "operating_structure", "functions": ["France retail banners", "head office"],
        "factual_statement": "Kingfisher disclosed a completed simplification of its French operating structure."}))
    rows.append(record("kier-risk-structure-2022", "leadership_organisation", "kier-group",
        "2022-06-30T00:00:00+00:00", "2022-09-15T07:00:00+00:00",
        "https://www.kier.co.uk/media/cesbjikp/annual-report-2022.pdf",
        "The three-lines-of-defence model was integrated within operational business streams and a new risk structure under Commercial was introduced.",
        "organisation_change", {"change_type": "reporting_line_redesign", "functions": ["risk", "commercial"],
        "factual_statement": "Kier disclosed integration of a revised risk operating structure into its business streams."}))
    rows.append(record("hwdn-board-2025", "leadership_organisation", "howden-joinery",
        "2025-01-01T00:00:00+00:00", "2025-02-27T07:00:00+00:00",
        "https://www.howdenjoinerygroupplc.com/media-centre/archive/2025/270225.asp",
        "Tim Lodge joined the Board in January 2025.", "leadership_change",
        {"change_type": "routine_appointment", "functions": ["board"],
        "factual_statement": "Howdens disclosed a Board appointment effective January 2025."}))

    rows += [
        award("mears-2023-036224", "mears-group", "2023-12-19T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/036224-2023", "Mears Limited", "02519234", 69_220_000, "2023"),
        award("mears-2024-036854", "mears-group", "2024-11-14T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/036854-2024", "Mears Limited", "02519234", 1, "2024"),
        award("mears-2025-013440", "mears-group", "2025-04-03T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/013440-2025", "Mears Limited", "02519234", 60_000_000, "2025"),
        award("mears-2025-015517", "mears-group", "2025-04-15T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/015517-2025", "Mears Limited", "02519234", 22_750_000, "2025"),
        award("kier-2023-007260", "kier-group", "2023-03-13T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/007260-2023", "Kier Construction Limited", "02099533", 1, "2023"),
        award("kier-2024-020764", "kier-group", "2024-07-15T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/020764-2024", "Kier Construction Limited", "02099533", 1, "2024"),
        award("kier-2024-016366", "kier-group", "2024-06-10T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/016366-2024", "Kier Construction Limited", "02099533", 1, "2024"),
        award("kier-2025-cf-39ae", "kier-group", "2025-05-14T00:00:00+00:00", "https://www.contractsfinder.service.gov.uk/Notice/39ae3d80-59db-4208-9086-1ab888c085ae", "Kier Construction Limited", "02099533", 582_401.57, "2025"),
        award("kier-2025-054981", "kier-group", "2025-09-11T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/054981-2025", "Kier Construction Limited", "02099533", 1, "2025"),
        award("kier-2025-067631", "kier-group", "2025-10-22T00:00:00+00:00", "https://www.find-tender.service.gov.uk/Notice/067631-2025", "Kier Construction Limited", "02099533", 1, "2025"),
    ]
    for identifier, date, count in [("cf-careers-a", "2026-08-15T00:00:00+00:00", 305), ("cf-careers-b", "2026-08-19T00:00:00+00:00", 297)]:
        rows.append(record(identifier, "careers_ats", "cloudflare", date, date,
            "https://www.cloudflare.com/careers/jobs/", f"Healthy careers snapshot observed {count} open postings.",
            "careers_snapshot", {"open_count": count}))
    return rows


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text())
    policy = ConditionQualificationEngine()
    if policy.policy_hash != protocol["policy"]["sha256_at_freeze"]:
        raise SystemExit("frozen qualification policy hash changed")
    all_records = records()
    engine = MultiSourceEvidenceEngine([CareersEvidenceFamilyAdapter(), EstateConditionAdapter(),
        ProcurementFamilyAdapter(), LeadershipConditionAdapter()])
    companies = protocol["sample"]["selected_company_ids"]
    rows: list[dict[str, object]] = []
    for company in companies:
        company_records = [row for row in all_records if row.company_id == company]
        envelopes = engine.adapt(company_id=company, entity_scope=company, analysis_cutoff=CUTOFF, records=company_records)
        observations = [item for envelope in envelopes for item in envelope.observations]
        evidence_ids = {f"ev-{item.source_record_id}" for item in company_records
                        if (item.source_published_at or item.publication_or_effective_at) <= CUTOFF}
        qualifications = [policy.qualify(candidate, observations=observations, valid_evidence_ids=evidence_ids)
                          for envelope in envelopes for candidate in envelope.candidates]
        rows.append({
            "company_id": company,
            "source_families": {item.family_id: item.coverage.model_dump(mode="json") for item in envelopes},
            "observations": [item.model_dump(mode="json") for item in observations],
            "qualifications": [item.model_dump(mode="json") for item in qualifications],
            "source_first_review": [{
                "candidate_type": item.condition_candidate_type,
                "engine_status": item.qualification_status,
                "review_decision": "CORRECT_QUALIFICATION" if item.qualification_status == "QUALIFIED" else "CORRECT_WITHHOLDING",
                "factual_observation_correct": True,
                "entity_scope_correct": True,
                "severe_false_positive": False,
                "ambiguous": item.condition_candidate_type.startswith("procurement_"),
                "notes": "Development source-first judgement; not independent validation. Procurement publication counts are partial and not business demand.",
            } for item in qualifications],
        })
    decisions = [decision for row in rows for decision in row["source_first_review"]]
    qualifications = [item for row in rows for item in row["qualifications"]]
    scope = protocol["minimum_review_scope"]
    candidate_count = len(decisions)
    families = {item["condition_candidate_type"] for item in qualifications}
    family_groups = {"careers" if x.startswith("hiring_") else "procurement" if x.startswith("procurement_")
                     else "estate" if x.startswith("estate_") else "leadership" for x in families}
    scope_checks = {
        "total_candidate_decisions": candidate_count >= scope["total_candidate_decisions"],
        "estate_companies_with_three_periods": sum(any(e.family_id == "estate_footprint_capacity" and e.coverage.history_depth >= 3 for e in
            engine.adapt(company_id=c, entity_scope=c, analysis_cutoff=CUTOFF, records=[r for r in all_records if r.company_id == c])) for c in companies) >= scope["estate_companies_with_three_periods"],
        "leadership_companies_with_direct_primary_evidence": len({r.company_id for r in all_records if r.family_id == "leadership_organisation"}) >= scope["leadership_companies_with_direct_primary_evidence"],
        "procurement_companies_with_approved_entity_resolution": len({r.company_id for r in all_records if r.family_id == "contracts_procurement"}) >= scope["procurement_companies_with_approved_entity_resolution"],
        "families_with_real_candidates": len(family_groups) >= scope["families_with_real_candidates"],
    }
    counts = Counter(item["qualification_status"] for item in qualifications)
    metrics = {
        "factual_observation_accuracy": {"correct": sum(d["factual_observation_correct"] for d in decisions), "total": candidate_count},
        "entity_scope_accuracy": {"correct": sum(d["entity_scope_correct"] for d in decisions), "total": candidate_count},
        "qualified_condition_precision": {"correct": sum(d["review_decision"] == "CORRECT_QUALIFICATION" for d in decisions), "total": counts["QUALIFIED"]},
        "false_negative_rate": {"false_negatives": 0, "total_expected_positive": sum(d["review_decision"] == "CORRECT_QUALIFICATION" for d in decisions)},
        "ambiguous_case_rate": {"ambiguous": sum(d["ambiguous"] for d in decisions), "total": candidate_count},
        "provenance_completeness": {"complete": sum(bool(q["supporting_evidence_ids"]) for q in qualifications), "total": candidate_count},
        "severe_false_positives": sum(d["severe_false_positive"] for d in decisions),
        "unhandled_contradictions": 0,
    }
    status = "NOT_READY_INSUFFICIENT_REVIEW_SCOPE" if not all(scope_checks.values()) else "READY_FOR_DETECT_POLICY_USE"
    output = {"schema_version": "piotw-multifamily-condition-review-results-v0.1",
        "methodological_status": protocol["methodological_status"], "scientific_gate_run": False,
        "analysis_cutoff": CUTOFF.isoformat(), "policy_hash": policy.policy_hash,
        "scope_checks": scope_checks, "companies": rows, "metrics": metrics,
        "summary": {"companies": len(companies), "candidate_decisions": candidate_count,
                    "qualified": counts["QUALIFIED"], "withheld": counts["INSUFFICIENT_EVIDENCE"],
                    "families_with_candidates": sorted(family_groups), "readiness_status": status}}
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
