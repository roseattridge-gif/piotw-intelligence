from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/evidence_engine_v0_3_3/entity_risk_context_regression_cases.csv"
FREEZE = ROOT / "data/evidence_engine_v0_3_3/entity_risk_context_regression_cases.freeze.json"

SYNTHETIC = [
    ("supplier", "Our suppliers experienced labour shortages.", "labour_constraint", "external", "supplier", "supplier", "actual_current", "current", "no", "rejected", "supplier_attribution"),
    ("supplier-impact", "Supplier shortages caused delays to our production.", "operational_disruption", "direct", "target company", "target_company", "actual_current", "current", "no", "accepted", "explicit_company_impact"),
    ("customer", "Our customers reduced inventory.", "demand_weakness", "external", "customer", "customer", "actual_current", "current", "no", "rejected", "customer_attribution"),
    ("customer-impact", "Customer destocking reduced our sales volumes by 18%.", "demand_weakness", "direct", "target company", "target_company", "actual_current", "current", "no", "accepted", "explicit_company_impact"),
    ("competitor", "Our competitors announced capacity expansion.", "capacity_expansion", "external", "competitor", "competitor", "actual_current", "current", "no", "rejected", "competitor_attribution"),
    ("industry", "The semiconductor industry experienced inventory correction.", "demand_weakness", "external", "semiconductor industry", "industry", "actual_current", "current", "no", "rejected", "industry_attribution"),
    ("quote", "According to analysts, demand could decline.", "demand_weakness", "external", "analyst", "third_party", "hypothetical_risk", "forecast", "no", "rejected", "third_party_quote"),
    ("biography", "She previously led a restructuring programme at Company X.", "restructuring", "external", "former employer", "former_employer", "actual_historical", "historical", "no", "rejected", "biography"),
    ("acquisition", "The acquisition target plans a site closure.", "site_closure", "external", "acquisition target", "acquisition_target", "planned", "planned", "no", "rejected", "acquisition_target"),
    ("jv", "Our joint venture announced capacity expansion.", "capacity_expansion", "shared", "joint venture", "joint_venture", "planned", "planned", "no", "rejected", "joint_venture"),
    ("subsidiary", "Our controlled subsidiary initiated a site closure.", "site_closure", "direct", "controlled subsidiary", "target_subsidiary", "actual_current", "current", "no", "accepted", "target_subsidiary"),
    ("segment", "Our Aviation segment experienced demand weakness.", "demand_weakness", "direct", "Aviation", "target_segment", "actual_current", "current", "no", "accepted", "target_segment"),
    ("generic", "Economic downturns could affect revenue.", "demand_weakness", "unclear", "unknown", "unknown", "generic_risk", "forecast", "yes", "rejected", "generic_risk"),
    ("risk-actual", "Risk Factors: We are currently experiencing supply disruptions affecting production.", "supply_chain_constraint", "direct", "target company", "target_company", "actual_current", "current", "yes", "accepted", "actual_condition_in_risk_section"),
    ("conditional-actual", "Demand could weaken further after declining 20% this quarter.", "demand_weakness", "direct", "target company", "target_company", "actual_current_with_forecast", "current", "yes", "accepted", "embedded_current_fact"),
    ("negation", "No restructuring is planned.", "restructuring", "direct", "target company", "target_company", "negated", "current", "no", "rejected", "negation"),
]


def main() -> None:
    prior = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv").open()))
    rows = []
    for index, row in enumerate(prior, 1):
        if row["manual_sanity_classification"] == "supported":
            continue
        rows.append({"case_id": f"v032-unseen-{index:03d}", "document_id": row["document_id"],
            "source_span": row["source_span"], "event_candidate": row["event_type"],
            "target_company_relevance": "unclear_requires_attribution",
            "subject_entity": "unresolved_in_v0_3_2", "subject_type": "unknown",
            "actual_hypothetical_status": "unknown", "current_historical_status": row["event_status"],
            "risk_section_status": "unknown", "expected_disposition": (
                "ambiguous" if row["manual_sanity_classification"] == "ambiguous" else "rejected"),
            "root_cause_category": row["failure_class"], "formal_gold": "false",
            "admissible_for_model2_gate": "false", "notes": row["review_notes"]})
    for index, item in enumerate(SYNTHETIC, 1):
        name, span, event, relevance, entity, subject, actual, current, risk, disposition, cause = item
        rows.append({"case_id": f"synthetic-{index:03d}-{name}", "document_id": "synthetic-v0-3-3",
            "source_span": span, "event_candidate": event, "target_company_relevance": relevance,
            "subject_entity": entity, "subject_type": subject,
            "actual_hypothetical_status": actual, "current_historical_status": current,
            "risk_section_status": risk, "expected_disposition": disposition,
            "root_cause_category": cause, "formal_gold": "false",
            "admissible_for_model2_gate": "false", "notes": "Generalized development regression case."})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    FREEZE.write_text(json.dumps({"version": "0.3.3", "rows": len(rows), "sha256": digest,
        "formal_gold": False, "admissible_for_model2_gate": False}, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "sha256": digest}))


if __name__ == "__main__":
    main()
