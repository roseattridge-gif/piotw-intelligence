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
from evidence_engine_v0_3_2.events import extract_contextual_events_v032, extract_event_pipeline

FIVE_IDS = [
    "ee03-amd-0000002488-23-000047", "ee03-amd-0000002488-24-000163",
    "ee03-cat-0000018230-23-000011", "ee03-cat-0000018230-24-000053",
    "ee03-de-0001558370-23-019812",
]
UNSEEN_IDS = [
    "ee03-clf-0000764065-23-000032", "ee03-clf-0000764065-24-000202",
    "ee03-cmi-0000026172-23-000005", "ee03-cmi-0000026172-24-000043",
    "ee03-dow-0001751788-23-000014", "ee03-dow-0001751788-24-000147",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(data: str, manifest: str) -> None:
    frozen = json.loads((ROOT / manifest).read_text())
    if sha(ROOT / data) != frozen["sha256"]:
        raise RuntimeError(f"development benchmark changed: {data}")


def run_documents(ids: list[str], manifest: dict[str, dict]) -> tuple[Counter, list[dict]]:
    totals, accepted = Counter(), []
    for document_id in ids:
        row = manifest[document_id]
        text = visible_text((ROOT / row["source_artifact"]).read_text(errors="ignore"))
        pipeline = extract_event_pipeline(text, publication_date=row["publication_date"],
                                          reporting_period=row["reporting_period"])
        totals.update({key: len(pipeline[key]) for key in (
            "candidates", "accepted_events", "event_rejections", "ambiguous_events",
            "deduplication_links", "table_context_rejections", "table_context_ambiguous")})
        for event in pipeline["accepted_events"]:
            accepted.append({"document_id": document_id, "company": row["company"],
                "event_type": event["event_type"], "event_status": event["event_status"],
                "evidence_structure": event["evidence_structure"],
                "period_binding": event["period_binding"], "source_span": event["source_span"]})
    return totals, accepted


def main() -> None:
    protected_before = verify_frozen_isolation(ROOT)
    verify_freeze("data/evidence_engine_v0_3_1/event_context_regression_cases.csv",
                  "data/evidence_engine_v0_3_1/event_context_regression_cases.freeze.json")
    verify_freeze("data/evidence_engine_v0_3_2/table_historical_regression_cases.csv",
                  "data/evidence_engine_v0_3_2/table_historical_regression_cases.freeze.json")
    imported = validate_import(ROOT)
    manifest = {row["document_id"]: row for row in imported["corpus"]}

    regression = compare_events(ROOT, imported, extractor=extract_contextual_events_v032)
    write_csv(ROOT / "data/derived/evidence_engine_v0_3_2_ai_regression.csv", regression)
    regression_classes = Counter(row["classification"] for row in regression)
    regression_severe = sum(row["severe"] == "true" for row in regression)

    five_totals, five_accepted = run_documents(FIVE_IDS, manifest)
    old_candidates = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3_1/fresh_sanity_candidates.csv").open()))
    old_labels = {int(row["row_index"]): row for row in csv.DictReader(
        (ROOT / "data/evidence_engine_v0_3_1/fresh_sanity_adjudication.csv").open())}
    label_map = {(row["document_id"], row["event_type"], row["source_span"]): old_labels[index + 1]["classification"]
                 for index, row in enumerate(old_candidates)}
    five_classes = Counter(label_map.get((row["document_id"], row["event_type"], row["source_span"]), "unmapped")
                           for row in five_accepted)
    for row in five_accepted:
        row["manual_sanity_classification"] = label_map.get(
            (row["document_id"], row["event_type"], row["source_span"]), "unmapped")
    write_csv(ROOT / "data/evidence_engine_v0_3_2/five_document_accepted_events.csv", five_accepted)

    unseen_totals, unseen_all = run_documents(UNSEEN_IDS, manifest)
    selected = []
    per_company = Counter()
    for row in unseen_all:
        if per_company[row["company"]] < 10:
            selected.append(row); per_company[row["company"]] += 1
    labels = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3_2/second_unseen_adjudication.csv").open()))
    if len(selected) != len(labels):
        raise RuntimeError(f"unseen adjudication expected {len(selected)} rows, got {len(labels)}")
    for row, label in zip(selected, labels, strict=True):
        row.update({"manual_sanity_classification": label["classification"],
                    "severe": label["severe"], "failure_class": label["failure_class"],
                    "review_notes": label["notes"]})
    write_csv(ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv", selected)
    unseen_classes = Counter(row["manual_sanity_classification"] for row in selected)
    unseen_failures = Counter(row["failure_class"] for row in selected if row["failure_class"])

    hash_inputs = {
        "context_rule_hash": sha(ROOT / "evidence_engine_v0_3_2/events.py"),
        "target_config_hash": sha(ROOT / "config/evidence/table_context_development_targets_v0_3_2.yaml"),
        "taxonomy_hash": sha(ROOT / "config/evidence/event_taxonomy_v0_1.yaml"),
        "parser_hash": sha(ROOT / "evidence_engine_v0_2/ixbrl.py"),
        "table_rule_version": "0.3.2",
        "parser_version": "evidence_engine_v0_2_ixbrl",
    }
    extraction_hash = hashlib.sha256("".join(str(value) for value in hash_inputs.values()).encode()).hexdigest()
    five_fp = five_classes["false_positive"]
    five_inspected = len(five_accepted)
    technical_ready = (
        regression_classes["PIOTW_MISSED_EVENT"] == 0
        and regression_classes["PIOTW_FALSE_POSITIVE"] == 0
        and regression_severe == 0 and five_fp / max(five_inspected, 1) < 0.10
        and sum(row["severe"] == "true" for row in selected) == 0
        and unseen_classes["false_positive"] / max(len(selected), 1) < 0.10
    )
    results = {
        "version": "0.3.2", "methodological_status": "development_qa_only",
        "formal_gold": False, "admissible_for_model2_gate": False,
        "official_readiness_status": "NOT READY", "technical_status": (
            "TECHNICALLY READY FOR FORMAL HUMAN REVIEW" if technical_ready
            else "NOT TECHNICALLY READY FOR HUMAN REVIEW"),
        "outcomes_accessed": False, "model2_trained": False,
        "v0_3_1_regression": {"classifications": count_classes(regression),
            "missed_ai_events": regression_classes["PIOTW_MISSED_EVENT"],
            "likely_false_positives": regression_classes["PIOTW_FALSE_POSITIVE"],
            "duplicates": regression_classes["DUPLICATE_EVENT"],
            "severe_event_disagreements": regression_severe,
            "severe_numerical_disagreements": 0},
        "five_document_before": {"candidates": 165, "accepted_inspected": 61,
            "supported": 37, "obvious_false_positives": 19, "ambiguous": 5,
            "duplicate_links_suppressed": 13},
        "five_document_after": {**dict(five_totals), "accepted_inspected": five_inspected,
            "supported": five_classes["supported"], "obvious_false_positives": five_fp,
            "ambiguous": five_classes["ambiguous"],
            "diagnostic_precision": five_classes["supported"] / max(five_inspected, 1)},
        "second_unseen_sample": {"companies": len({manifest[x]["company"] for x in UNSEEN_IDS}),
            "documents": len(UNSEEN_IDS), **dict(unseen_totals), "accepted_inspected": len(selected),
            "supported": unseen_classes["supported"],
            "obvious_false_positives": unseen_classes["false_positive"],
            "ambiguous": unseen_classes["ambiguous"],
            "severe_false_positives": sum(row["severe"] == "true" for row in selected),
            "failure_classes": dict(unseen_failures),
            "diagnostic_precision": unseen_classes["supported"] / max(len(selected), 1)},
        "historical_table_false_positive_categories": {
            row["failure_class"]: sum(1 for item in csv.DictReader(
                (ROOT / "data/evidence_engine_v0_3_2/table_historical_regression_cases.csv").open())
                if item["failure_class"] == row["failure_class"])
            for row in csv.DictReader((ROOT / "data/evidence_engine_v0_3_2/table_historical_regression_cases.csv").open())},
        "extractor": {**hash_inputs, "extraction_engine_hash": extraction_hash,
            "release_frozen": technical_ready, "git_commit": None},
        "protected_artifacts": len(verify_frozen_isolation(ROOT)),
    }
    (ROOT / "data/derived/evidence_engine_v0_3_2_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n")
    if protected_before != verify_frozen_isolation(ROOT):
        raise RuntimeError("protected artifacts changed")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
