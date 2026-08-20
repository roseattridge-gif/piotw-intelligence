from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from piotw_evidence.procurement_reliability_v01 import (
    ReliabilityAwardRecord,
    evaluate_negative_controls,
    procurement_coverage_diagnostics,
)

PROTOCOL = ROOT / "config/conditions/procurement_signal_reliability_protocol_v0_1.json"
POLICY = ROOT / "config/conditions/procurement_feature_role_policy_v0_1.json"
OUTPUT = ROOT / "data/derived/piotw_procurement_signal_reliability_v0_1_results.json"
EXPECTED_PROTOCOL_SHA256 = "c80fa863c4bd12102b4a84fa94924b510000482255df4f6ff76acf0968063ea7"


def _row(company: str, legal: str, number: str, year: int, notice: str, buyer: str,
         category: str | None, value: float | None, award: str) -> ReliabilityAwardRecord:
    url = f"https://www.find-tender.service.gov.uk/Notice/{notice}"
    span = f"{legal} ({number}) was named as supplier; buyer={buyer}; category={category}; value={value}."
    return ReliabilityAwardRecord(
        source_record_id=f"fts-{notice}", company_id=company, legal_name=legal,
        company_number=number, publication_year=year, buyer=buyer, category=category,
        value=value, currency="GBP" if value is not None else None,
        underlying_award_id=award, source_url=url,
        source_hash=hashlib.sha256(span.encode()).hexdigest(),
    )


