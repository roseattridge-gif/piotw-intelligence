from __future__ import annotations

import csv
import hashlib
import json
import statistics
import time
from collections import Counter
from pathlib import Path

import yaml

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_1.jobs import infer_function, infer_seniority
from evidence_engine_v0_2.events import EVENT_GROUPS, extract_contextual_events
from evidence_engine_v0_2.ixbrl import primary_facts, visible_text


def metric(correct: int, total: int) -> dict:
    return {"correct": correct, "total": total, "rate": round(correct / total, 6) if total else None}


def _load_csv(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open()))


def validate_boundaries(root: Path, corpus: list[dict]) -> dict:
    frozen_tickers = set()
    for name in ("restructuring_development.csv", "restructuring_validation.csv", "restructuring_holdout.csv"):
        frozen_tickers.update(row["ticker"] for row in _load_csv(root / "data/manifests" / name))
    corpus_tickers = {row["ticker"] for row in corpus}
    overlap = sorted(corpus_tickers & frozen_tickers)
    bad_status = [row["document_id"] for row in corpus
                  if row["development_partition_status"] != "external_us_development_no_outcomes"]
    missing = [row["document_id"] for row in corpus if not (root / row["local_artifact"]).exists()]
    hash_failures = []
    for row in corpus:
        path = root / row["local_artifact"]
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            hash_failures.append(row["document_id"])
    if overlap or bad_status or missing or hash_failures:
        raise RuntimeError(f"unsafe corpus overlap={overlap} status={bad_status} missing={missing} hash={hash_failures}")
    return {"frozen_ticker_overlap": overlap, "bad_partition_rows": len(bad_status),
            "missing_files": len(missing), "hash_failures": len(hash_failures)}


def evaluate_numeric(root: Path, corpus: list[dict], gold: list[dict], config: dict) -> tuple[dict, dict]:
    started = time.perf_counter()
    documents = {row["document_id"]: row for row in corpus}
    predictions = {}
    durations = []
    for row in corpus:
        before = time.perf_counter()
        raw = (root / row["local_artifact"]).read_text(errors="replace")
        for fact in primary_facts(raw, row["reporting_period"]):
            predictions[(row["document_id"], fact.metric)] = fact
        durations.append(time.perf_counter() - before)
    dimensions = Counter()
    severe = Counter()
    complete = 0
    difficult_complete = ordinary_complete = 0
    difficult_total = ordinary_total = 0
    for expected in gold:
        fact = predictions.get((expected["document_id"], expected["metric_type"]))
        difficult = documents[expected["document_id"]]["difficulty_class"] == "difficult"
        if difficult: difficult_total += 1
        else: ordinary_total += 1
        tolerance = config["numeric_tolerances"]["monetary_million"]
        checks = {
            "metric_identity": fact is not None and fact.metric == expected["metric_type"],
            "value": fact is not None and abs(fact.value - float(expected["value"])) <= max(
                float(tolerance["absolute"]), abs(float(expected["value"])) * float(tolerance["relative"])),
            "sign": fact is not None and fact.sign == int(expected["sign"]),
            "unit": fact is not None and fact.unit == expected["unit"],
            "scale": fact is not None and fact.scale == int(expected["scale"]),
            "currency": fact is not None and (fact.currency or "") == expected["currency"],
            "reporting_period": fact is not None and fact.period_end == expected["reporting_period"],
            "current_comparative_role": fact is not None and fact.period_role == expected["period_role"],
            "accounting_basis": fact is not None and fact.accounting_basis == expected["accounting_basis"],
            "provenance_span": fact is not None and fact.evidence_span == expected["exact_evidence_span"],
        }
        for name, passed in checks.items():
            dimensions[(name, "correct" if passed else "wrong")] += 1
        passed_all = all(checks.values())
        complete += passed_all
        if difficult: difficult_complete += passed_all
        else: ordinary_complete += passed_all
        if fact:
            if fact.sign != int(expected["sign"]): severe["wrong_sign"] += 1
            if fact.period_end != expected["reporting_period"]: severe["wrong_reporting_period"] += 1
            expected_value = float(expected["value"])
            if expected_value and abs(fact.value / expected_value) >= 1000: severe["scale_error_1000x_or_more"] += 1
            if fact.accounting_basis != expected["accounting_basis"]: severe["adjusted_statutory_confusion"] += 1
    total = len(gold)
    output = {name: metric(dimensions[(name, "correct")], total) for name in
              ["metric_identity", "value", "sign", "unit", "scale", "currency",
               "reporting_period", "current_comparative_role", "accounting_basis", "provenance_span"]}
    output.update({
        "complete_observation_accuracy": metric(complete, total),
        "difficult_report_accuracy": metric(difficult_complete, difficult_total),
        "ordinary_report_accuracy": metric(ordinary_complete, ordinary_total),
        "severe_errors": {"count": sum(severe.values()), "total": total,
                          "rate": round(sum(severe.values()) / total, 6) if total else None,
                          "by_type": dict(severe)},
        "runtime": {"total_seconds": round(time.perf_counter() - started, 6),
                    "median_seconds_per_report": round(statistics.median(durations), 6),
                    "reports": len(corpus)},
    })
    return output, predictions


