from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipelines.common.pages import RobotsAwarePageClient, save_page_snapshot
from pipelines.common.adapter import SourceUnavailable


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot explicitly configured first-party pages")
    parser.add_argument("--config", default="config/page_sources.json")
    parser.add_argument("--database", default="data/derived/pages.sqlite3")
    parser.add_argument("--raw-root", default="data/raw/pages")
    parser.add_argument("--status-output", default="data/derived/page_collection_status.json")
    args = parser.parse_args()
    client = RobotsAwarePageClient()
    sources = json.loads(Path(args.config).read_text())
    collected = 0
    statuses = []
    for source in sources:
        if not source.get("enabled"):
            continue
        try:
            snapshot = client.retrieve(source["url"])
            changed = save_page_snapshot(args.database, args.raw_root, source["company_id"],
                                         source["page_type"], snapshot)
        except SourceUnavailable as exc:
            statuses.append({**source, "status": "unavailable", "reason": str(exc)})
            print(f"{source['company_id']} {source['page_type']}: unavailable ({exc})")
            continue
        collected += 1
        statuses.append({**source, "status": "changed" if changed else "unchanged",
                         "observed_at": snapshot.observed_at.isoformat(),
                         "content_hash": snapshot.content_hash})
        print(f"{source['company_id']} {source['page_type']}: {'changed' if changed else 'unchanged'}")
    status_path = Path(args.status_output)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps({
        "run_at": datetime.now(timezone.utc).isoformat(), "configured": len(sources),
        "collected": collected, "sources": statuses,
    }, indent=2) + "\n")
    print(f"Saved {collected} permitted page snapshots; status: {status_path}")


if __name__ == "__main__":
    main()
