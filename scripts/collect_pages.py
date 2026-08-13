from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipelines.common.pages import RobotsAwarePageClient, save_page_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot explicitly configured first-party pages")
    parser.add_argument("--config", default="config/page_sources.json")
    parser.add_argument("--database", default="data/derived/pages.sqlite3")
    parser.add_argument("--raw-root", default="data/raw/pages")
    args = parser.parse_args()
    client = RobotsAwarePageClient()
    sources = json.loads(Path(args.config).read_text())
    collected = 0
    for source in sources:
        if not source.get("enabled"):
            continue
        snapshot = client.retrieve(source["url"])
        changed = save_page_snapshot(args.database, args.raw_root, source["company_id"],
                                     source["page_type"], snapshot)
        collected += 1
        print(f"{source['company_id']} {source['page_type']}: {'changed' if changed else 'unchanged'}")
    print(f"Saved {collected} permitted page snapshots")


if __name__ == "__main__":
    main()
