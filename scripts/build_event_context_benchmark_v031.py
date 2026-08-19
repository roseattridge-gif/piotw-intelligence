from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/derived/evidence_engine_v0_3_ai_finops_event_comparison.csv"
OUTPUT = ROOT / "data/evidence_engine_v0_3_1/event_context_regression_cases.csv"


def failure_class(row: dict[str, str]) -> str:
    text = (row["piotw_evidence_span"] or row["ai_exact_evidence_span"]).lower()
    if row["classification"] == "DUPLICATE_EVENT": return "duplicate"
    if "served as" in text or "career" in text or "where she worked" in text: return "biography"
    if "redundancy and other continuity" in text: return "taxonomy_overreach"
    if "as a simplification" in text: return "taxonomy_overreach"
    if "may include" in text or "assumptions about" in text: return "generic_boilerplate"
    if any(token in text for token in (" may ", " could ", " if ", "risk of")): return "hypothetical_risk"
    if row["classification"] == "AMBIGUOUS": return "incomplete_source"
    if row["classification"] == "PIOTW_MISSED_EVENT": return "synonym_or_phrase_structure_missing"
    if row["classification"] == "PIOTW_FALSE_POSITIVE": return "contextual_false_positive"
    return "unadjudicated_plausible_ai_omission"


def main() -> None:
    with SOURCE.open(newline="") as stream: rows = list(csv.DictReader(stream))
    fields = ["case_id", "benchmark_version", "document_id", "source_span", "piotw_proposed_event",
              "diagnostic_expected_classification", "expected_context_status", "failure_class",
              "formal_gold", "admissible_for_model2_gate", "notes"]
    output = []
    for row in rows:
        classification = row["classification"]
        if classification == "PIOTW_MISSED_EVENT":
            expected, status = "accepted", "planned" if row["ai_normalized_event_type"] == "major_investment" else "current_or_ongoing"
        elif classification in {"PIOTW_FALSE_POSITIVE", "DUPLICATE_EVENT"}:
            expected, status = "rejected", "hypothetical_or_irrelevant"
        else:
            expected, status = "ambiguous", "requires_human_adjudication"
        output.append({"case_id": row["comparison_id"], "benchmark_version": "0.3.1",
            "document_id": row["document_id"],
            "source_span": row["piotw_evidence_span"] or row["ai_exact_evidence_span"],
            "piotw_proposed_event": row["piotw_event_type"] or row["ai_normalized_event_type"],
            "diagnostic_expected_classification": expected, "expected_context_status": status,
            "failure_class": failure_class(row), "formal_gold": "false",
            "admissible_for_model2_gate": "false",
            "notes": "Frozen AI-assisted development diagnostic; not independent truth."})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fields, lineterminator="\n"); writer.writeheader(); writer.writerows(output)
    manifest = {"benchmark_version": "0.3.1", "status": "frozen_development_diagnostic",
        "formal_gold": False, "admissible_for_model2_gate": False, "rows": len(output),
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "source": "Evidence Engine 0.3 AI finance/operations diagnostic comparison"}
    (OUTPUT.parent / "event_context_regression_cases.freeze.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__": main()
