from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/evidence_engine_v0_3_2/table_historical_regression_cases.csv"
FREEZE = ROOT / "data/evidence_engine_v0_3_2/table_historical_regression_cases.freeze.json"

SYNTHETIC = [
    ("comparative", "Restructuring charges 2022 $18m 2021 $25m", "restructuring", "rejected", "multi_year_history", "table_row", "comparative", "historical_table", "financial_observation_not_operational_event"),
    ("historical", "Charges related to the 2022 programme were $18m.", "restructuring", "rejected", "historical", "narrative_sentence", "prior", "completed_programme", "historical_or_comparative_disclosure"),
    ("current-charge", "Restructuring charges for 2024 were $24m.", "restructuring", "rejected", "current", "table_row", "current", "accounting_measure_only", "financial_observation_not_operational_event"),
    ("current-program", "During 2024 we initiated a restructuring programme.", "restructuring", "accepted", "current", "narrative_sentence", "current", "current_programme", "current_operational_support"),
    ("footnote", "1 Represents restructuring costs included in operating expenses.", "restructuring", "rejected", "unknown", "table_footnote", "unknown", "accounting_measure_only", "financial_observation_not_operational_event"),
    ("malformed", "2024 2023 24 (18 9 7 Restructuring GAAP Adjusted", "restructuring", "rejected", "ambiguous", "malformed_unknown_fragment", "unknown", "malformed_table_fragment", "malformed_table_fragment"),
    ("repeated-heading", "2024 2023 GAAP Adjusted Restructuring 2024 2023 Table of Contents", "restructuring", "rejected", "ambiguous", "malformed_unknown_fragment", "unknown", "repeated_table_heading", "malformed_table_fragment"),
    ("subtotal", "Total restructuring costs 2024 120 2023 95", "restructuring", "rejected", "multi_year_history", "table_row", "current_and_comparative", "accounting_measure_only", "financial_observation_not_operational_event"),
    ("negative", "Restructuring charges (24) 18", "restructuring", "rejected", "unknown", "table_row", "unknown", "accounting_measure_only", "financial_observation_not_operational_event"),
    ("multicolumn", "Three Months Ended 2024 2023 Restructuring costs 24 18", "restructuring", "rejected", "multi_year_history", "table_row", "current_and_comparative", "accounting_measure_only", "financial_observation_not_operational_event"),
    ("supported-note", "During 2024 we initiated a site closure. Restructuring charges were $24m.", "site_closure", "accepted", "current", "narrative_paragraph", "current", "current_programme", "current_operational_support"),
]


def main() -> None:
    candidates = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3_1/fresh_sanity_candidates.csv").open()))
    labels = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3_1/fresh_sanity_adjudication.csv").open()))
    rows = []
    for label in labels:
        if label["classification"] not in {"false_positive", "ambiguous"}:
            continue
        candidate = candidates[int(label["row_index"]) - 1]
        root = label["root_cause"]
        failure = {
            "historical_completed_event": "historical_table",
            "table_fragment": "malformed_table_fragment",
            "wrong_context": "accounting_measure_only",
            "source_layout_issue": "narrative_table_mismatch",
        }.get(root, root or "other")
        rows.append({
            "case_id": f"fresh-{int(label['row_index']):03d}",
            "document_id": candidate["document_id"],
            "source_page": "unknown_not_preserved_by_v0_3_1_html_extraction",
            "raw_extracted_span": candidate["source_span"],
            "candidate_event_type": candidate["event_type"],
            "expected_disposition": "ambiguous" if label["classification"] == "ambiguous" else "rejected",
            "historical_current_status": "historical" if "historical" in root else "ambiguous",
            "table_narrative_status": "malformed_unknown_fragment" if "fragment" in root else "unknown_requires_retyping",
            "comparative_current_period": "unknown",
            "failure_class": failure,
            "expected_reason": "preserve_ambiguity" if label["classification"] == "ambiguous" else failure,
            "formal_gold": "false",
            "admissible_for_model2_gate": "false",
            "notes": label["notes"],
        })
    for index, item in enumerate(SYNTHETIC, 1):
        name, span, event_type, disposition, status, structure, period, failure, reason = item
        rows.append({"case_id": f"synthetic-{index:03d}-{name}", "document_id": "synthetic-v0-3-2",
            "source_page": "synthetic", "raw_extracted_span": span,
            "candidate_event_type": event_type, "expected_disposition": disposition,
            "historical_current_status": status, "table_narrative_status": structure,
            "comparative_current_period": period, "failure_class": failure,
            "expected_reason": reason, "formal_gold": "false",
            "admissible_for_model2_gate": "false", "notes": "Generalized development regression case."})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    FREEZE.write_text(json.dumps({"version": "0.3.2", "rows": len(rows), "sha256": digest,
        "formal_gold": False, "admissible_for_model2_gate": False}, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "sha256": digest}))


if __name__ == "__main__":
    main()
