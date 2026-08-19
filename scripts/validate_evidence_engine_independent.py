from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_1.guard import verify_frozen_isolation
from evidence_engine_v0_3.blinding import verify_frozen_annotations


def count(path: Path) -> int:
    with path.open(newline="") as stream: return sum(1 for _ in csv.DictReader(stream))


def main() -> None:
    protected = verify_frozen_isolation(ROOT)
    data = ROOT / "data/evidence_engine_v0_3"
    with (data / "corpus_manifest.csv").open(newline="") as stream:
        corpus = list(csv.DictReader(stream))
    if len(corpus) != 30 or len({row["ticker"] for row in corpus}) != 15:
        raise SystemExit("0.3 corpus must contain 15 companies and 30 reports")
    if any(row["development_safe_status"] != "external_us_development_no_outcomes" for row in corpus):
        raise SystemExit("unsafe corpus partition")
    reasons = []
    try:
        freeze = verify_frozen_annotations(data)
        gold_ready = True
    except ValueError as exc:
        freeze = json.loads((data / "annotation_freeze_manifest.json").read_text())
        gold_ready = False; reasons.append(str(exc))
    job_rows = list(csv.DictReader((data / "jobs_gold.csv").open()))
    jobs_sample = len(job_rows)
    jobs_gold = sum(bool(row["reviewer_id"] and row["annotation_timestamp"] and row["human_function"])
                    for row in job_rows)
    review_rows = list(csv.DictReader((data / "review_workflow_log.csv").open()))
    timed_reviews = sum(bool(row["elapsed_seconds"]) for row in review_rows)
    if jobs_gold < 100: reasons.append(f"independent jobs labels incomplete ({jobs_gold}/100 minimum)")
    if timed_reviews == 0: reasons.append("no human review timings recorded")
    status = "NOT READY"
    source_bytes = sum((ROOT / row["source_artifact"]).stat().st_size for row in corpus)
    pdf_bytes = sum((ROOT / row["reviewer_pdf"]).stat().st_size for row in corpus)
    results = {
        "engine_version": "0.3.0", "status": status,
        "evaluation_stage": "pre_evaluation_blocked" if not gold_ready else "gold_frozen_pending_full_scoring",
        "reasons": reasons, "frozen_rules_artefacts_verified": len(protected),
        "outcomes_used": False, "predictive_model_trained": False,
        "corpus": {"companies": len({row["ticker"] for row in corpus}), "reports": len(corpus),
                   "difficult_reports": sum(row["difficulty_class"] == "difficult" for row in corpus)},
        "independent_gold": {"frozen": gold_ready,
            "numerical_facts": count(data / "gold_observations.csv"),
            "events": count(data / "gold_events.csv"), "jobs": jobs_gold,
            "jobs_sample_prepared": jobs_sample},
        "review_burden": {"timed_reports": timed_reviews, "total_reports": len(review_rows)},
        "prepared_artifacts": {"source_bytes": source_bytes, "reviewer_pdf_bytes": pdf_bytes,
                               "jobs_snapshots": len(list((data / "jobs_snapshots").glob("*.json")))},
        "metrics": {name: {"correct": 0, "total": 0, "rate": None, "status": "not_scored_before_gold_freeze"}
                    for name in ("overall_numerical_accuracy", "strategic_metric_accuracy", "severe_error_rate",
                                 "accounting_basis_accuracy", "period_accuracy", "event_precision", "event_recall",
                                 "event_f1", "provenance_completeness", "longitudinal_feature_accuracy",
                                 "manual_acceptance_rate", "manual_correction_rate", "manual_rejection_rate",
                                 "review_time_saved", "jobs_classification_accuracy", "jobs_lifecycle_reliability")},
        "annotation_manifest": freeze,
    }
    output = ROOT / "data/derived/evidence_engine_v0_3_results.json"
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": status, "stage": results["evaluation_stage"],
                      "protected_artefacts": len(protected), "corpus": results["corpus"],
                      "reasons": reasons}, indent=2))


if __name__ == "__main__": main()
