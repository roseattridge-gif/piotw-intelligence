from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from pipelines.careers.models import JobPosting


SCHEMA = """
CREATE TABLE IF NOT EXISTS career_jobs (
  identity TEXT PRIMARY KEY,
  company_id TEXT NOT NULL,
  company_name TEXT NOT NULL,
  provider TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  location TEXT,
  department TEXT,
  employment_type TEXT,
  workplace_type TEXT,
  description TEXT,
  published_at TEXT,
  source_url TEXT NOT NULL,
  apply_url TEXT,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  closed_at TEXT
);
CREATE TABLE IF NOT EXISTS career_snapshots (
  snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  open_job_count INTEGER NOT NULL
);
"""


def save_snapshot(path: str | Path, source_company_id: str, provider: str,
                  jobs: Iterable[JobPosting], observed_at: datetime | None = None) -> int:
    observed = (observed_at or datetime.now(timezone.utc)).isoformat()
    records = list(jobs)
    database = Path(path)
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA)
        active = {job.identity for job in records}
        for job in records:
            values = job.model_dump(mode="json")
            connection.execute("""
                INSERT INTO career_jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(identity) DO UPDATE SET
                  title=excluded.title, location=excluded.location, department=excluded.department,
                  employment_type=excluded.employment_type, workplace_type=excluded.workplace_type,
                  description=excluded.description, source_url=excluded.source_url,
                  apply_url=excluded.apply_url, last_seen_at=excluded.last_seen_at, closed_at=NULL
            """, (job.identity, values["company_id"], values["company_name"], values["provider"],
                  values["external_id"], values["title"], values["location"], values["department"],
                  values["employment_type"], values["workplace_type"], values["description"],
                  values["published_at"], values["source_url"], values["apply_url"], observed, observed))
        open_rows = connection.execute(
            "SELECT identity FROM career_jobs WHERE company_id=? AND provider=? AND closed_at IS NULL",
            (source_company_id, provider),
        ).fetchall()
        for (identity,) in open_rows:
            if identity not in active:
                connection.execute("UPDATE career_jobs SET closed_at=? WHERE identity=?", (observed, identity))
        connection.execute(
            "INSERT INTO career_snapshots(company_id, provider, observed_at, open_job_count) VALUES (?, ?, ?, ?)",
            (source_company_id, provider, observed, len(records)),
        )
    return len(records)