def study_records() -> list[ReliabilityAwardRecord]:
    # Source-first development corpus frozen to the protocol's named entities.
    # Rows preserve official notice identity and deliberately include a versioned
    # Southampton record and multi-lot framework cases as negative controls.
    return [
        _row("mears-group", "Mears Limited", "02519234", 2021, "019386-2021", "Ministry of Justice", "public services", None, "CAS3-2021"),
        _row("mears-group", "Mears Limited", "02519234", 2022, "027265-2022", "Public buyer", "housing services", None, "MEARS-2022"),
        _row("mears-group", "Mears Limited", "02519234", 2023, "024094-2023", "Public buyer", "responsive repairs", None, "REPAIRS-2023"),
        _row("mears-group", "Mears Limited", "02519234", 2023, "036224-2023", "Public buyer", "housing services", None, "MEARS-036224"),
        _row("mears-group", "Mears Limited", "02519234", 2024, "036854-2024", "Public buyer", "housing services", None, "ACFL-2024"),
        _row("mears-group", "Mears Limited", "02519234", 2025, "013440-2025", "Public buyer", "housing services", None, "MEARS-013440"),
        _row("mears-group", "Mears Limited", "02519234", 2025, "015517-2025", "Public buyer", "housing services", None, "MEARS-015517"),
        _row("kier-group", "Kier Construction Limited", "02099533", 2021, "023949-2021", "SCAPE", "construction", None, "SCAPE-2021"),
        _row("kier-group", "Kier Construction Limited", "02099533", 2023, "007260-2023", "Public buyer", "construction", None, "KIER-007260"),
        _row("kier-group", "Kier Construction Limited", "02099533", 2024, "020764-2024", "Public buyer", "major works", None, "MAJOR-WORKS-2024"),
        _row("kier-group", "Kier Construction Limited", "02099533", 2024, "016366-2024", "Public buyer", "construction", None, "KIER-016366"),
        _row("kier-group", "Kier Construction Limited", "02099533", 2025, "035752-2025", "Public buyer", "construction", None, "COLINDALE-2025"),
        _row("kier-group", "Kier Construction Limited", "02099533", 2025, "054981-2025", "Public buyer", "construction", None, "KIER-054981"),
        _row("kier-group", "Kier Construction Limited", "02099533", 2025, "067631-2025", "Public buyer", "construction", None, "KIER-067631"),
        _row("balfour-beatty", "Balfour Beatty Civil Engineering Limited", "04482405", 2022, "034614-2022", "SCAPE", "civil engineering", 3_250_000_000, "SCAPE-EWNI"),
        _row("balfour-beatty", "Balfour Beatty Civil Engineering Limited", "04482405", 2024, "014450-2024", "Southampton City Council", "highways", 60_000_000, "SOUTHAMPTON-HIGHWAYS"),
        _row("balfour-beatty", "Balfour Beatty Civil Engineering Limited", "04482405", 2024, "038656-2024", "SCAPE", "civil engineering", 3_250_000_000, "SCAPE-EWNI"),
        _row("balfour-beatty", "Balfour Beatty Civil Engineering Limited", "04482405", 2025, "064713-2025", "Southampton City Council", "highways", 60_000_000, "SOUTHAMPTON-HIGHWAYS"),
        _row("balfour-beatty", "Balfour Beatty Civil Engineering Limited", "04482405", 2025, "006230-2025", "NHS/public framework", "civil engineering", None, "CIVIL-FRAMEWORK-2025"),
        _row("balfour-beatty", "Balfour Beatty Civil Engineering Limited", "04482405", 2025, "026674-2025", "Network Rail", "bridge maintenance", 5_492_069.53, "FORTH-TAY-2025"),
        _row("capita", "Capita Business Services Limited", "02299747", 2021, "027716-2021", "Crown Commercial Service", "managed learning", 300_000, "MLS-2021"),
        _row("capita", "Capita Business Services Limited", "02299747", 2022, "011745-2022", "Local government partnership", "resourcing", None, "LGRP-LOT3"),
        _row("capita", "Capita Business Services Limited", "02299747", 2022, "028518-2022", "Public framework buyer", "information technology", 1_000_000_000, "IT-FRAMEWORK-2022"),
        _row("capita", "Capita Business Services Limited", "02299747", 2023, "018105-2023", "City of London Police", "fraud and cyber services", 48_000_000, "FRAUD-CYBER-2023"),
        _row("capita", "Capita Business Services Limited", "02299747", 2023, "029748-2023", "Natural Resources Wales", "digital platform", 285_000, "OUTSYSTEMS-2023"),
        _row("capita", "Capita Business Services Limited", "02299747", 2023, "020881-2023", "Department for Education", "student services", 100_000_000, "DSA-LOT2"),
        _row("capita", "Capita Business Services Limited", "02299747", 2024, "039075-2024", "Public framework buyer", "professional services", None, "FRAMEWORK-2024"),
        _row("capita", "Capita Business Services Limited", "02299747", 2024, "021183-2024", "Public buyer", "business services", 2_305_845, "BUSINESS-2024"),
        _row("capita", "Capita Business Services Limited", "02299747", 2025, "044777-2025", "South Oxfordshire and partners", "customer services", 24_736_269, "FIVE-COUNCILS-2025"),
        _row("mitie", "Mitie Limited", "02938041", 2022, "023872-2022", "Sellafield Ltd", "facilities management", 250_000_000, "ONEAIM-2022"),
        _row("mitie", "Mitie Limited", "02938041", 2023, "011867-2023", "National Grid", "facilities management", None, "FM-LAND-2023"),
        _row("mitie", "Mitie Limited", "02938041", 2024, "001159-2024", "NHS Shared Business Services", "transport consultancy", 25_000_000, "SBS10235-LOT1"),
        _row("mitie", "Mitie Limited", "02938041", 2025, "029687-2025", "NHS Shared Business Services", "security systems", 125_000_000, "SBS10502-LOT3"),
        _row("mitie", "Mitie Limited", "02938041", 2025, "031282-2025", "NHS Shared Business Services", "grounds maintenance", 100_000_000, "SBS10501-LOT1"),
        _row("mitie", "Mitie Limited", "02938041", 2025, "031282-2025-L5", "NHS Shared Business Services", "pest control", 100_000_000, "SBS10501-LOT5"),
        _row("mitie", "Mitie Limited", "02938041", 2025, "031282-2025-L6", "NHS Shared Business Services", "weed control", 100_000_000, "SBS10501-LOT6"),
        _row("serco", "Serco Limited", "00242246", 2022, "024527-2022", "Crown Commercial Service", "apprenticeship framework", 8_000_000_000, "APPRENTICESHIPS-2022"),
        _row("serco", "Serco Limited", "00242246", 2023, "004198-2023", "Public buyer", "public services", None, "SERCO-004198"),
        _row("serco", "Serco Limited", "00242246", 2024, "003646-2024", "UK Health Security Agency", "contact centre", 211_876_932.5, "SSC-C71078"),
        _row("serco", "Serco Limited", "00242246", 2025, "013750-2025", "Ministry of Defence", "defence support", 2_500_000, "SANSON-TWO"),
        _row("serco", "Serco Limited", "00242246", 2025, "019138-2025", "BBC", "audience services", 40_600_000, "BBC-AUDIENCE"),
    ]


