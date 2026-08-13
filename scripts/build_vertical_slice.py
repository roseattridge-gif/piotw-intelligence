"""Build the complete Bodycote historical vertical slice in a fresh SQLite database."""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.backtests import run_backtest
from core.database import Database
from core.events import event_fingerprint
from core.outcomes import OutcomeResolution, store_outcome
from core.predictions import PredictionRegistry, TargetContribution

DATABASE = ROOT / "data/derived/piotw_mvp.sqlite3"
CREATED = "2026-08-13T12:00:00+00:00"
CUTOFF = datetime(2021, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
MODEL_VERSION = "margin-deterioration-prior-0.1.0"


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{hashlib.sha256(value.encode()).hexdigest()[:20]}"


def insert_evidence(connection: sqlite3.Connection, row: dict, manifest: dict,
                    source_id: str, company_id: str) -> str:
    evidence_id = row["fact_id"]
    raw_text = row["observation"]
    connection.execute("""
      INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (evidence_id, company_id, source_id, evidence_id, manifest["source_url"],
          manifest["available_at"] + "T00:00:00+00:00", manifest["available_at"],
          manifest["available_at"] + "T00:00:00+00:00", manifest["retrieved_at"] + "T00:00:00+00:00",
          raw_text[:120], raw_text, json.dumps({"direction": int(row["direction"]), "condition": row["condition"]}),
          json.dumps({"source_location": row["source_location"]}),
          hashlib.sha256((manifest["content_hash"] + evidence_id).encode()).hexdigest(),
          manifest["raw_storage_path"], manifest["parser_version"], "manual_checked_v01",
          1.0, float(row["reliability"])))
    return evidence_id


def build() -> dict:
    if DATABASE.exists():
        DATABASE.unlink()
    database = Database(DATABASE)
    database.migrate(ROOT / "database/sqlite")
    manifests = {row["document_id"]: row for row in csv.DictReader((ROOT / "data/document_manifest.csv").open())}
    ledger = [row for row in csv.DictReader((ROOT / "data/evidence_ledger.csv").open()) if row["company"] == "Bodycote"]

    with database.connect() as connection:
        connection.execute("INSERT INTO companies VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                           ("bodycote", "Bodycote plc", "Bodycote", "00519057", "BOY", "bodycote.com",
                            "Industrial services", "United Kingdom", None, "entity-map-0.1.0", CREATED))
        for alias in ("Bodycote", "Bodycote plc", "Bodycote Group"):
            normalized = " ".join(word for word in alias.casefold().split() if word not in {"plc", "group"})
            connection.execute("INSERT OR IGNORE INTO company_aliases VALUES(?,?,?,?,?,?,?,?)",
                               (stable_id("alias", alias), "bodycote", alias, normalized, "legal_or_trading", 1.0, None, None))
        connection.execute("INSERT INTO sources VALUES(?,?,?,?,?,?,?,?)",
                           ("bodycote-ir", "company_regulated_disclosure", "Bodycote investor relations",
                            "https://www.bodycote.com", "public_page", 0.80, "2026-08-13", "{}"))
        connection.execute("INSERT INTO collector_runs VALUES(?,?,?,?,?,?,?,?,?)",
                           ("fixture-bodycote-0.1", "bodycote-ir", CREATED, CREATED, "complete", 9, 9, None, "fixture-loader-0.1.0"))

        prediction_evidence_ids = []
        event_ids = {}
        for row in ledger:
            evidence_id = insert_evidence(connection, row, manifests[row["document_id"]], "bodycote-ir", "bodycote")
            prediction_evidence_ids.append(evidence_id)
            event_type = row["signal_family"]
            summary = row["observation"]
            event_day = date.fromisoformat(manifests[row["document_id"]]["available_at"])
            fingerprint = event_fingerprint("bodycote", event_type, event_day, summary)
            event_id = stable_id("event", fingerprint)
            event_ids[evidence_id] = event_id
            connection.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?)",
                               (event_id, "bodycote", event_type, summary, event_day.isoformat(),
                                event_day.isoformat() + "T00:00:00+00:00", float(row["materiality"]),
                                "event-resolver-0.1.0", fingerprint, CREATED))
            connection.execute("INSERT INTO event_evidence VALUES(?,?,?,?)",
                               (event_id, evidence_id, "supports" if int(row["direction"]) > 0 else "contradicts", 1.0))

        outcome_manifest = manifests["bodycote-fy22"]
        outcome_text = "Headline operating margin fell by only 30 basis points, below the 150 basis-point outcome threshold."
        connection.execute("""INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                           ("BOY-OUTCOME-2023", "bodycote", "bodycote-ir", "bodycote-fy22",
                            outcome_manifest["source_url"], "2023-03-17T00:00:00+00:00", "2023-03-17",
                            "2023-03-17T00:00:00+00:00", outcome_manifest["retrieved_at"] + "T00:00:00+00:00",
                            "Bodycote 2022 full-year results", outcome_text,
                            json.dumps({"headline_margin_change_bps": -30, "threshold_bps": -150}), "{}",
                            hashlib.sha256((outcome_manifest["content_hash"] + "outcome").encode()).hexdigest(),
                            outcome_manifest["raw_storage_path"], outcome_manifest["parser_version"],
                            "manual_outcome_resolution", 1.0, 0.80))

        feature_values = {
            "guidance_reduction_signal": 0.80,
            "automotive_supply_pressure": 0.80,
            "cash_strength_signal": 0.70,
            "pricing_recovery_signal": 0.55,
        }
        feature_evidence = {
            "guidance_reduction_signal": ["BOY03"], "automotive_supply_pressure": ["BOY02"],
            "cash_strength_signal": ["BOY06"], "pricing_recovery_signal": ["BOY07"]}
        for feature, value in feature_values.items():
            connection.execute("INSERT INTO feature_snapshots VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                               (stable_id("feature", feature), "bodycote", feature, "features-0.1.0", "2021-12-31",
                                value, "normalised_0_1", 0.70, json.dumps(feature_evidence[feature]),
                                json.dumps({"method": "manual_checked_vertical_slice", "cutoff": "2021-12-31"}), CREATED))

        configuration = {"target": "operating_margin_deterioration", "prior": 0.20, "scale": 4.0,
                         "threshold_bps": -150, "weights": {"guidance": 0.16, "supply": 0.10, "cash": -0.08, "pricing": -0.06}}
        config_json = json.dumps(configuration, sort_keys=True)
        connection.execute("INSERT INTO model_versions VALUES(?,?,?,?,?,?,?,?,?)",
                           (MODEL_VERSION, "transparent_weighted_evidence", "operating_margin_deterioration",
                            "features-0.1.0", config_json, hashlib.sha256(config_json.encode()).hexdigest(),
                            "2021-12-31", CREATED, "frozen_demo"))
        contributions = [
            TargetContribution("BOY03", event_ids["BOY03"], "supports", 0.16, ledger[2]["observation"]),
            TargetContribution("BOY02", event_ids["BOY02"], "supports", 0.10, ledger[1]["observation"]),
            TargetContribution("BOY06", event_ids["BOY06"], "contradicts", 0.08, ledger[5]["observation"]),
            TargetContribution("BOY07", event_ids["BOY07"], "contradicts", 0.06, ledger[6]["observation"]),
        ]
        registry = PredictionRegistry(connection)
        prediction_id = registry.register("bodycote", "operating_margin_deterioration", CUTOFF, MODEL_VERSION,
                                          feature_values, contributions, confidence=0.42,
                                          created_at=CUTOFF, prediction_id="pred-bodycote-margin-20211231")
        outcome_id = store_outcome(connection, OutcomeResolution(
            company_id="bodycote", target="operating_margin_deterioration", window_start=date(2021, 12, 31),
            window_end=date(2022, 12, 31), occurred=False, outcome_date=None,
            evidence_id="BOY-OUTCOME-2023", notes="Headline margin fell 30bps; the predefined deterioration threshold was 150bps."),
            CREATED, outcome_id="outcome-bodycote-margin-2022")
        connection.execute("INSERT INTO prediction_resolutions VALUES(?,?,?,?,?)",
                           (prediction_id, outcome_id, "resolved_negative", CREATED, "outcome-resolver-0.1.0"))
        backtest = run_backtest(connection, "Bodycote margin vertical slice", "vertical-slice-0.1",
                                MODEL_VERSION, "operating_margin_deterioration", CREATED,
                                run_id="backtest-bodycote-margin-0.1")
        prediction = dict(connection.execute("""
          SELECT p.*,r.resolution_status,r.resolved_at,r.outcome_id
          FROM predictions p LEFT JOIN prediction_resolutions r USING(prediction_id)
          WHERE p.prediction_id=?
        """, (prediction_id,)).fetchone())
        evidence = [dict(row) for row in connection.execute("""
          SELECT pe.relationship,pe.contribution,e.evidence_id,e.title,e.raw_text,e.source_url,e.available_at
          FROM prediction_evidence pe JOIN evidence e USING(evidence_id)
          WHERE pe.prediction_id=? ORDER BY ABS(pe.contribution) DESC
        """, (prediction_id,))]
        output = {"status": "complete historical vertical slice; n=1 infrastructure proof only",
                  "company": {"company_id": "bodycote", "name": "Bodycote"},
                  "prediction": prediction, "evidence": evidence,
                  "outcome": {"outcome_id": outcome_id, "occurred": False, "outcome_date": None},
                  "backtest": backtest}
    output_path = ROOT / "data/derived/vertical_slice.json"
    output_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"built immutable vertical slice in {DATABASE} and {output_path}")
    return output


if __name__ == "__main__":
    build()
