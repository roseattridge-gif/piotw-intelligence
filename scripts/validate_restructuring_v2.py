"""One-command, fail-closed PIOTW restructuring validation v2 runner."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtesting.evaluation import evaluate_binary
from scripts.freeze_restructuring_v2 import verify as verify_freeze
from validation.adjudication import agreement_report
from validation.metrics_v2 import clustered_bootstrap, evaluate_rows, lead_time_summary, sensitivity
from validation.restructuring_v2 import BASELINES_PATH, baseline_probabilities, load_json
from validation.restructuring_v2_data import read_csv, validate_adjudication, validate_manifest

RESULT = ROOT / "data/derived/restructuring_validation_results_v2.json"
REPORT = ROOT / "docs/restructuring-validation-report-v2.md"
PARTITIONS = ("validation", "holdout")


def development_outcomes() -> list[dict[str, Any]]:
    predictions = json.loads((ROOT / "data/derived/restructuring_predictions_pre_outcome.json").read_text())
    prediction_by_id = {row["prediction_id"]: row for row in predictions["predictions"]}
    return [
        {"company": prediction_by_id[row["prediction_id"]]["company"],
         "status": row["outcome_status"], "occurred": int(row["occurred"])}
        for row in read_csv(ROOT / "data/restructuring/outcomes.csv")
    ]


def completeness() -> dict[str, Any]:
    evidence = read_csv(ROOT / "data/restructuring_v2/evidence.csv")
    features = read_csv(ROOT / "data/restructuring_v2/features.csv")
    reconciled = read_csv(ROOT / "data/restructuring_v2/adjudications_reconciled.csv")
    exclusions_path = ROOT / "data/restructuring_v2/occasion_exclusions.csv"
    excluded = ({row["occasion_id"] for row in read_csv(exclusions_path)}
                if exclusions_path.exists() else set())
    required = []
    by_partition = {}
    for partition in PARTITIONS:
        manifest = read_csv(ROOT / f"data/manifests/restructuring_{partition}.csv")
        included = {row["occasion_id"] for row in manifest
                    if row["inclusion_status"].startswith("included")
                    and row["occasion_id"] not in excluded}
        required.extend(included)
        by_partition[partition] = len(included)
    evidence_coverage = {row["occasion_id"] for row in evidence}
    feature_coverage = {row["occasion_id"] for row in features}
    outcome_coverage = {row["occasion_id"] for row in reconciled}
    required_set = set(required)
    prediction_files = {
        partition: ROOT / f"data/derived/restructuring_{partition}_predictions_v2.json"
        for partition in PARTITIONS
    }
    prediction_counts = {}
    for partition, path in prediction_files.items():
        prediction_counts[partition] = (
            json.loads(path.read_text()).get("prediction_count", 0) if path.exists() else 0
        )
    return {
        "required": len(required_set), "manifest_occasions": len(required_set | excluded),
        "excluded": len(excluded), "excluded_occasions": sorted(excluded),
        "by_partition": by_partition,
        "evidence_complete": len(required_set & evidence_coverage),
        "features_complete": len(required_set & feature_coverage),
        "outcomes_complete": len(required_set & outcome_coverage),
        "prediction_counts": prediction_counts,
        "missing_evidence": sorted(required_set - evidence_coverage),
        "missing_features": sorted(required_set - feature_coverage),
        "missing_outcomes": sorted(required_set - outcome_coverage),
    }


def write_pending(lock: dict[str, Any], coverage: dict[str, Any]) -> None:
    predictions = sum(coverage["prediction_counts"].values())
    if coverage["features_complete"] < coverage["required"]:
        next_action = "Complete and review pre-cutoff evidence and frozen-rubric feature rows."
    elif predictions < coverage["required"]:
        next_action = "Register and commit immutable predictions before any outcome review."
    else:
        next_action = "Complete blinded outcome adjudication, then reconcile the labels."
    result = {"status": "INCOMPLETE", "frozen_lock": lock, "coverage": coverage,
              "next_action": next_action,
              "answer": "Validation v2 cannot be evaluated until frozen predictions and blinded adjudications are complete."}
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    REPORT.write_text(
        "# PIOTW restructuring validation report v2\n\n"
        "Status: **INCOMPLETE — no v2 performance result is reported.**\n\n"
        f"The frozen manifests retain {coverage['manifest_occasions']} occasions: "
        f"{coverage['required']} are prediction-eligible and {coverage['excluded']} are retained "
        f"frozen-rule exclusions. Evidence exists for "
        f"{coverage['evidence_complete']}, features for {coverage['features_complete']}, and reconciled "
        f"blinded outcomes for {coverage['outcomes_complete']}. Immutable predictions have been generated "
        f"for {predictions}. The runner fails closed rather than evaluating a convenient subset.\n\n"
        f"Next action: **{next_action}**\n")


def joined_rows(partition: str, predictions_doc: dict[str, Any],
                adjudications: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    evidence_by_occasion: dict[str, list[dict[str, str]]] = {}
    for evidence in read_csv(ROOT / "data/restructuring_v2/evidence.csv"):
        evidence_by_occasion.setdefault(evidence["occasion_id"], []).append(evidence)
    development = development_outcomes()
    rows = []
    for prediction in predictions_doc["predictions"]:
        adjudication = adjudications[prediction["occasion_id"]]
        if adjudication["adjudication"] == "uncertain":
            continue
        text = "\n".join(row["observation"] for row in evidence_by_occasion[prediction["occasion_id"]])
        baselines = baseline_probabilities(prediction["features"], text, prediction["company"], development)
        outcome = int(adjudication["adjudication"] == "positive")
        lead_time = ((date.fromisoformat(adjudication["event_date"]) - date.fromisoformat(prediction["cutoff"])).days
                     if outcome else "")
        rows.append({**prediction, **baselines, "outcome": outcome, "lead_time_days": lead_time,
                     "outcome_source_url": adjudication["source_url"]})
    return rows


def evaluate_partition(rows: list[dict[str, Any]], baseline_names: list[str],
                       config: dict[str, Any]) -> dict[str, Any]:
    edges = config["evaluation"]["calibration_bin_edges"]
    outcomes = [int(row["outcome"]) for row in rows]
    baseline_results = {}
    for name in baseline_names:
        baseline_results[name] = asdict(evaluate_binary([float(row[name]) for row in rows], outcomes))
    return {
        "occasion_count": len(rows), "unique_companies": len({row["stable_id"] for row in rows}),
        "positive_count": sum(outcomes), "prevalence": sum(outcomes) / len(outcomes),
        "piotw": evaluate_rows(rows, edges), "baselines": baseline_results,
        "lead_time": lead_time_summary(rows),
        "bootstrap": clustered_bootstrap(rows, config["evaluation"]["bootstrap"]["replicates"],
                                         config["evaluation"]["bootstrap"]["seed"]),
        "sensitivity": sensitivity(rows, edges),
    }


def gate(holdout: dict[str, Any], rows: list[dict[str, Any]], agreement: dict[str, Any]) -> dict[str, Any]:
    strongest = min(value["brier_score"] for value in holdout["baselines"].values())
    piotw = holdout["piotw"]
    sensitivity_rows = holdout["sensitivity"]["leave_one_company_out"]
    robust = all(value["brier_skill_vs_constant_prior"] > 0 and (value["roc_auc"] or 0) > 0.5
                 for value in sensitivity_rows.values())
    positive_by_sector: dict[str, int] = {}
    for row in rows:
        positive_by_sector[row["stratum"]] = positive_by_sector.get(row["stratum"], 0) + int(row["outcome"])
    sector_share = max(positive_by_sector.values(), default=0) / holdout["positive_count"] if holdout["positive_count"] else 1
    checks = {
        "brier_skill_positive": piotw["brier_skill_vs_constant_prior"] > 0,
        "within_0_01_of_strongest_baseline": piotw["brier_score"] <= strongest + 0.01,
        "top_quintile_lift": piotw["top_risk_group"]["lift"] > 1 and piotw["top_risk_group"]["positive_count"] >= 2,
        "auc_above_random": (piotw["roc_auc"] or 0) > 0.5,
        "median_lead_at_least_90_days": (holdout["lead_time"]["median"] or 0) >= 90,
        "company_and_sector_robustness": robust and sector_share <= 0.60,
        "adjudication_integrity": agreement["raw_agreement"] is None or agreement["raw_agreement"] >= 0.90,
    }
    sufficient = holdout["occasion_count"] >= 50 and holdout["unique_companies"] >= 40 and holdout["positive_count"] >= 8
    passed = sum(checks.values())
    if not sufficient:
        decision = "INSUFFICIENT EVIDENCE"
    elif passed == 7:
        decision = "PASS FOR NEXT-STAGE PRODUCT RESEARCH"
    elif passed >= 5:
        decision = "PROMISING / CONTINUE VALIDATION"
    else:
        decision = "FAIL"
    return {"decision": decision, "minimum_sample_satisfied": sufficient,
            "criteria_passed": passed, "criteria": checks, "sector_positive_share_max": sector_share}


def report_markdown(result: dict[str, Any]) -> str:
    lines = ["# PIOTW restructuring validation report v2", "",
             f"Decision: **{result['gate']['decision']}**", "",
             "The frozen PIOTW Rules 1.0.0 model was evaluated without tuning on the new outcomes.", ""]
    for partition in PARTITIONS:
        section = result["partitions"][partition]
        piotw = section["piotw"]
        lines.extend([
            f"## {partition.title()}", "",
            (f"{section['occasion_count']} occasions, {section['unique_companies']} companies, "
             f"{section['positive_count']} positives ({section['prevalence']:.1%} prevalence)."),
            "",
            (f"PIOTW Brier {piotw['brier_score']:.6f}; Brier skill vs frozen prior "
             f"{piotw['brier_skill_vs_constant_prior']:.3f}; ROC AUC {piotw['roc_auc']}; "
             f"average precision {piotw['average_precision']:.6f}; top-group lift "
             f"{piotw['top_risk_group']['lift']:.3f}."), "",
            (f"True-positive lead time: n={section['lead_time']['count']}, median="
             f"{section['lead_time']['median']} days, mean={section['lead_time']['mean']} days, "
             f"range={section['lead_time']['minimum']}–{section['lead_time']['maximum']} days."), "",
        ])
    lines.extend(["## Limitations", "",
                  ("This gate is a research-stage decision, not production readiness, statistical proof, "
                   "commercial superiority or validated proprietary intelligence. Full hashes, calibration, "
                   "bootstrap intervals, baseline results and sensitivity tables are in the machine-readable JSON."), ""])
    return "\n".join(lines)


def main() -> None:
    lock = verify_freeze()
    for partition in PARTITIONS:
        validate_manifest(read_csv(ROOT / f"data/manifests/restructuring_{partition}.csv"), partition)
    subprocess.run([sys.executable, str(ROOT / "scripts/build_restructuring_feature_diagnostics_v2.py")], check=True)
    coverage = completeness()
    if any(coverage[name] != coverage["required"] for name in (
            "evidence_complete", "features_complete")):
        write_pending(lock, coverage)
        print(f"v2 incomplete: {coverage['features_complete']}/{coverage['required']} feature rows; "
              f"{coverage['outcomes_complete']}/{coverage['required']} outcomes")
        return
    for partition in PARTITIONS:
        subprocess.run([sys.executable, str(ROOT / "scripts/register_restructuring_v2_predictions.py"), partition], check=True)
    coverage = completeness()
    if coverage["outcomes_complete"] != coverage["required"]:
        write_pending(lock, coverage)
        print(f"v2 predictions frozen: {sum(coverage['prediction_counts'].values())}/{coverage['required']}; "
              f"outcomes incomplete: {coverage['outcomes_complete']}/{coverage['required']}")
        return
    first = read_csv(ROOT / "data/restructuring_v2/adjudications_reviewer_1.csv")
    second = read_csv(ROOT / "data/restructuring_v2/adjudications_reviewer_2.csv")
    agreement = agreement_report(first, second)
    reconciled_rows = read_csv(ROOT / "data/restructuring_v2/adjudications_reconciled.csv")
    manifests = {row["occasion_id"]: row for partition in PARTITIONS for row in read_csv(
        ROOT / f"data/manifests/restructuring_{partition}.csv")}
    for row in reconciled_rows:
        validate_adjudication(row, manifests[row["occasion_id"]])
    reconciled = {row["occasion_id"]: row for row in reconciled_rows}
    config = load_json(BASELINES_PATH)
    baseline_names = list(config["comparators"])
    partition_rows = {}
    partition_results = {}
    for partition in PARTITIONS:
        predictions = json.loads((ROOT / f"data/derived/restructuring_{partition}_predictions_v2.json").read_text())
        partition_rows[partition] = joined_rows(partition, predictions, reconciled)
        partition_results[partition] = evaluate_partition(partition_rows[partition], baseline_names, config)
    result = {"status": "COMPLETE", "frozen_lock": lock, "agreement": agreement,
              "partitions": partition_results,
              "gate": gate(partition_results["holdout"], partition_rows["holdout"], agreement)}
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    REPORT.write_text(report_markdown(result))
    print(result["gate"]["decision"])


if __name__ == "__main__":
    main()
