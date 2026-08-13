from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipelines.careers import CareerSource, adapter_for
from pipelines.careers.storage import save_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot documented public ATS job feeds")
    parser.add_argument("--config", default="config/career_sources.json")
    parser.add_argument("--database", default="data/derived/careers.sqlite3")
    args = parser.parse_args()
    sources = [CareerSource.model_validate(row) for row in json.loads(Path(args.config).read_text())]
    total = 0
    for source in sources:
        if not source.enabled:
            continue
        jobs = adapter_for(source.provider).collect(source)
        count = save_snapshot(args.database, source.company_id, source.provider, jobs)
        total += count
        print(f"{source.company_name}: {count} open jobs via {source.provider}")
    print(f"Saved {total} current postings to {args.database}")


if __name__ == "__main__":
    main()
