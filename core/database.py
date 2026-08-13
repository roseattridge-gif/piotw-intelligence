from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def migrate(self, migrations: str | Path) -> None:
        with self.connect() as connection:
            for path in sorted(Path(migrations).glob("*.sql")):
                connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations "
                                   "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
                if connection.execute("SELECT 1 FROM schema_migrations WHERE version=?",
                                      (path.name,)).fetchone():
                    continue
                connection.executescript(path.read_text())
                connection.execute("INSERT INTO schema_migrations VALUES (?,?)",
                                   (path.name, datetime.now(timezone.utc).isoformat()))
