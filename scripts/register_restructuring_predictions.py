"""Build and lock the pre-outcome restructuring validation predictions."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/restructuring/pre_cutoff_evidence.csv"
DATABASE = ROOT / "data/derived/restructuring_validation.sqlite3"
OUTPUT = ROOT / "data/derived/restructuring_predictions_pre_outcome.json"
MODEL_VERSION = "restructuring-rules-1.0.0"
PRIOR = 0.12
WEIGHTS = {"pressure_language": 1.40, "margin_pressure": 0.90,
           "cash_pressure": 0.70, "contrary_strength": -0.80}


def probability(row: dict[str, str]) -> tuple[float, dict[str, float]]:
    contributions = {name: WEIGHTS[name] * float(row[name]) for name in WEIGHTS}
    logit = math.log(PRIOR / (1 - PRIOR)) + sum(contributions.values())
    return 1 / (1 + math.exp(-logit)), contributions


def build() -> dict:
    rows = list(csv.DictReader(INPUT.open()))
    if len(rows) != 20 or len({(r["ticker"], r["cutoff"]) for r in rows}) != 20:
        raise ValueError("expected exactly 20 unique prediction occasions")
    for row in rows:
        if row["available_at"] > row["cutoff"]:
            raise ValueError(f"future evidence at {row['evidence_id']}")

    if DATABASE.exists():
        DATABASE.unlink()
    connection = sqlite3.connect(DATABASE)
    connection.executescript("""
      CREATE TABLE evidence(
        evidence_id TEXT PRIMARY KEY, company TEXT NOT NULL, ticker TEXT NOT NULL,
        cutoff TEXT NOT NULL, available_at TEXT NOT NULL CHECK(available_at <= cutoff),
        source_title TEXT NOT NULL, source_url TEXT NOT NULL, observation TEXT NOT NULL,
        snapshot_hash TEXT NOT NULL UNIQUE, features_json TEXT NOT NULL,
        exclusion TEXT NOT NULL, review_status TEXT NOT NULL
      );
      CREATE TABLE model_versions(
        model_version TEXT PRIMARY KEY, target TEXT NOT NULL, horizon_months INTEGER NOT NULL,
        prior REAL NOT NULL, weights_json TEXT NOT NULL, frozen_at TEXT NOT NULL
      );
      CREATE TABLE predictions(
        prediction_id TEXT PRIMARY KEY, company TEXT NOT NULL, ticker TEXT NOT NULL,
        target TEXT NOT NULL, horizon_months INTEGER NOT NULL, information_cutoff TEXT NOT NULL,
        probability REAL NOT NULL CHECK(probability BETWEEN 0 AND 1), confidence REAL NOT NULL,
        model_version TEXT NOT NULL REFERENCES model_versions(model_version),
        evidence_ids_json TEXT NOT NULL, feature_contributions_json TEXT NOT NULL,
        evidence_snapshot_hash TEXT NOT NULL, created_at TEXT NOT NULL,
        UNIQUE(ticker, target, information_cutoff, model_version)
      );
      CREATE TRIGGER predictions_no_update BEFORE UPDATE ON predictions
        BEGIN SELECT RAISE(ABORT, 'validation predictions are immutable'); END;
      CREATE TRIGGER predictions_no_delete BEFORE DELETE ON predictions
        BEGIN SELECT RAISE(ABORT, 'validation predictions are immutable'); END;
    """)
    frozen = datetime.now(timezone.utc).isoformat()
    connection.execute("INSERT INTO model_versions VALUES(?,?,?,?,?,?)", (
        MODEL_VERSION, "restructuring_announced", 12, PRIOR,
        json.dumps(WEIGHTS, sort_keys=True), frozen))
    predictions = []
    for row in rows:
        features = {name: float(row[name]) for name in WEIGHTS}
        snapshot_hash = hashlib.sha256(json.dumps({
            "available_at": row["available_at"], "source_url": row["source_url"],
            "observation": row["observation"], "features": features,
            "exclusion": row["already_announced_exclusion"],
        }, sort_keys=True).encode()).hexdigest()
        connection.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (
            row["evidence_id"], row["company"], row["ticker"], row["cutoff"], row["available_at"],
            row["source_title"], row["source_url"], row["observation"], snapshot_hash,
            json.dumps(features, sort_keys=True), row["already_announced_exclusion"], row["review_status"]))
        prob, contributions = probability(row)
        prediction_id = f"rv-{row['ticker']}-{row['cutoff']}-{MODEL_VERSION}"
        evidence_ids = [row["evidence_id"]]
        evidence_snapshot_hash = hashlib.sha256(json.dumps(
            {"evidence_ids": evidence_ids, "snapshot_hashes": [snapshot_hash]}, sort_keys=True).encode()).hexdigest()
        confidence = 0.48  # one checked primary disclosure; probability and coverage confidence are separate
        connection.execute("INSERT INTO predictions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            prediction_id, row["company"], row["ticker"], "restructuring_announced", 12,
            row["cutoff"], prob, confidence, MODEL_VERSION, json.dumps(evidence_ids),
            json.dumps(contributions, sort_keys=True), evidence_snapshot_hash, frozen))
        predictions.append({
            "prediction_id": prediction_id, "company": row["company"], "ticker": row["ticker"],
            "information_cutoff": row["cutoff"], "probability": round(prob, 6),
            "confidence": confidence, "model_version": MODEL_VERSION, "evidence_ids": evidence_ids,
            "feature_contributions": contributions, "evidence_snapshot_hash": evidence_snapshot_hash,
            "already_announced_exclusion": row["already_announced_exclusion"],
        })
    connection.commit()
    connection.close()
    result = {
        "status": "frozen before outcome inspection", "target": "restructuring_announced",
        "horizon_months": 12, "model_version": MODEL_VERSION, "prior": PRIOR,
        "weights": WEIGHTS, "frozen_at": frozen, "prediction_count": len(predictions),
        "predictions": predictions,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"registered {len(predictions)} immutable pre-outcome predictions in {DATABASE}")
    return result


if __name__ == "__main__":
    build()

