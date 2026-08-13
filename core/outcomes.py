from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from uuid import uuid4


@dataclass(frozen=True)
class OutcomeResolution:
    company_id: str
    target: str
    window_start: date
    window_end: date
    occurred: bool
    outcome_date: date | None
    evidence_id: str | None
    notes: str


def store_outcome(connection: sqlite3.Connection, outcome: OutcomeResolution,
                  resolved_at: str, resolver_version: str = "outcome-resolver-0.1.0",
                  outcome_id: str | None = None) -> str:
    identifier = outcome_id or str(uuid4())
    connection.execute("""
      INSERT INTO outcomes VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    """, (identifier, outcome.company_id, outcome.target, outcome.window_start.isoformat(),
          outcome.window_end.isoformat(), int(outcome.occurred),
          outcome.outcome_date.isoformat() if outcome.outcome_date else None, resolved_at,
          "resolved", outcome.evidence_id, resolver_version, outcome.notes))
    return identifier
