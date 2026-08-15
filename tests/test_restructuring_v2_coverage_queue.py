from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from validation.restructuring_v2_data import read_csv

ROOT = Path(__file__).resolve().parents[1]


def test_coverage_queue_dispositions_every_frozen_occasion():
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_restructuring_v2_coverage_queue.py")],
        check=True,
    )
    queue = read_csv(ROOT / "data/derived/restructuring_v2_coverage_queue.csv")
    summary = json.loads((ROOT / "data/derived/restructuring_v2_coverage_summary.json").read_text())
    manifest_ids = {
        row["occasion_id"]
        for partition in ("validation", "holdout")
        for row in read_csv(ROOT / f"data/manifests/restructuring_{partition}.csv")
    }
    assert len(queue) == len(manifest_ids) == summary["occasion_count"] == 291
    assert {row["occasion_id"] for row in queue} == manifest_ids
    assert all(row["required_evidence_categories"] for row in queue)
    assert all(row["evidence_completeness_status"] for row in queue)
    assert summary["outcomes_researched"] == 0
    assert sum(summary["status_counts"].values()) == 291
    excluded = [row for row in queue
                if row["evidence_completeness_status"] == "excluded_frozen_rule"]
    assert {row["occasion_id"] for row in excluded} == {
        "rv2-DWL-2020-12-31", "rv2-DWL-2022-12-31"}
    assert all(row["exclusion_reason"] for row in excluded)
