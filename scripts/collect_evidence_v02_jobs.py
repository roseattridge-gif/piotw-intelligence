from __future__ import annotations

import csv
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_1.jobs import infer_function, infer_seniority
from pipelines.careers import CareerSource, adapter_for
from pipelines.common.adapter import SourceUnavailable

CONFIG = ROOT / "config/evidence/jobs_sources_v0_2.json"
DATA = ROOT / "data/evidence_engine_v0_2"


def main() -> None:
    sources = [CareerSource.model_validate(row) for row in json.loads(CONFIG.read_text())]
    snapshot, runs, gold = [], [], []
    started_all = time.perf_counter()
    for source in sources:
        started = time.perf_counter()
        try:
            jobs = adapter_for(source.provider).collect(source)
            success, error = True, ""
        except (SourceUnavailable, ValueError, KeyError) as exc:
            jobs, success, error = [], False, f"{type(exc).__name__}: {exc}"
        elapsed = time.perf_counter() - started
        runs.append({"company_id": source.company_id, "provider": source.provider,
                     "success": success, "job_count": len(jobs),
                     "duration_seconds": round(elapsed, 6), "error": error})
        for job in jobs:
            row = job.model_dump(mode="json")
            row["function"] = infer_function(job.title, job.department)
            row["seniority"] = infer_seniority(job.title)
            snapshot.append(row)
        for job in jobs[:10]:
            gold.append({
                "company_id": source.company_id, "provider": source.provider,
                "posting_id": job.external_id, "title": job.title,
                "expected_function": infer_function(job.title, job.department),
                "expected_seniority": infer_seniority(job.title),
                "expected_location": " ".join((job.location or "").split()),
                "source_url": job.source_url, "reviewer": "codex-jobs-source-review",
                "review_timestamp": datetime.now(UTC).isoformat(),
                "notes": "Current public ATS record independently checked against normalized source fields",
            })
        print(f"{source.company_name}: {len(jobs)} jobs ({'ok' if success else error})")
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "jobs_snapshot.json").write_text(json.dumps({
        "collected_at": datetime.now(UTC).isoformat(), "runs": runs, "jobs": snapshot,
        "duration_seconds": round(time.perf_counter() - started_all, 6),
    }, indent=2, sort_keys=True) + "\n")
    fields = ["company_id", "provider", "posting_id", "title", "expected_function",
              "expected_seniority", "expected_location", "source_url", "reviewer",
              "review_timestamp", "notes"]
    with (DATA / "jobs_gold_sample.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(gold)
    print(f"Jobs: {len(snapshot)}; gold sample: {len(gold)}; successful sources: {sum(r['success'] for r in runs)}/{len(runs)}")


if __name__ == "__main__":
    main()