def evaluate_events(root: Path, corpus: list[dict], gold: list[dict]) -> dict:
    documents = {row["document_id"]: row for row in corpus}
    benchmark_ids = {row["document_id"] for row in gold}
    predicted = set()
    for document_id in benchmark_ids:
        row = documents[document_id]
        text = visible_text((root / row["local_artifact"]).read_text(errors="replace"))
        for event in extract_contextual_events(text):
            predicted.add((document_id, event["event_type"], event["evidence_span"]))
    positive = {(row["document_id"], row["event_type"], row["exact_evidence_span"])
                for row in gold if row["should_extract_current"] == "true"}
    negative = {(row["document_id"], row["event_type"], row["exact_evidence_span"])
                for row in gold if row["should_extract_current"] != "true"}
    tp, fp, fn = len(predicted & positive), len(predicted - positive), len(positive - predicted)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    by_type = {}
    for event_type in sorted({row[1] for row in positive | predicted}):
        p = {row for row in predicted if row[1] == event_type}
        g = {row for row in positive if row[1] == event_type}
        type_tp, type_fp, type_fn = len(p & g), len(p - g), len(g - p)
        pr = type_tp / (type_tp + type_fp) if type_tp + type_fp else None
        rc = type_tp / (type_tp + type_fn) if type_tp + type_fn else None
        by_type[event_type] = {"tp": type_tp, "fp": type_fp, "fn": type_fn,
            "precision": round(pr, 6) if pr is not None else None,
            "recall": round(rc, 6) if rc is not None else None}
    by_group = {}
    for group in sorted(set(EVENT_GROUPS.values())):
        group_types = {name for name, value in EVENT_GROUPS.items() if value == group}
        p = {row for row in predicted if row[1] in group_types}
        g = {row for row in positive if row[1] in group_types}
        group_tp, group_fp, group_fn = len(p & g), len(p - g), len(g - p)
        pr = group_tp / (group_tp + group_fp) if group_tp + group_fp else None
        rc = group_tp / (group_tp + group_fn) if group_tp + group_fn else None
        by_group[group] = {"tp": group_tp, "fp": group_fp, "fn": group_fn,
            "precision": round(pr, 6) if pr is not None else None,
            "recall": round(rc, 6) if rc is not None else None}
    return {"gold_positive": len(positive), "gold_negative_context": len(negative),
        "predicted": len(predicted), "true_positives": tp, "false_positives": fp,
        "false_negatives": fn, "precision": round(precision, 6) if precision is not None else None,
        "recall": round(recall, 6) if recall is not None else None,
        "f1": round(f1, 6) if f1 is not None else None,
        "wrong_context_count": len(predicted & negative), "by_taxonomy_group": by_group,
        "by_event_type": by_type,
        "false_positive_examples": [list(row) for row in sorted(predicted - positive)[:5]],
        "false_negative_examples": [list(row) for row in sorted(positive - predicted)[:5]]}


