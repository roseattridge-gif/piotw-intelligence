from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from validation.restructuring_v2 import canonical_json, predict_restructuring, specification_hash
from validation.restructuring_v2_data import validate_evidence, validate_features, validate_manifest

SCHEMA = """
CREATE TABLE IF NOT EXISTS v2_specifications(
  specification_type TEXT PRIMARY KEY, version TEXT NOT NULL, sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS v2_evidence(
  evidence_id TEXT PRIMARY KEY, occasion_id TEXT NOT NULL, available_at TEXT NOT NULL,
  source_url TEXT NOT NULL, raw_sha256 TEXT NOT NULL, extraction_sha256 TEXT NOT NULL,
  observation TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS v2_predictions(
  prediction_id TEXT PRIMARY KEY, occasion_id TEXT NOT NULL UNIQUE, stable_id TEXT NOT NULL,
  company TEXT NOT NULL, ticker TEXT NOT NULL, sector TEXT NOT NULL, stratum TEXT NOT NULL,
  partition TEXT NOT NULL, cutoff TEXT NOT NULL, window_end TEXT NOT NULL,
  probability REAL NOT NULL CHECK(probability BETWEEN 0 AND 1), confidence REAL NOT NULL,
  model_version TEXT NOT NULL, model_specification_sha256 TEXT NOT NULL,
  features_json TEXT NOT NULL, contributions_json TEXT NOT NULL,
  evidence_ids_json TEXT NOT NULL, evidence_snapshot_sha256 TEXT NOT NULL,
  manifest_row_sha256 TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS v2_evidence_no_update BEFORE UPDATE ON v2_evidence
  BEGIN SELECT RAISE(ABORT, 'v2 evidence is immutable'); END;
CREATE TRIGGER IF NOT EXISTS v2_evidence_no_delete BEFORE DELETE ON v2_evidence
  BEGIN SELECT RAISE(ABORT, 'v2 evidence is immutable'); END;
CREATE TRIGGER IF NOT EXISTS v2_predictions_no_update BEFORE UPDATE ON v2_predictions
  BEGIN SELECT RAISE(ABORT, 'v2 predictions are immutable'); END;
CREATE TRIGGER IF NOT EXISTS v2_predictions_no_delete BEFORE DELETE ON v2_predictions
  BEGIN SELECT RAISE(ABORT, 'v2 predictions are immutable'); END;
"""


def _insert_exact(connection: sqlite3.Connection, table: str, key_name: str,
                  key: str, columns: list[str], values: list[Any]) -> None:
    existing = connection.execute(
        f"SELECT {','.join(columns)} FROM {table} WHERE {key_name}=?", (key,)).fetchone()
    expected = tuple(values)
    if existing is not None:
        if tuple(existing) != expected:
            raise ValueError(f"immutable {table} conflict for {key}")
        return
    placeholders = ",".join("?" for _ in columns)
    connection.execute(
        f"INSERT INTO {table}({','.join(columns)}) VALUES({placeholders})", expected)


def register_predictions(manifest: list[dict[str, str]], evidence: list[dict[str, str]],
                         features: list[dict[str, str]], root: str | Path,
                         database: str | Path, model_path: str | Path) -> dict[str, Any]:
    validate_manifest(manifest)
    validate_evidence(manifest, evidence, root)
    validate_features(manifest, evidence, features)
    model = json.loads(Path(model_path).read_text())
    model_hash = specification_hash(model_path)
    evidence_by_id = {row["evidence_id"]: row for row in evidence}
    manifest_by_id = {row["occasion_id"]: row for row in manifest}
    predictions = []
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA)
        _insert_exact(connection, "v2_specifications", "specification_type", "model",
                      ["specification_type", "version", "sha256"],
                      ["model", model["model_version"], model_hash])
        for row in evidence:
            _insert_exact(connection, "v2_evidence", "evidence_id", row["evidence_id"],
                          ["evidence_id", "occasion_id", "available_at", "source_url", "raw_sha256",
                           "extraction_sha256", "observation"],
                          [row["evidence_id"], row["occasion_id"], row["available_at"], row["source_url"],
                           row["raw_sha256"], row["extraction_sha256"], row["observation"]])
        for feature_row in features:
            occasion = manifest_by_id[feature_row["occasion_id"]]
            feature_values = {name: float(feature_row[name]) for name in model["inputs"]}
            probability, contributions = predict_restructuring(feature_values, model)
            evidence_ids = [item for item in feature_row["evidence_ids"].split("|") if item]
            snapshot_hashes = [evidence_by_id[item]["extraction_sha256"] for item in evidence_ids]
            evidence_snapshot_hash = hashlib.sha256(canonical_json({
                "ordered_evidence_ids": evidence_ids,
                "ordered_extraction_hashes": snapshot_hashes,
            }).encode()).hexdigest()
            prediction_id = model["prediction_identity"].format(
                ticker=occasion["ticker"], cutoff=occasion["cutoff"])
            confidence = 0.48 if len(evidence_ids) >= 1 else 0.0
            prediction = {
                "prediction_id": prediction_id, "occasion_id": occasion["occasion_id"],
                "stable_id": occasion["stable_id"], "company": occasion["company"],
                "ticker": occasion["ticker"], "sector": occasion["sector"],
                "stratum": occasion["stratum"], "partition": occasion["dataset_partition"],
                "cutoff": occasion["cutoff"], "window_end": occasion["window_end"],
                "probability": probability, "confidence": confidence,
                "model_version": model["model_version"], "model_specification_sha256": model_hash,
                "features": feature_values, "contributions": contributions,
                "evidence_ids": evidence_ids, "evidence_snapshot_sha256": evidence_snapshot_hash,
                "manifest_row_sha256": hashlib.sha256(canonical_json(occasion).encode()).hexdigest(),
            }
            columns = [
                "prediction_id", "occasion_id", "stable_id", "company", "ticker", "sector", "stratum",
                "partition", "cutoff", "window_end", "probability", "confidence", "model_version",
                "model_specification_sha256", "features_json", "contributions_json", "evidence_ids_json",
                "evidence_snapshot_sha256", "manifest_row_sha256",
            ]
            values = [prediction.get(name) if name not in {"features_json", "contributions_json", "evidence_ids_json"}
                      else canonical_json(prediction[{"features_json": "features", "contributions_json": "contributions",
                                                     "evidence_ids_json": "evidence_ids"}[name]]) for name in columns]
            _insert_exact(connection, "v2_predictions", "prediction_id", prediction_id, columns, values)
            predictions.append(prediction)
    return {"model_version": model["model_version"], "model_specification_sha256": model_hash,
            "prediction_count": len(predictions), "predictions": predictions}
