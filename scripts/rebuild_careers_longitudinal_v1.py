from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipelines.careers.longitudinal import record_snapshot
from pipelines.careers.models import JobPosting


def main() -> int:
    baseline = json.loads((ROOT / "data/evidence_engine_v0_3/jobs_snapshots/snapshot_001_baseline.json").read_text())
    current_path = max((ROOT / "data/collection/careers_v1").glob("snapshot_*.json"))
    current = json.loads(current_path.read_text())
    target = ROOT / "data/collection/careers_v1/careers_longitudinal.sqlite3"
    staging = target.with_suffix(".rebuild.sqlite3")
    if staging.exists():
        staging.unlink()
    baseline_jobs: dict[tuple[str, str], list[JobPosting]] = {}
    for row in baseline["jobs"]:
        item = JobPosting.model_validate(row)
        baseline_jobs.setdefault((item.company_id, item.provider), []).append(item)
    baseline_runs = {(row["company_id"], row["provider"]): row for row in baseline["runs"]}
    baseline_at = datetime.fromisoformat(baseline["collected_at"])
    for key, run in baseline_runs.items():
        record_snapshot(staging, company_id=key[0], provider=key[1],
            jobs=baseline_jobs.get(key, []), fetched_at=baseline_at, retrieval_success=run["success"])
    current_at = datetime.fromisoformat(current["collected_at"])
    for run in current["runs"]:
        record_snapshot(staging, company_id=run["company_id"], provider=run["provider"],
            jobs=[JobPosting.model_validate(row) for row in run["jobs"]], fetched_at=current_at,
            retrieval_success=run["retrieval_success"])
    os.replace(staging, target)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