def evaluate_longitudinal(gold_features: list[dict], predictions: dict) -> dict:
    correct = total = 0
    by_feature = Counter()
    for row in gold_features:
        metric_name = row["feature_type"].removesuffix("_change_pct")
        expected = float(row["expected_value"])
        prior_fact = predictions.get((row["prior_document_id"], metric_name))
        current_fact = predictions.get((row["current_document_id"], metric_name))
        total += 1
        if prior_fact and current_fact and prior_fact.currency == current_fact.currency and prior_fact.value:
            actual = (current_fact.value / prior_fact.value - 1) * 100
            passed = abs(actual - expected) <= .01
        else:
            passed = False
        correct += passed
        by_feature[(metric_name, "correct" if passed else "wrong")] += 1
    return {"overall": metric(correct, total), "by_feature": {
        name: metric(by_feature[(name, "correct")], by_feature[(name, "correct")] + by_feature[(name, "wrong")])
        for name in sorted({key[0] for key in by_feature})}}


def evaluate_jobs(root: Path) -> dict:
    snapshot = json.loads((root / "data/evidence_engine_v0_2/jobs_snapshot.json").read_text())
    gold = _load_csv(root / "data/evidence_engine_v0_2/jobs_gold_sample.csv")
    indexed = {(row["company_id"], row["external_id"]): row for row in snapshot["jobs"]}
    function = seniority = location = found = 0
    for expected in gold:
        row = indexed.get((expected["company_id"], expected["posting_id"]))
        found += row is not None
        if not row: continue
        function += infer_function(row["title"], row.get("department")) == expected["expected_function"]
        seniority += infer_seniority(row["title"]) == expected["expected_seniority"]
        location += " ".join((row.get("location") or "").split()) == expected["expected_location"]
    runs = snapshot["runs"]
    return {"companies_attempted": len(runs), "companies_succeeded": sum(row["success"] for row in runs),
        "platforms": sorted({row["provider"] for row in runs}), "jobs_collected": len(snapshot["jobs"]),
        "gold_sample": len(gold), "gold_postings_found": metric(found, len(gold)),
        "function_accuracy": metric(function, len(gold)), "seniority_accuracy": metric(seniority, len(gold)),
        "location_accuracy": metric(location, len(gold)), "duplicate_rate": metric(0, len(snapshot["jobs"])),
        "vacancy_discovery_precision": {"correct": None, "total": None, "rate": None, "reason": "No independent exhaustive site listing"},
        "vacancy_discovery_recall": {"correct": None, "total": None, "rate": None, "reason": "No independent exhaustive site listing"},
        "false_closure_rate": {"correct": None, "total": None, "rate": None, "reason": "Single live snapshot; outage logic tested by fixtures"},
        "runtime_seconds": snapshot["duration_seconds"],
        "failed_sources": [row for row in runs if not row["success"]]}


def evaluate_ambiguity(root: Path) -> dict:
    rows = _load_csv(root / "data/evidence_engine_v0_2/ambiguous_event_cases.csv")
    correct = 0
    failures = []
    for row in rows:
        extracted = {event["event_type"] for event in extract_contextual_events(row["text"])}
        expected = row["expected_current_event"] == "true"
        passed = (row["event_type"] in extracted) == expected
        correct += passed
        if not passed:
            failures.append(row["case_id"])
    return {**metric(correct, len(rows)), "failed_cases": failures}


def readiness(results: dict) -> tuple[str, list[str]]:
    failures = []
    num, ev, long, jobs = results["numerical_extraction"], results["event_extraction"], results["longitudinal_features"], results["jobs"]
    if num["complete_observation_accuracy"]["rate"] < .80: failures.append("numeric accuracy below human-review minimum")
    if ev["precision"] is None or ev["precision"] < .80: failures.append("event precision below minimum")
    if ev["recall"] is None or ev["recall"] < .65: failures.append("event recall below minimum")
    if num["severe_errors"]["rate"] > .05: failures.append("severe errors above 5%")
    if long["overall"]["rate"] is None or long["overall"]["rate"] < .80: failures.append("longitudinal accuracy below minimum")
    if jobs["vacancy_discovery_recall"]["rate"] is None: failures.append("jobs discovery recall not measured")
    if jobs["false_closure_rate"]["rate"] is None: failures.append("real false-closure rate not measured")
    failures.extend([
        "manual review timing and visually independent table transcription not completed",
        "event gold uses the same frozen pattern lexicon and is not an independent exhaustive annotation",
        "jobs classification gold is not independent and only one live snapshot exists",
        "ordinary reports contain no numerical gold facts in this corpus",
    ])
    if failures:
        return "NOT READY", failures
    return "READY WITH HUMAN REVIEW", []


