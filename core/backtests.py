from __future__ import annotations

import json
import sqlite3
from datetime import date
from uuid import uuid4

from backtesting.evaluation import evaluate_binary


def run_backtest(connection: sqlite3.Connection, name: str, cohort_version: str,
                 model_version: str, target: str, started_at: str,
                 run_id: str | None = None) -> dict:
    identifier = run_id or str(uuid4())
    rows = connection.execute("""
      SELECT p.prediction_id,p.probability,p.information_cutoff_at,o.outcome_id,o.occurred,o.outcome_date
      FROM predictions p JOIN outcomes o
        ON o.company_id=p.company_id AND o.prediction_target=p.prediction_target
       AND o.window_start=date(p.information_cutoff_at)
      WHERE p.model_version=? AND p.prediction_target=? AND o.resolution_status='resolved'
      ORDER BY p.prediction_id
    """, (model_version, target)).fetchall()
    if not rows:
        raise ValueError("No resolved prediction/outcome pairs")
    connection.execute("INSERT INTO backtest_runs VALUES(?,?,?,?,?,?,?,?,?)",
                       (identifier, name, cohort_version, model_version, target,
                        json.dumps({"point_in_time": True}, sort_keys=True), started_at, started_at, "complete"))
    for row in rows:
        cutoff = date.fromisoformat(row["information_cutoff_at"][:10])
        lead = ((date.fromisoformat(row["outcome_date"]) - cutoff).days
                if row["occurred"] and row["outcome_date"] else None)
        connection.execute("INSERT INTO backtest_results VALUES(?,?,?,?,?,?,?,?)",
                           (str(uuid4()), identifier, row["prediction_id"], row["outcome_id"],
                            row["probability"], row["occurred"],
                            (row["probability"] - row["occurred"]) ** 2, lead))
    metrics = evaluate_binary([row["probability"] for row in rows], [row["occurred"] for row in rows])
    return {"backtest_run_id": identifier, "target": target, "metrics": metrics.__dict__,
            "warning": "Single-company vertical-slice metric; infrastructure proof only" if len(rows) == 1 else None}
