from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipelines.careers import CareerSource, adapter_for
from pipelines.careers.models import AccessMode
from pipelines.careers.storage import save_snapshot
from pipelines.careers.structured_page import collect_structured_page


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
        jobs = (adapter_for(source.provider).collect(source)
                if source.access_mode == AccessMode.public_api else collect_structured_page(source))
        count = save_snapshot(args.database, source.company_id, source.provider, jobs)
        total += count
        print(f"{source.company_name}: {count} open jobs via {source.provider}")
    print(f"Saved {total} current postings to {args.database}")


if __name__ == "__main__":
    main()
