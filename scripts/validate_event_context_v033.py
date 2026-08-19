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
from evidence_engine_v0_3_3.events import extract_contextual_events_v033, extract_event_pipeline

FIVE_IDS = ["ee03-amd-0000002488-23-000047", "ee03-amd-0000002488-24-000163",
    "ee03-cat-0000018230-23-000011", "ee03-cat-0000018230-24-000053",
    "ee03-de-0001558370-23-019812"]
PRIOR_UNSEEN_IDS = ["ee03-clf-0000764065-23-000032", "ee03-clf-0000764065-24-000202",
    "ee03-cmi-0000026172-23-000005", "ee03-cmi-0000026172-24-000043",
    "ee03-dow-0001751788-23-000014", "ee03-dow-0001751788-24-000147"]
NEW_TICKERS = {"GM", "HON", "HPQ"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(data: str, manifest: str) -> None:
    frozen = json.loads((ROOT / manifest).read_text())
    if sha(ROOT / data) != frozen["sha256"]:
        raise RuntimeError(f"benchmark changed: {data}")


def extract_docs(ids: list[str], manifest: dict[str, dict], artifact_field: str) -> tuple[Counter, list[dict]]:
    totals, accepted = Counter(), []
    for document_id in ids:
        row = manifest[document_id]
        text = visible_text((ROOT / row[artifact_field]).read_text(errors="ignore"))
        pipeline = extract_event_pipeline(text, publication_date=row["publication_date"],
                                          reporting_period=row["reporting_period"])
        totals.update({key: len(pipeline[key]) for key in ("candidates", "accepted_events",
            "event_rejections", "ambiguous_events", "deduplication_links",
            "entity_context_rejections", "entity_context_ambiguous")})
        for event in pipeline["accepted_events"]:
            accepted.append({"document_id": document_id, "company": row["company"],
                "event_type": event["event_type"], "event_status": event["event_status"],
                "subject_type": event["subject_type"], "entity_scope": event["entity_scope"],
                "factual_status": event["factual_status"], "source_span": event["source_span"]})
    return totals, accepted


def retained_classes(accepted: list[dict], labelled_path: Path) -> tuple[Counter, int]:
    keys = {(row["document_id"], row["event_type"], row["source_span"]) for row in accepted}
    labelled = list(csv.DictReader(labelled_path.open()))
    counts = Counter(row["manual_sanity_classification"] for row in labelled
                     if (row["document_id"], row["event_type"], row["source_span"]) in keys)
    return counts, sum(row["manual_sanity_classification"] == "supported" for row in labelled)


def main() -> None:
    protected_before = verify_frozen_isolation(ROOT)
    for data, manifest in [
        ("data/evidence_engine_v0_3_1/event_context_regression_cases.csv", "data/evidence_engine_v0_3_1/event_context_regression_cases.freeze.json"),
        ("data/evidence_engine_v0_3_2/table_historical_regression_cases.csv", "data/evidence_engine_v0_3_2/table_historical_regression_cases.freeze.json"),
        ("data/evidence_engine_v0_3_3/entity_risk_context_regression_cases.csv", "data/evidence_engine_v0_3_3/entity_risk_context_regression_cases.freeze.json")]:
        verify_freeze(data, manifest)
    imported = validate_import(ROOT)
    manifest_v3 = {row["document_id"]: row for row in imported["corpus"]}
    regression = compare_events(ROOT, imported, extractor=extract_contextual_events_v033)
    regression_classes = Counter(row["classification"] for row in regression)
    write_csv(ROOT / "data/derived/evidence_engine_v0_3_3_ai_regression.csv", regression)

    five_totals, five_accepted = extract_docs(FIVE_IDS, manifest_v3, "source_artifact")
    five_classes, five_supported_total = retained_classes(
        five_accepted, ROOT / "data/evidence_engine_v0_3_2/five_document_accepted_events.csv")
    prior_totals, prior_accepted = extract_docs(PRIOR_UNSEEN_IDS, manifest_v3, "source_artifact")
    prior_classes, prior_supported_total = retained_classes(
        prior_accepted, ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv")

    v2_rows = list(csv.DictReader((ROOT / "data/evidence_engine_v0_2/corpus_manifest.csv").open()))
    manifest_v2 = {row["document_id"]: row for row in v2_rows}
    new_ids = [row["document_id"] for row in v2_rows if row["ticker"] in NEW_TICKERS]
    new_totals, new_all = extract_docs(new_ids, manifest_v2, "local_artifact")
    selected, company_counts = [], Counter()
    for row in new_all:
        if company_counts[row["company"]] < 10:
            selected.append(row); company_counts[row["company"]] += 1
    labels = list(csv.DictReader((ROOT / "data/evidence_engine_v0_3_3/new_unseen_adjudication.csv").open()))
    if len(selected) != len(labels):
        raise RuntimeError(f"new unseen labels {len(labels)} do not cover selection {len(selected)}")
    for row, label in zip(selected, labels, strict=True):
        row.update({"manual_sanity_classification": label["classification"],
                    "severe": label["severe"], "failure_class": label["failure_class"],
                    "review_notes": label["notes"]})
    write_csv(ROOT / "data/evidence_engine_v0_3_3/new_unseen_inspected_events.csv", selected)
    new_classes = Counter(row["manual_sanity_classification"] for row in selected)
    failure_classes = Counter(row["failure_class"] for row in selected if row["failure_class"])
    severe = sum(row["severe"] == "true" for row in selected)
    attribution_errors = sum(row["failure_class"] in {"third_party_attribution", "supplier_attribution",
        "customer_attribution", "competitor_attribution", "industry_context"}
        and row["manual_sanity_classification"] == "false_positive" for row in selected)

    hashes = {"context_rule_hash": sha(ROOT / "evidence_engine_v0_3_3/events.py"),
        "entity_attribution_rule_hash": sha(ROOT / "evidence_engine_v0_3_3/events.py"),
        "target_config_hash": sha(ROOT / "config/evidence/entity_context_development_targets_v0_3_3.yaml"),
        "taxonomy_hash": sha(ROOT / "config/evidence/event_taxonomy_v0_1.yaml"),
        "parser_table_rule_hash": sha(ROOT / "evidence_engine_v0_3_2/events.py")}
    extraction_hash = hashlib.sha256("".join(hashes.values()).encode()).hexdigest()
    precision = new_classes["supported"] / max(len(selected), 1)
    technical_ready = (precision >= 0.85 and severe == 0 and attribution_errors == 0
        and prior_classes["false_positive"] <= 3
        and regression_classes["PIOTW_MISSED_EVENT"] == 0
        and sum(row["severe"] == "true" for row in regression) == 0
        and five_classes["supported"] == five_supported_total)
    status = "TECHNICALLY READY FOR FORMAL REVIEW" if technical_ready else "NOT TECHNICALLY READY FOR HUMAN REVIEW"
    results = {"version": "0.3.3", "methodological_status": "development_qa_only",
        "formal_gold": False, "admissible_for_model2_gate": False,
        "official_readiness_status": "NOT READY", "technical_status": status,
        "outcomes_accessed": False, "model2_trained": False,
        "prior_regression": {"classifications": count_classes(regression),
            "missed_ai_events": regression_classes["PIOTW_MISSED_EVENT"],
            "likely_false_positives": regression_classes["PIOTW_FALSE_POSITIVE"],
            "duplicates": regression_classes["DUPLICATE_EVENT"],
            "severe_disagreements": sum(row["severe"] == "true" for row in regression)},
        "five_document_regression": {**dict(five_totals), "supported_retained": five_classes["supported"],
            "supported_total": five_supported_total, "false_positives_retained": five_classes["false_positive"]},
        "v0_3_2_unseen_before": {"candidates": 169, "accepted_events": 64, "inspected": 30,
            "supported": 17, "obvious_false_positives": 12, "ambiguous": 1,
            "severe_false_positives": 0, "diagnostic_precision": 0.5667},
        "v0_3_2_unseen_after": {**dict(prior_totals), "inspected_prior_rows_retained": sum(prior_classes.values()),
            "supported_retained": prior_classes["supported"], "supported_total": prior_supported_total,
            "obvious_false_positives_retained": prior_classes["false_positive"],
            "ambiguous_retained": prior_classes["ambiguous"]},
        "new_unseen_sample": {"companies": len(NEW_TICKERS), "documents": len(new_ids), **dict(new_totals),
            "accepted_inspected": len(selected), "supported": new_classes["supported"],
            "obvious_false_positives": new_classes["false_positive"], "ambiguous": new_classes["ambiguous"],
            "severe_false_positives": severe, "attribution_errors": attribution_errors,
            "diagnostic_precision": precision, "failure_classes": dict(failure_classes)},
        "technical_gate": {"new_unseen_precision_min": 0.85, "passed": technical_ready},
        "extractor": {**hashes, "extraction_engine_hash": extraction_hash,
            "release_frozen": technical_ready, "git_commit": None},
        "protected_artifacts": len(verify_frozen_isolation(ROOT))}
    (ROOT / "data/derived/evidence_engine_v0_3_3_results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n")
    if protected_before != verify_frozen_isolation(ROOT): raise RuntimeError("protected artifacts changed")
    print(json.dumps(results, indent=2))


if __name__ == "__main__": main()