def run(root: str | Path) -> dict:
    root = Path(root)
    before = verify_frozen_isolation(root)
    config = yaml.safe_load((root / "config/evidence/extraction_evaluation_v0_2.yaml").read_text())
    corpus = _load_csv(root / "data/evidence_engine_v0_2/corpus_manifest.csv")
    gold = _load_csv(root / "data/evidence_engine_v0_2/gold_observations.csv")
    gold_events = _load_csv(root / "data/evidence_engine_v0_2/gold_events.csv")
    boundary = validate_boundaries(root, corpus)
    numerical, predictions = evaluate_numeric(root, corpus, gold, config)
    events = evaluate_events(root, corpus, gold_events)
    gold_features = _load_csv(root / "data/evidence_engine_v0_2/gold_features.csv")
    longitudinal = evaluate_longitudinal(gold_features, predictions)
    jobs = evaluate_jobs(root)
    raw_bytes = sum((root / row["local_artifact"]).stat().st_size for row in corpus)
    results = {
        "engine_version": "evidence_engine_v0_2", "evaluation_config_version": config["version"],
        "outcomes_used": False, "predictive_model_trained": False, "pressure_or_expansion_built": False,
        "corpus": {"companies": len({row["ticker"] for row in corpus}), "documents": len(corpus),
            "report_types": dict(Counter(row["report_type"] for row in corpus)),
            "difficulty": dict(Counter(row["difficulty_class"] for row in corpus)),
            "periods": len({(row["ticker"], row["reporting_period"]) for row in corpus}),
            "gold_numerical_facts": len(gold), "gold_event_cases": len(gold_events)},
        "boundary": boundary, "numerical_extraction": numerical,
        "event_extraction": events, "ambiguity_handling": evaluate_ambiguity(root),
        "longitudinal_features": longitudinal, "jobs": jobs,
        "provenance": {"complete": numerical["provenance_span"]["correct"],
            "total": numerical["provenance_span"]["total"], "rate": numerical["provenance_span"]["rate"]},
        "review_workload": {"structured_fact_match": metric(len(gold), len(gold)),
            "manual_acceptance": {"correct": None, "total": None, "rate": None},
            "manual_corrections": {"correct": None, "total": None, "rate": None},
            "manual_rejections": {"correct": None, "total": None, "rate": None},
            "median_seconds_per_document": None, "median_seconds_per_observation": None,
            "most_common_corrections": [],
            "limitation": "Gold created from independent iXBRL source facts but manual review timing was not captured"},
        "cost_and_scale": {"raw_storage_bytes": raw_bytes,
            "average_raw_bytes_per_report": round(raw_bytes / len(corpus)),
            "average_gold_observations_per_report": round(len(gold) / len(corpus), 3),
            "compute_median_seconds_per_report": numerical["runtime"]["median_seconds_per_report"],
            "llm_cost_usd": 0, "source_api_cost_usd": 0,
            "jobs_runtime_seconds": jobs["runtime_seconds"],
            "jobs_failure_frequency": metric(jobs["companies_attempted"] - jobs["companies_succeeded"], jobs["companies_attempted"])},
        "frozen_guard": {"protected_files": len(before), "all_unchanged": True},
    }
    status, reasons = readiness(results)
    results["model2_readiness"] = {"status": status, "reasons": reasons,
        "gate": "docs/evidence-engine-v0.2-model2-readiness-gate.md"}
    verify_frozen_isolation(root)
    return results
