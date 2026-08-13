"""Resolve the frozen restructuring validation and publish auditable metrics."""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtesting.evaluation import evaluate_binary
PREDICTIONS = ROOT / "data/derived/restructuring_predictions_pre_outcome.json"
EVIDENCE = ROOT / "data/restructuring/pre_cutoff_evidence.csv"
OUTCOMES = ROOT / "data/restructuring/outcomes.csv"
DATABASE = ROOT / "data/derived/restructuring_validation.sqlite3"
OUTPUT = ROOT / "data/derived/restructuring_validation_results.json"


def _rule_scores(features: dict[str, dict[str, float]]) -> tuple[list[float], list[float]]:
    # Deterministic 0/1 comparators. Their numeric thresholds were formalised only
    # after outcome review, so they are sensitivity analyses, not gate-eligible.
    financial = [
        float(row["margin_pressure"] >= 0.6 and row["cash_pressure"] >= 0.6)
        for row in features.values()
    ]
    language = [float(row["pressure_language"] >= 0.5) for row in features.values()]
    return financial, language


def build() -> dict:
    prediction_doc = json.loads(PREDICTIONS.read_text())
    predictions = prediction_doc["predictions"]
    outcomes_by_id = {row["prediction_id"]: row for row in csv.DictReader(OUTCOMES.open())}
    evidence_rows = list(csv.DictReader(EVIDENCE.open()))
    feature_by_key = {
        (row["ticker"], row["cutoff"]): {
            name: float(row[name])
            for name in ("pressure_language", "margin_pressure", "cash_pressure", "contrary_strength")
        }
        for row in evidence_rows
    }
    if set(outcomes_by_id) != {row["prediction_id"] for row in predictions}:
        raise ValueError("outcomes must resolve every frozen prediction exactly once")

    ordered_outcomes = [outcomes_by_id[row["prediction_id"]] for row in predictions]
    if any(row["outcome_status"] not in {"positive", "negative", "ambiguous"} for row in ordered_outcomes):
        raise ValueError("invalid outcome status")
    scored = [index for index, row in enumerate(ordered_outcomes) if row["outcome_status"] != "ambiguous"]
    probabilities = [predictions[index]["probability"] for index in scored]
    actuals = [int(ordered_outcomes[index]["occurred"]) for index in scored]
    prior = [float(prediction_doc["prior"])] * len(scored)
    ordered_features = {
        row["prediction_id"]: feature_by_key[(row["ticker"], row["information_cutoff"])]
        for row in predictions
    }
    financial_all, language_all = _rule_scores(ordered_features)
    financial = [financial_all[index] for index in scored]
    language = [language_all[index] for index in scored]

    companies = [predictions[index]["ticker"] for index in scored]
    loo = []
    for index, company in enumerate(companies):
        others = [outcome for other, outcome in zip(companies, actuals) if other != company]
        loo.append(sum(others) / len(others))

    evaluations = {
        "piotw": asdict(evaluate_binary(probabilities, actuals)),
        "constant_12_percent": asdict(evaluate_binary(prior, actuals)),
        "leave_one_company_out": asdict(evaluate_binary(loo, actuals)),
        "financial_stress_rule": asdict(evaluate_binary(financial, actuals)),
        "disclosure_language_rule": asdict(evaluate_binary(language, actuals)),
    }
    event_rows = [row for row in ordered_outcomes if row["occurred"] == "1"]
    lead_times = [
        (date.fromisoformat(row["outcome_date"]) - date.fromisoformat(row["cutoff"])).days
        for row in event_rows
    ]
    sorted_leads = sorted(lead_times)
    median_lead = (sorted_leads[len(sorted_leads) // 2 - 1] + sorted_leads[len(sorted_leads) // 2]) / 2
    if len(sorted_leads) % 2:
        median_lead = sorted_leads[len(sorted_leads) // 2]

    piotw_brier = evaluations["piotw"]["brier_score"]
    frozen_comparator_briers = {"constant_12_percent": evaluations["constant_12_percent"]["brier_score"]}
    quantitative_gate_candidate = all(piotw_brier < value for value in frozen_comparator_briers.values()) and (
        evaluations["piotw"]["top_quintile_lift"] > 1 or median_lead >= 90
    )
    errors = []
    for prediction, outcome in zip(predictions, ordered_outcomes):
        predicted = prediction["probability"] >= 0.5
        actual = outcome["occurred"] == "1"
        if predicted != actual:
            errors.append({
                "prediction_id": prediction["prediction_id"], "ticker": prediction["ticker"],
                "probability": prediction["probability"], "actual": int(actual),
                "error": "false_positive" if predicted else "false_negative",
            })

    outcome_hash = hashlib.sha256(OUTCOMES.read_bytes()).hexdigest()
    result = {
        "status": "resolved single-researcher feasibility validation",
        "prediction_model": prediction_doc["model_version"],
        "prediction_count": len(predictions), "scored_count": len(scored),
        "positive_count": sum(actuals), "outcome_file_sha256": outcome_hash,
        "evaluations": evaluations,
        "lead_time_days": {"values": lead_times, "median": median_lead},
        "threshold_errors": errors,
        "occasions": [
            {
                "prediction_id": prediction["prediction_id"], "company": prediction["company"],
                "ticker": prediction["ticker"], "cutoff": prediction["information_cutoff"],
                "probability": prediction["probability"], "confidence": prediction["confidence"],
                "outcome": int(outcome["occurred"]), "outcome_status": outcome["outcome_status"],
                "outcome_date": outcome["outcome_date"], "source_url": outcome["source_url"],
            }
            for prediction, outcome in zip(predictions, ordered_outcomes)
        ],
        "gate": {
            "passed": False,
            "status": "indeterminate_due_protocol_deviation",
            "quantitative_candidate_met": quantitative_gate_candidate,
            "eligible_comparators": list(frozen_comparator_briers),
            "decision": "do not expand yet; freeze numeric comparator rules and obtain independent outcome adjudication",
            "limitation": "Only the constant prior was fully specified before outcome review; the declared simple-rule comparators were not numerically frozen.",
        },
        "protocol_deviations": [
            "Financial-stress and disclosure-language rule thresholds were not numerically frozen before outcome review; their results are sensitivity analyses and excluded from the formal gate.",
            "Outcome adjudication was completed by one researcher rather than independently duplicated.",
            "Pre-cutoff evidence hashes cover the structured extraction, URL and features, not a locally archived full source document.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")

    with sqlite3.connect(DATABASE) as connection:
        connection.executescript("""
          DROP TABLE IF EXISTS validation_metrics;
          DROP TABLE IF EXISTS validation_outcomes;
          CREATE TABLE validation_outcomes(
            prediction_id TEXT PRIMARY KEY REFERENCES predictions(prediction_id),
            outcome_status TEXT NOT NULL, occurred INTEGER NOT NULL,
            outcome_date TEXT, source_url TEXT NOT NULL, resolution_note TEXT NOT NULL,
            exclusion_applied TEXT NOT NULL, review_status TEXT NOT NULL,
            outcome_file_sha256 TEXT NOT NULL
          );
          CREATE TABLE validation_metrics(
            metric_set TEXT PRIMARY KEY, results_json TEXT NOT NULL,
            outcome_file_sha256 TEXT NOT NULL
          );
          CREATE TRIGGER validation_outcomes_no_update BEFORE UPDATE ON validation_outcomes
            BEGIN SELECT RAISE(ABORT, 'validation outcomes are immutable'); END;
          CREATE TRIGGER validation_outcomes_no_delete BEFORE DELETE ON validation_outcomes
            BEGIN SELECT RAISE(ABORT, 'validation outcomes are immutable'); END;
        """)
        for row in ordered_outcomes:
            connection.execute("INSERT INTO validation_outcomes VALUES(?,?,?,?,?,?,?,?,?)", (
                row["prediction_id"], row["outcome_status"], int(row["occurred"]),
                row["outcome_date"] or None, row["source_url"], row["resolution_note"],
                row["exclusion_applied"], row["review_status"], outcome_hash,
            ))
        connection.execute("INSERT INTO validation_metrics VALUES(?,?,?)", (
            "restructuring-validation-v1", json.dumps(result, sort_keys=True), outcome_hash))
    print(f"resolved {len(scored)} predictions; formal gate passed: False")
    return result


if __name__ == "__main__":
    build()
