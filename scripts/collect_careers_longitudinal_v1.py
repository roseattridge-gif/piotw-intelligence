from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipelines.careers import CareerSource, adapter_for
from pipelines.careers.longitudinal import record_snapshot, source_health_report, source_is_due
from pipelines.common.adapter import SourceUnavailable

SOURCES = ROOT / "config/evidence/jobs_sources_v0_2.json"
OUTPUT = ROOT / "data/collection/careers_v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--at", help="UTC ISO timestamp; defaults to now")
    args = parser.parse_args()
    fetched_at = datetime.fromisoformat(args.at) if args.at else datetime.now(UTC)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    database = OUTPUT / "careers_longitudinal.sqlite3"
    runs = []
    for source in [CareerSource.model_validate(row) for row in json.loads(SOURCES.read_text())]:
        if not source_is_due(database, company_id=source.company_id, provider=source.provider, as_of=fetched_at):
            runs.append({"company_id": source.company_id, "provider": source.provider,
                "collection_status": "NOT_DUE", "retrieval_success": None, "jobs": []})
            print(f"{source.company_id}: not due")
            continue
        try:
            jobs = adapter_for(source.provider).collect(source)
            success, error = True, None
        except (SourceUnavailable, ValueError, KeyError) as exc:
            jobs, success, error = [], False, f"{type(exc).__name__}: {exc}"
        result = record_snapshot(database, company_id=source.company_id, provider=source.provider,
            jobs=jobs, fetched_at=fetched_at, retrieval_success=success)
        runs.append({"company_id": source.company_id, "provider": source.provider,
            "collection_status": "COLLECTED",
            "retrieval_success": success, "error": error, **result.__dict__,
            "jobs": [job.model_dump(mode="json") for job in jobs]})
        print(f"{source.company_id}: {len(jobs)} jobs; {result.health}")
    stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")
    target = OUTPUT / f"snapshot_{stamp}.json"
    target.write_text(json.dumps({"collected_at": fetched_at.isoformat(),
        "collector_version": "careers-longitudinal-v1", "runs": runs},
        indent=2, sort_keys=True, default=str) + "\n")
    (OUTPUT / "source_health.json").write_text(json.dumps({
        "as_of": fetched_at.isoformat(), "sources": source_health_report(database, as_of=fetched_at)},
        indent=2, sort_keys=True) + "\n")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
