from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from pipelines.common.adapter import SourceUnavailable
from pipelines.common.http import PublicHttpClient


@dataclass(frozen=True)
class PageSnapshot:
    url: str
    observed_at: datetime
    content_hash: str
    html: str


class RobotsAwarePageClient:
    """Fail-closed single-page retriever for explicitly configured first-party pages."""

    def __init__(self, client: PublicHttpClient | None = None):
        self.client = client or PublicHttpClient(minimum_interval_seconds=1.0)

    def retrieve(self, url: str) -> PageSnapshot:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Configured pages must use an absolute HTTPS URL")
        robots_url = urlunsplit((parsed.scheme, parsed.netloc, "/robots.txt", "", ""))
        try:
            robots_text = self.client.get_text(robots_url)
        except SourceUnavailable as exc:
            raise SourceUnavailable(f"Could not verify robots policy for {url}; collection stopped") from exc
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(robots_text.splitlines())
        if not parser.can_fetch(self.client.user_agent, url):
            raise SourceUnavailable(f"Robots policy does not permit collection of {url}")
        html = self.client.get_text(url, {"Accept": "text/html,application/xhtml+xml"})
        return PageSnapshot(url=url, observed_at=datetime.now(timezone.utc),
                            content_hash=hashlib.sha256(html.encode()).hexdigest(), html=html)


PAGE_SCHEMA = """
CREATE TABLE IF NOT EXISTS page_snapshots (
  snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id TEXT NOT NULL,
  page_type TEXT NOT NULL,
  url TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  raw_path TEXT NOT NULL,
  changed_from_previous INTEGER NOT NULL
);
"""


def save_page_snapshot(database: str | Path, raw_root: str | Path, company_id: str,
                       page_type: str, snapshot: PageSnapshot) -> bool:
    database_path = Path(database)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    raw_directory = Path(raw_root) / company_id / page_type
    raw_directory.mkdir(parents=True, exist_ok=True)
    filename = snapshot.observed_at.strftime("%Y%m%dT%H%M%SZ") + f"-{snapshot.content_hash[:12]}.html"
    raw_path = raw_directory / filename
    raw_path.write_text(snapshot.html)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(PAGE_SCHEMA)
        previous = connection.execute(
            "SELECT content_hash FROM page_snapshots WHERE company_id=? AND page_type=? "
            "ORDER BY observed_at DESC LIMIT 1", (company_id, page_type),
        ).fetchone()
        changed = previous is None or previous[0] != snapshot.content_hash
        connection.execute(
            "INSERT INTO page_snapshots(company_id,page_type,url,observed_at,content_hash,raw_path,changed_from_previous) "
            "VALUES(?,?,?,?,?,?,?)", (company_id, page_type, snapshot.url, snapshot.observed_at.isoformat(),
                                      snapshot.content_hash, str(raw_path), int(changed)))
    return changed
