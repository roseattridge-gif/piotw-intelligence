from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/evidence_engine_v0_2/corpus_manifest.csv"
DATA = ROOT / "data/evidence_engine_v0_3"


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows or [])


def select_corpus() -> list[dict[str, str]]:
    with SOURCE.open(newline="") as stream:
        source = list(csv.DictReader(stream))
    tickers = sorted({row["ticker"] for row in source})[:15]
    selected = []
    for ticker in tickers:
        rows = [row for row in source if row["ticker"] == ticker]
        annual = [row for row in rows if row["form"] == "10-K"]
        first = annual[0]
        alternatives = [row for row in rows if row["document_id"] != first["document_id"]]
        second = next((row for row in alternatives if row["form"] != "10-K"), alternatives[-1])
        selected.extend([first, second])
    output = []
    for index, row in enumerate(selected, 1):
        output.append({
            "document_id": row["document_id"].replace("ee02", "ee03"),
            "company": row["company"], "ticker": row["ticker"],
            "source_url": row["source_url"], "report_type": row["report_type"],
            "publication_date": row["publication_date"], "reporting_period": row["reporting_period"],
            "document_format": "SEC inline-XBRL HTML plus reviewer PDF rendering",
            "source_artifact": row["local_artifact"],
            "reviewer_pdf": f"output/pdf/evidence_engine_v0_3/{row['document_id'].replace('ee02', 'ee03')}.pdf",
            "difficulty_flags": row["difficulty_flags"] + "|visual_pdf_rendering|table_reading_order",
            "difficulty_class": "difficult",
            "development_safe_status": "external_us_development_no_outcomes",
            "annotation_workflow": "human_first" if index % 2 else "piotw_first_review_burden_only",
        })
    return output


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    corpus = select_corpus()
    write_csv(DATA / "corpus_manifest.csv", list(corpus[0]), corpus)
    write_csv(DATA / "gold_observations.csv", [
        "document_id", "metric_type", "value", "unit", "scale", "currency", "period",
        "accounting_basis", "source_page_section", "exact_evidence_span", "reviewer_id",
        "annotation_timestamp", "ambiguity_flag", "notes",
    ])
    write_csv(DATA / "gold_events.csv", [
        "document_id", "reviewer_free_text_label", "mapped_event_type", "label_status",
        "source_page_section", "exact_evidence_span", "reviewer_id", "annotation_timestamp",
        "ambiguity_flag", "notes",
    ])
    write_csv(DATA / "review_workflow_log.csv", [
        "document_id", "workflow", "reviewer_id", "started_at", "completed_at", "elapsed_seconds",
        "extracted_observations", "accepted", "corrected", "rejected", "missing_added",
        "severe_corrections", "notes",
    ], [{"document_id": row["document_id"], "workflow": row["annotation_workflow"]} for row in corpus])
    assignments = [{
        "document_id": row["document_id"], "company": row["company"],
        "workflow": row["annotation_workflow"], "source_url": row["source_url"],
        "reviewer_pdf": row["reviewer_pdf"],
        "machine_output_visibility": "hidden until gold freeze" if row["annotation_workflow"] == "human_first" else "shown only in separate assisted-review stage",
    } for row in corpus]
    write_csv(DATA / "annotation_assignments.csv", list(assignments[0]), assignments)
    job_fields = [
        "sample_id", "source_company", "source_platform", "posting_id", "title", "raw_location",
        "source_url", "human_function", "human_seniority", "human_normalized_location",
        "human_duplicate_or_repost", "human_lifecycle_status", "reviewer_id", "annotation_timestamp",
        "ambiguity_flag", "notes",
    ]
    snapshot = json.loads((ROOT / "data/evidence_engine_v0_2/jobs_snapshot.json").read_text())
    snapshots = DATA / "jobs_snapshots"
    snapshots.mkdir(exist_ok=True)
    (snapshots / "snapshot_001_baseline.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    )
    jobs = []
    for index, job in enumerate(snapshot["jobs"][:150], 1):
        jobs.append({
            "sample_id": f"job-v03-{index:03d}", "source_company": job["company_name"],
            "source_platform": job.get("source_platform", job.get("platform", "")),
            "posting_id": job.get("posting_id", job.get("job_id", "")), "title": job["title"],
            "raw_location": job.get("location", ""), "source_url": job.get("apply_url", ""),
        })
    write_csv(DATA / "jobs_gold.csv", job_fields, jobs)
    write_csv(DATA / "jobs_snapshot_schedule.csv", [
        "scheduled_sequence", "minimum_day_offset", "purpose", "status",
    ], [
        {"scheduled_sequence": "1", "minimum_day_offset": "0", "purpose": "baseline", "status": "ready"},
        {"scheduled_sequence": "2", "minimum_day_offset": "1", "purpose": "repeat appearance and temporary absence", "status": "pending elapsed time"},
        {"scheduled_sequence": "3", "minimum_day_offset": "2", "purpose": "closure confirmation after two healthy misses", "status": "pending elapsed time"},
    ])
    manifest = {
        "schema_version": "0.3.0", "status": "awaiting_independent_human_annotation",
        "blinded_human_first": True, "frozen": False,
        "prohibition": "Do not run PIOTW extraction comparison before completed human-first annotations are frozen.",
        "blank_file_hashes": {
            name: hashlib.sha256((DATA / name).read_bytes()).hexdigest()
            for name in ("gold_observations.csv", "gold_events.csv", "jobs_gold.csv")
        },
    }
    (DATA / "annotation_freeze_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__": main()
