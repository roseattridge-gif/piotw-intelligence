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
from evidence_engine_v0_3.ai_finops import compare_events, count_classes, validate_import
from evidence_engine_v0_3_4.events import extract_contextual_events_v034, extract_event_pipeline
from evidence_engine_v0_3_4.semantic import DeterministicSemanticVerifier

NEW_TICKERS = {"MMM", "INTC", "MSFT"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError(f"refusing to write empty CSV: {path}")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def build_benchmark() -> tuple[list[dict], str]:
    rows: list[dict] = []
    sources = [
        ("0.3.3_new_unseen", "data/evidence_engine_v0_3_3/new_unseen_inspected_events.csv"),
        ("0.3.2_previous_unseen", "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv"),
        ("0.3.2_five_document", "data/evidence_engine_v0_3_2/five_document_accepted_events.csv"),
    ]
    for source_name, relative in sources:
        for index, row in enumerate(csv.DictReader((ROOT / relative).open()), 1):
            classification = row.get("manual_sanity_classification", "supported")
            expected = {"supported": "accept", "false_positive": "reject",
                        "ambiguous": "ambiguous"}.get(classification, "ambiguous")
            rows.append({"case_id": f"{source_name}-{index:03d}", "benchmark_source": source_name,
                "document_id": row["document_id"], "company": row.get("company", ""),
                "candidate_event_type": row["event_type"], "source_context": row["source_span"],
                "expected_decision": expected, "expected_event_type": row["event_type"] if expected == "accept" else "",
                "expected_subject": row.get("subject_type", "target_company"),
                "expected_status": row.get("factual_status", row.get("event_status", "")),
                "failure_class": row.get("failure_class", ""), "development_only": "true",
                "formal_gold": "false", "admissible_for_model2_gate": "false"})
    regression_sources = [
        ("0.3.1_78_case", "data/evidence_engine_v0_3_1/event_context_regression_cases.csv",
         "piotw_proposed_event", "diagnostic_expected_classification", "expected_context_status"),
        ("0.3.2_table_historical", "data/evidence_engine_v0_3_2/table_historical_regression_cases.csv",
         "candidate_event_type", "expected_disposition", "historical_current_status"),
        ("0.3.3_entity_risk", "data/evidence_engine_v0_3_3/entity_risk_context_regression_cases.csv",
         "event_candidate", "expected_disposition", "actual_hypothetical_status"),
    ]
    for source_name, relative, event_field, disposition_field, status_field in regression_sources:
        for index, row in enumerate(csv.DictReader((ROOT / relative).open()), 1):
            span = row.get("source_span") or row.get("raw_extracted_span") or ""
            disposition = row[disposition_field]
            expected = {"accepted": "accept", "rejected": "reject",
                        "ambiguous": "ambiguous"}.get(disposition, disposition)
            rows.append({"case_id": f"{source_name}-{index:03d}", "benchmark_source": source_name,
                "document_id": row["document_id"], "company": "", "candidate_event_type": row[event_field],
                "source_context": span, "expected_decision": expected,
                "expected_event_type": row[event_field] if expected == "accept" else "",
                "expected_subject": row.get("subject_type", ""), "expected_status": row.get(status_field, ""),
                "failure_class": row.get("failure_class", row.get("root_cause_category", "")),
                "development_only": "true", "formal_gold": "false",
                "admissible_for_model2_gate": "false"})
    output = ROOT / "data/evidence_engine_v0_3_4/semantic_event_benchmark.csv"
    write_csv(output, rows)
    digest = sha(output)
    freeze = {"version": "0.3.4", "sha256": digest, "rows": len(rows),
        "methodological_status": "development_only", "formal_gold": False,
        "admissible_for_model2_gate": False}
    (output.parent / "semantic_event_benchmark.freeze.json").write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    return rows, digest


def run_documents(rows: list[dict], *, artifact_field: str) -> tuple[Counter, list[dict]]:
    totals: Counter = Counter(); accepted: list[dict] = []
    verifier = DeterministicSemanticVerifier()
    for row in rows:
        text = visible_text((ROOT / row[artifact_field]).read_text(errors="ignore"))
        pipeline = extract_event_pipeline(text, target_company=row["company"],
            publication_date=row["publication_date"], reporting_period=row["reporting_period"],
            verifier=verifier)
        totals.update({"documents": 1, "candidates": len(pipeline["candidates"]),
            "deterministic_rejects": len(pipeline["event_rejections"]) - len(pipeline["semantic_rejections"]),
            "semantic_calls": pipeline["semantic_calls"], "accepted": len(pipeline["accepted_events"]),
            "semantic_rejected": len(pipeline["semantic_rejections"]),
            "ambiguous": len(pipeline["semantic_ambiguous"]),
            "input_tokens": sum(x["semantic_input_tokens"] for x in pipeline["semantic_assessments"]),
            "output_tokens": sum(x["semantic_output_tokens"] for x in pipeline["semantic_assessments"]),
            "latency_ms": sum(x["semantic_latency_ms"] for x in pipeline["semantic_assessments"])})
        for event in pipeline["accepted_events"]:
            accepted.append({"document_id": row["document_id"], "company": row["company"],
                "event_type": event["event_type"], "source_span": event["source_span"],
                "reason_code": event["semantic_reason_code"], "support_span": event["semantic_exact_support_span"]})
    return totals, accepted


def retained_label_summary(accepted: list[dict], labelled_path: Path) -> dict:
    keys = {(row["document_id"], row["event_type"], row["source_span"]) for row in accepted}
    labelled = list(csv.DictReader(labelled_path.open()))
    retained = [row for row in labelled
                if (row["document_id"], row["event_type"], row["source_span"]) in keys]
    classes = Counter(row["manual_sanity_classification"] for row in retained)
    supported_total = sum(row["manual_sanity_classification"] == "supported" for row in labelled)
    return {"labelled_rows": len(labelled), "retained_rows": len(retained),
        "supported_retained": classes["supported"], "supported_total": supported_total,
        "supported_retention": classes["supported"] / max(supported_total, 1),
        "false_positives_retained": classes["false_positive"],
        "ambiguous_retained": classes["ambiguous"]}


def main() -> None:
    protected_before = verify_frozen_isolation(ROOT)
    benchmark, benchmark_hash = build_benchmark()
    imported = validate_import(ROOT)
    six_comparison = compare_events(ROOT, imported, extractor=extract_contextual_events_v034)
    six_classes = Counter(row["classification"] for row in six_comparison)
    manifest = list(csv.DictReader((ROOT / "data/evidence_engine_v0_2/corpus_manifest.csv").open()))

    known_ids = {row["document_id"] for row in benchmark}
    unseen_rows = [row for row in manifest if row["ticker"] in NEW_TICKERS and row["document_id"] not in known_ids]
    unseen_totals, unseen_accepted = run_documents(unseen_rows, artifact_field="local_artifact")
    gm_rows = [row for row in manifest if row["ticker"] in {"GM", "HON", "HPQ"}]
    gm_totals, gm_accepted = run_documents(gm_rows, artifact_field="local_artifact")
    gm_summary = retained_label_summary(
        gm_accepted, ROOT / "data/evidence_engine_v0_3_3/new_unseen_inspected_events.csv")
    prior_ids = {row["document_id"] for row in csv.DictReader(
        (ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv").open())}
    prior_rows = [row for row in imported["corpus"] if row["document_id"] in prior_ids]
    prior_totals, prior_accepted = run_documents(prior_rows, artifact_field="source_artifact")
    prior_summary = retained_label_summary(
        prior_accepted, ROOT / "data/evidence_engine_v0_3_2/second_unseen_inspected_events.csv")
    selected: list[dict] = []; company_counts: Counter = Counter()
    for row in unseen_accepted:
        if company_counts[row["company"]] < 10:
            selected.append(row); company_counts[row["company"]] += 1
    output = ROOT / "data/evidence_engine_v0_3_4/new_unseen_semantic_inspection.csv"
    labels_path = ROOT / "data/evidence_engine_v0_3_4/new_unseen_semantic_adjudication.csv"
    labels = list(csv.DictReader(labels_path.open())) if labels_path.exists() else []
    for index, row in enumerate(selected):
        label = labels[index] if index < len(labels) else {}
        row.update({"diagnostic_classification": label.get("classification", "not_yet_inspected"),
            "severe": label.get("severe", ""), "failure_class": label.get("failure_class", ""),
            "notes": label.get("notes", "")})
    write_csv(output, selected)
    classes = Counter(row["diagnostic_classification"] for row in selected)
    severe = sum(row["severe"] == "true" for row in selected)
    inspected = len(selected) and "not_yet_inspected" not in classes
    precision = classes["supported"] / len(selected) if inspected else None
    provenance = sum(bool(row["support_span"] and row["support_span"] in row["source_span"])
                     for row in selected) / max(len(selected), 1)
    model_backed = False
    technical_ready = bool(model_backed and inspected and precision is not None and precision >= .85
        and severe == 0 and provenance == 1)
    status = "TECHNICALLY READY FOR BLINDED CROSS-REVIEW" if technical_ready else "NOT TECHNICALLY READY"

    results = {"version": "0.3.4", "methodological_status": "development_qa_only",
        "formal_gold": False, "admissible_for_model2_gate": False,
        "official_readiness_status": "NOT READY", "technical_status": status,
        "outcomes_accessed": False, "model2_trained": False,
        "semantic_benchmark": {"rows": len(benchmark), "sha256": benchmark_hash},
        "six_document_ai_diagnostic": {"classifications": count_classes(six_comparison),
            "missed_ai_events": six_classes["PIOTW_MISSED_EVENT"],
            "likely_false_positives": six_classes["PIOTW_FALSE_POSITIVE"],
            "duplicates": six_classes["DUPLICATE_EVENT"],
            "severe_disagreements": sum(row.get("severe") == "true" for row in six_comparison)},
        "semantic_verifier": {"provider": "deterministic_semantic_development",
            "model": "semantic-rules-v0.3.4", "prompt_version": "semantic-event-v0.3.4",
            "model_backed": model_backed, "actual_model_calls": 0},
        "previous_unseen": {"before_precision": 0.5667, **dict(prior_totals), **prior_summary},
        "gm_honeywell_hp": {"before_precision": 0.4333, **dict(gm_totals), **gm_summary},
        "new_unseen_sample": {"companies": len({row["company"] for row in unseen_rows}),
            **dict(unseen_totals), "accepted_inspected": len(selected) if inspected else 0,
            "supported": classes["supported"], "false_positives": classes["false_positive"],
            "diagnostic_ambiguous": classes["ambiguous"], "severe_false_positives": severe,
            "diagnostic_precision": precision, "provenance_completeness": provenance},
        "technical_gate": {"model_backed_unseen_required": True, "passed": technical_ready},
        "cost": {"actual_api_cost_usd": 0, "observed_model_latency_ms": None,
            "semantic_calls_per_report": unseen_totals["semantic_calls"] / max(unseen_totals["documents"], 1),
            "estimated_tokens_per_call": {"input": 600, "output": 120},
            "estimated_cost_usd_per_call": 0.00039,
            "estimated_cost_usd_per_report": 0.00806},
        "hashes": {"semantic_prompt": sha(ROOT / "config/evidence/semantic_event_prompt_v0_3_4.txt"),
            "semantic_config": sha(ROOT / "config/evidence/semantic_verifier_v0_3_4.yaml"),
            "semantic_schema_and_provider": sha(ROOT / "evidence_engine_v0_3_4/semantic.py"),
            "final_decision_logic": sha(ROOT / "evidence_engine_v0_3_4/events.py"),
            "taxonomy": sha(ROOT / "config/evidence/event_taxonomy_v0_1.yaml")},
        "release": {"frozen": technical_ready, "reason": (
            "gate passed" if technical_ready else "No authorised model-backed unseen evaluation was completed")},
        "protected_artifacts": len(verify_frozen_isolation(ROOT))}
    derived = ROOT / "data/derived/evidence_engine_v0_3_4_results.json"
    derived.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    if protected_before != verify_frozen_isolation(ROOT):
        raise RuntimeError("protected artefacts changed")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
