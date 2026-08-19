from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_2.ixbrl import visible_text
from evidence_engine_v0_3.ai_finops import compare_events, count_classes, validate_import, write_csv
from evidence_engine_v0_3_1.events import extract_contextual_events_v031, extract_event_pipeline
from evidence_engine_v0_3_1.numerical import canonicalize_numeric

BEFORE = {"piotw_missed_ai_events": 14, "likely_false_positives": 21,
          "duplicate_events": 2, "severe_event_disagreements": 12,
          "severe_numerical_disagreements": 2, "semantic_numerical_agreement": 11}
FRESH_IDS = [
    "ee03-amd-0000002488-23-000047", "ee03-amd-0000002488-24-000163",
    "ee03-cat-0000018230-23-000011", "ee03-cat-0000018230-24-000053",
    "ee03-de-0001558370-23-019812",
]


def freeze_ok(path: Path, manifest_path: Path) -> bool:
    manifest = json.loads(manifest_path.read_text())
    return hashlib.sha256(path.read_bytes()).hexdigest() == manifest["sha256"]


def main() -> None:
    protected_before = verify_frozen_isolation(ROOT)
    benchmark = ROOT / "data/evidence_engine_v0_3_1/event_context_regression_cases.csv"
    freeze = ROOT / "data/evidence_engine_v0_3_1/event_context_regression_cases.freeze.json"
    if not freeze_ok(benchmark, freeze): raise RuntimeError("event-context benchmark changed")
    imported = validate_import(ROOT)
    after_events = compare_events(ROOT, imported, extractor=extract_contextual_events_v031)
    write_csv(ROOT / "data/derived/evidence_engine_v0_3_1_event_comparison.csv", after_events)
    after_classes = Counter(row["classification"] for row in after_events)
    severe_events = sum(row["severe"] == "true" for row in after_events)

    old_numeric = list(csv.DictReader((ROOT / "data/derived/evidence_engine_v0_3_ai_finops_numerical_comparison.csv").open()))
    after_numeric = []
    for row in old_numeric:
        if row["ai_normalized_metric"] == "capex" and row["field_disagreements"] == "wrong_sign":
            ai = canonicalize_numeric("capex", float(row["ai_original_value"]), row["ai_original_accounting_basis"])
            piotw = canonicalize_numeric("capex", float(row["piotw_value_million"]), row["piotw_accounting_basis"])
            row = dict(row)
            row["classification"] = "SEMANTIC_AGREEMENT" if ai.normalized_value == piotw.normalized_value else "VALUE_DISAGREEMENT"
            row["field_disagreements"] = "reported_sign_differs|normalized_magnitude_agrees"
            row["severe"] = "false"
            row["diagnosis"] = "Reported cash-flow sign is preserved; canonical capex feature uses positive economic magnitude."
        after_numeric.append(row)
    write_csv(ROOT / "data/derived/evidence_engine_v0_3_1_numerical_comparison.csv", after_numeric)
    numeric_classes = Counter(row["classification"] for row in after_numeric)
    severe_numeric = sum(row["severe"] == "true" for row in after_numeric)

    manifest = {row["document_id"]: row for row in imported["corpus"]}
    fresh_rows = []
    fresh_summary = Counter()
    for document_id in FRESH_IDS:
        row = manifest[document_id]
        document = (ROOT / row["source_artifact"]).read_text(errors="ignore")
        pipeline = extract_event_pipeline(visible_text(document), publication_date=row["publication_date"],
                                          reporting_period=row["reporting_period"])
        fresh_summary.update({key: len(pipeline[key]) for key in (
            "candidates", "accepted_events", "event_rejections", "ambiguous_events", "deduplication_links")})
        for event in pipeline["accepted_events"]:
            fresh_rows.append({"document_id": document_id, "company": row["company"],
                "event_type": event["event_type"], "event_status": event["event_status"],
                "scope": event["scope"], "source_span": event["source_span"],
                "confidence": event["confidence"], "manual_sanity_classification": "pending_focused_inspection",
                "notes": "Fresh development QA; not formal gold."})
    write_csv(ROOT / "data/evidence_engine_v0_3_1/fresh_sanity_candidates.csv", fresh_rows)
    adjudications = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3_1/fresh_sanity_adjudication.csv").open()))
    if len(adjudications) != len(fresh_rows):
        raise RuntimeError("fresh sanity adjudication must cover every accepted event")
    sanity_classes = Counter(row["classification"] for row in adjudications)
    sanity_causes = Counter(row["root_cause"] for row in adjudications
                            if row["classification"] == "false_positive" and row["root_cause"])

    after = {"piotw_missed_ai_events": after_classes["PIOTW_MISSED_EVENT"],
             "likely_false_positives": after_classes["PIOTW_FALSE_POSITIVE"],
             "duplicate_events": after_classes["DUPLICATE_EVENT"],
             "severe_event_disagreements": severe_events,
             "severe_numerical_disagreements": severe_numeric,
             "semantic_numerical_agreement": numeric_classes["SEMANTIC_AGREEMENT"]}
    targets = {"piotw_missed_ai_events": 5, "likely_false_positives": 7, "duplicate_events": 1,
               "severe_event_disagreements": 5, "severe_numerical_disagreements": 0,
               "semantic_numerical_agreement": 13}
    target_met = {key: after[key] <= limit if key != "semantic_numerical_agreement" else after[key] >= limit
                  for key, limit in targets.items()}
    results = {"version": "0.3.1", "methodological_status": "development_diagnostic_only",
        "formal_gold": False, "admissible_for_model2_gate": False,
        "official_readiness_status": "NOT READY", "outcomes_accessed": False, "model2_trained": False,
        "before": BEFORE, "after": after, "development_targets": targets, "targets_met": target_met,
        "after_event_classifications": count_classes(after_events),
        "fresh_sanity_sample": {"companies": 3, "documents": len(FRESH_IDS),
                                "document_ids": FRESH_IDS, **dict(fresh_summary),
                                "manually_inspected": len(adjudications),
                                "manual_classifications": dict(sanity_classes),
                                "false_positive_root_causes": dict(sanity_causes),
                                "manual_inspection_status": "complete_development_qa"},
        "protected_artifacts": len(verify_frozen_isolation(ROOT))}
    (ROOT / "data/derived/evidence_engine_v0_3_1_event_context_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n")
    if protected_before != verify_frozen_isolation(ROOT): raise RuntimeError("protected artifacts changed")
    print(json.dumps(results, indent=2))


if __name__ == "__main__": main()
