from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipelines.careers.longitudinal import DERIVED_VERSION, SCHEMA, _json, _snapshot_feature_payload
from pipelines.careers.models import JobPosting

DEFAULT_DB = ROOT / "data/collection/careers_v1/careers_longitudinal.sqlite3"
DEFAULT_RAW = ROOT / "data/collection/careers_v1"


def backfill(database: Path = DEFAULT_DB, raw_directory: Path = DEFAULT_RAW) -> dict[str, int]:
    raw_runs: dict[str, dict[str, object]] = {}
    for path in sorted(raw_directory.glob("snapshot_*.json")):
        payload = json.loads(path.read_text())
        for run in payload.get("runs", []):
            if run.get("snapshot_id"):
                raw_runs[str(run["snapshot_id"])] = run

    counts = {"raw_reprocessed": 0, "legacy_summary_only": 0, "roles": 0}
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA)
        snapshots = connection.execute(
            "SELECT snapshot_id,open_count,retrieval_status FROM career_collection_snapshots ORDER BY fetch_timestamp"
        ).fetchall()
        for snapshot_id, open_count, health in snapshots:
            run = raw_runs.get(snapshot_id)
            if run and health == "healthy" and isinstance(run.get("jobs"), list):
                jobs = [JobPosting.model_validate(item) for item in run["jobs"]]
                roles, derived = _snapshot_feature_payload(jobs)
                connection.execute("DELETE FROM career_snapshot_roles WHERE snapshot_id=?", (snapshot_id,))
                connection.executemany(
                    "INSERT INTO career_snapshot_roles VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(snapshot_id, *role, "HISTORICAL_REPROCESSING", DERIVED_VERSION) for role in roles],
                )
                aggregate = {
                    "total_open": len(jobs), "new_count": run.get("new_count"),
                    "persistent_count": run.get("persistent_count"), "absent_once_count": None,
                    "confirmed_closed_count": run.get("closed_count"), "reopened_count": run.get("reopened_count"),
                    **derived,
                }
                origin = "HISTORICAL_REPROCESSING"
                counts["raw_reprocessed"] += 1; counts["roles"] += len(jobs)
            else:
                derived = {"function_mix": {}, "seniority_mix": {}, "geography_mix": {},
                           "workplace_mix": {}, "technology_mix": {},
                           "missingness": {"raw_role_records": open_count}}
                aggregate = {"total_open": open_count, "new_count": None, "persistent_count": None,
                    "absent_once_count": None, "confirmed_closed_count": None, "reopened_count": None, **derived}
                origin = "LEGACY_SUMMARY_ONLY"
                counts["legacy_summary_only"] += 1
            digest = hashlib.sha256(_json(aggregate).encode()).hexdigest()
            connection.execute(
                "INSERT OR REPLACE INTO career_snapshot_aggregates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (snapshot_id, "piotw-careers-snapshot-v0.1", DERIVED_VERSION, origin,
                 aggregate["total_open"], aggregate["new_count"], aggregate["persistent_count"],
                 aggregate["absent_once_count"], aggregate["confirmed_closed_count"], aggregate["reopened_count"],
                 _json(derived["function_mix"]), _json(derived["seniority_mix"]),
                 _json(derived["geography_mix"]), _json(derived["workplace_mix"]),
                 _json(derived["technology_mix"]), _json(derived["missingness"]), digest),
            )
    return counts


if __name__ == "__main__":
    print(json.dumps(backfill(), sort_keys=True))
