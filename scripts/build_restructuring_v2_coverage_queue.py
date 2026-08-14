"""Build the complete pre-outcome work queue for all frozen v2 occasions."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTITIONS = ("validation", "holdout")
OUTPUT = ROOT / "data/derived/restructuring_v2_coverage_queue.csv"
SUMMARY = ROOT / "data/derived/restructuring_v2_coverage_summary.json"
INDEX = ROOT / "data/derived/restructuring_v2_source_index.json"
DATA = ROOT / "data/restructuring_v2"
FIELDS = [
    "occasion_id", "company", "ticker", "stable_id", "dataset_partition", "cutoff",
    "required_evidence_categories", "sources_attempted", "sources_successfully_captured",
    "sources_unavailable", "extraction_status", "manual_scoring_status", "feature_ready",
    "exclusion_reason", "evidence_completeness_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def review_ids(pattern: str) -> set[str]:
    result = set()
    for path in DATA.glob(pattern):
        result.update(row["occasion_id"] for row in read_csv(path))
    return result


def unavailable_detail(source: dict[str, object]) -> str:
    failures = source.get("attempt_results", [])
    if not isinstance(failures, list):
        return str(source.get("reason", ""))
    return " | ".join(
        f"{item.get('url', '')} [{item.get('status', '')}: {item.get('reason', '')}]"
        for item in failures if isinstance(item, dict)
    )


def main() -> None:
    manifests = [row for partition in PARTITIONS for row in read_csv(
        ROOT / f"data/manifests/restructuring_{partition}.csv")]
    sources = json.loads(INDEX.read_text()).get("sources", {}) if INDEX.exists() else {}
    packets = {row["occasion_id"] for row in read_csv(
        ROOT / "data/derived/restructuring_v2_feature_review_queue.csv")}
    reviewed = review_ids("feature_reviews_batch_*.csv") | review_ids(
        "web_feature_reviews_batch_*.csv")
    evidence = {row["occasion_id"] for row in read_csv(DATA / "evidence.csv")}
    features = {row["occasion_id"] for row in read_csv(DATA / "features.csv")}
    rows = []
    for manifest in sorted(manifests, key=lambda row: row["occasion_id"]):
        occasion_id = manifest["occasion_id"]
        source = sources.get(occasion_id, {})
        source_status = str(source.get("status", "not_started"))
        attempted = source.get("attempted_urls", [])
        if not attempted and source.get("url"):
            attempted = [source["url"]]
        captured = source.get("url", "") if source_status == "preserved" else ""
        exclusion = manifest.get("exclusion_reason", "")
        if occasion_id in evidence and occasion_id in features:
            coverage = "evidence_complete_prediction_eligible"
        elif exclusion:
            coverage = "excluded_frozen_rule"
        elif source_status == "preserved":
            coverage = "source_captured_pending_processing"
        elif source_status in {"retrieval_failed", "parse_failed", "invalid_content"}:
            coverage = "technically_unavailable_pending_resolution"
        elif source_status == "not_found":
            coverage = "source_not_found_pending_alternative"
        else:
            coverage = "not_started"
        rows.append({
            "occasion_id": occasion_id, "company": manifest["company"],
            "ticker": manifest["ticker"], "stable_id": manifest["stable_id"],
            "dataset_partition": manifest["dataset_partition"], "cutoff": manifest["cutoff"],
            "required_evidence_categories": "annual_report_or_approved_primary_disclosure",
            "sources_attempted": " | ".join(map(str, attempted)),
            "sources_successfully_captured": str(captured),
            "sources_unavailable": unavailable_detail(source),
            "extraction_status": "complete" if occasion_id in evidence else (
                "packet_ready" if occasion_id in packets else "not_started"),
            "manual_scoring_status": "complete" if occasion_id in reviewed else "not_started",
            "feature_ready": "yes" if occasion_id in features else "no",
            "exclusion_reason": exclusion,
            "evidence_completeness_status": coverage,
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    statuses = Counter(row["evidence_completeness_status"] for row in rows)
    summary = {
        "schema_version": "1", "occasion_count": len(rows),
        "outcomes_researched": 0, "status_counts": dict(sorted(statuses.items())),
        "source_status_counts": dict(sorted(Counter(
            str(sources.get(row["occasion_id"], {}).get("status", "not_started"))
            for row in manifests).items())),
        "extraction_complete": sum(row["extraction_status"] == "complete" for row in rows),
        "manual_scoring_complete": sum(
            row["manual_scoring_status"] == "complete" for row in rows),
        "feature_ready": sum(row["feature_ready"] == "yes" for row in rows),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"coverage queue: {len(rows)} occasions; {summary['feature_ready']} feature-ready")


if __name__ == "__main__":
    main()