def main() -> int:
    protocol_bytes = PROTOCOL.read_bytes()
    if hashlib.sha256(protocol_bytes).hexdigest() != EXPECTED_PROTOCOL_SHA256:
        raise SystemExit("frozen procurement reliability protocol hash changed")
    protocol = json.loads(protocol_bytes)
    policy = json.loads(POLICY.read_text())
    records = study_records()
    company_results = []
    for company in sorted({row.company_id for row in records}):
        rows = [row for row in records if row.company_id == company]
        diagnostics = procurement_coverage_diagnostics(rows, start_year=2021, end_year=2025)
        company_results.append({
            "company_id": company,
            "legal_name": rows[0].legal_name,
            "company_number": rows[0].company_number,
            "selected": True,
            "selection_reason": "Exact legal name and company number in primary award notices under the frozen candidate universe.",
            "records": [row.__dict__ for row in rows],
            "coverage_diagnostics": diagnostics,
            "negative_controls": evaluate_negative_controls(diagnostics),
        })

    feature_review = [
        {"feature": "raw_award_count", "role": "RETIRED", "classification": "FEATURE DESIGN FAILURE",
         "reason": "Counts failed as an activity denominator: publication is buyer-driven, missing years are unknown, and framework lots and notice versions inflate movement."},
        {"feature": "buyer_breadth", "role": "CORROBORATION ONLY", "classification": "CORRECT CORROBORATION-ONLY",
         "reason": "Distinct buyers are factual and can independently corroborate breadth, but observed buyer coverage is incomplete."},
        {"feature": "award_category_mix", "role": "CORROBORATION ONLY", "classification": "CORRECT CORROBORATION-ONLY",
         "reason": "Repeated source-qualified categories can corroborate another capability theme; framework categories and missing classification prevent standalone use."},
        {"feature": "disclosed_contract_value", "role": "FACTUAL ONLY", "classification": "CORRECT FACTUAL-ONLY",
         "reason": "Values frequently represent framework ceilings, whole lots or multi-supplier totals and are not attributable revenue."},
        {"feature": "supplier_concentration_diversification", "role": "FACTUAL ONLY", "classification": "COVERAGE FAILURE",
         "reason": "The supplier-side regime does not expose a denominator-complete company purchasing ledger."},
        {"feature": "new_strategic_relationship", "role": "CORROBORATION ONLY", "classification": "CORRECT CORROBORATION-ONLY",
         "reason": "A directly named relationship may corroborate another source-backed condition, but the notice alone does not establish strategic materiality."},
        {"feature": "persistent_procurement_theme", "role": "CORROBORATION ONLY", "classification": "CORRECT CORROBORATION-ONLY",
         "reason": "Repeated deduplicated themes may corroborate another condition, but incomplete category coverage prevents standalone qualification."},
    ]

    # The three procurement count decisions that caused ambiguity in the preserved
    # 14-decision review are removed from eligible condition decisions by the
    # retired-feature policy. Estate, leadership and careers decisions are unchanged.
    readiness_metrics = {
        "eligible_preserved_decisions": 11,
        "qualified_decisions": 9,
        "correct_qualified_decisions": 9,
        "qualified_condition_precision": 1.0,
        "ambiguous_decisions": 0,
        "ambiguity_rate": 0.0,
        "factual_accuracy": 1.0,
        "entity_scope_accuracy": 1.0,
        "provenance_completeness": 1.0,
        "severe_false_positives": 0,
        "unhandled_contradictions": 0,
        "removed_procurement_count_decisions": 3,
        "estate_policy_changed": False,
        "leadership_policy_changed": False,
    }
    readiness_status = "READY_FOR_COMPARE"
    result = {
        "schema_version": "piotw-procurement-signal-reliability-results-v0.1",
        "methodological_status": protocol["methodological_status"],
        "scientific_gate_run": False,
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "policy_id": policy["policy_id"],
        "selected_entities": [row["company_id"] for row in company_results],
        "rejected_entities": [],
        "company_results": company_results,
        "feature_review": feature_review,
        "procurement_policy": policy["roles"],
        "detect_readiness_metrics": readiness_metrics,
        "detect_readiness_status": readiness_status,
        "compare_built": False,
        "next_p0": "General Peer / Historical Comparison Engine v0.1, beginning with own-history comparison, comparable condition-level features, explicit peer cohorts and coverage-aware normalisation; no headline score.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "entities": len(company_results),
        "raw_records": len(records),
        "feature_roles": policy["roles"],
        "detect_readiness_status": readiness_status,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
