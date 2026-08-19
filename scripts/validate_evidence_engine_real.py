from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_engine_v0_2.evaluate import run


def report(results: dict) -> str:
    corpus = results["corpus"]
    numeric = results["numerical_extraction"]
    events = results["event_extraction"]
    jobs = results["jobs"]
    ordinary_rate = (f"{numeric['ordinary_report_accuracy']['rate']:.1%}"
                     if numeric["ordinary_report_accuracy"]["rate"] is not None else "n/a")
    return f"""# Evidence Engine 0.2 — real-world validation

## Decision

**{results['model2_readiness']['status']}**

Reasons: {'; '.join(results['model2_readiness']['reasons'])}.

No restructuring outcomes were used, no predictive model was trained, and no Pressure or Expansion score was created.

## Corpus

- {corpus['companies']} real US public companies
- {corpus['documents']} historical SEC filings across {corpus['periods']} company-periods
- report types: {json.dumps(corpus['report_types'], sort_keys=True)}
- difficulty: {json.dumps(corpus['difficulty'], sort_keys=True)}
- {corpus['gold_numerical_facts']} independently sourced iXBRL gold numerical facts
- {corpus['gold_event_cases']} contextual event cases from 15 difficult filings

The corpus is separate from every frozen UK restructuring company and carries `external_us_development_no_outcomes` status.

## Numerical extraction

| Measure | Correct | Total | Rate |
|---|---:|---:|---:|
| Complete observation | {numeric['complete_observation_accuracy']['correct']} | {numeric['complete_observation_accuracy']['total']} | {numeric['complete_observation_accuracy']['rate']:.1%} |
| Metric identity | {numeric['metric_identity']['correct']} | {numeric['metric_identity']['total']} | {numeric['metric_identity']['rate']:.1%} |
| Value | {numeric['value']['correct']} | {numeric['value']['total']} | {numeric['value']['rate']:.1%} |
| Reporting period | {numeric['reporting_period']['correct']} | {numeric['reporting_period']['total']} | {numeric['reporting_period']['rate']:.1%} |
| Currency | {numeric['currency']['correct']} | {numeric['currency']['total']} | {numeric['currency']['rate']:.1%} |
| Unit | {numeric['unit']['correct']} | {numeric['unit']['total']} | {numeric['unit']['rate']:.1%} |
| Accounting basis | {numeric['accounting_basis']['correct']} | {numeric['accounting_basis']['total']} | {numeric['accounting_basis']['rate']:.1%} |
| Provenance span | {numeric['provenance_span']['correct']} | {numeric['provenance_span']['total']} | {numeric['provenance_span']['rate']:.1%} |
| Difficult reports | {numeric['difficult_report_accuracy']['correct']} | {numeric['difficult_report_accuracy']['total']} | {numeric['difficult_report_accuracy']['rate']:.1%} |
| Ordinary reports | {numeric['ordinary_report_accuracy']['correct']} | {numeric['ordinary_report_accuracy']['total']} | {ordinary_rate} |

Severe errors: {numeric['severe_errors']['count']}/{numeric['severe_errors']['total']} ({numeric['severe_errors']['rate']:.1%}).

Important limitation: the gold values are independently selected consolidated SEC iXBRL facts, not a complete manual visual transcription of every table. This benchmark validates iXBRL identity, period, unit, scale, and provenance handling; it does not prove OCR/PDF table accuracy.

The 12 reports tagged ordinary are regulatory 8-K primary documents with no selected numerical iXBRL gold facts, so ordinary-report numerical accuracy is `0/0`, not 100%. This missing benchmark stratum is a readiness failure.

## Event extraction

- true positives: {events['true_positives']}
- false positives: {events['false_positives']}
- false negatives: {events['false_negatives']}
- precision: {events['precision']:.1%}
- recall: {events['recall']:.1%}
- F1: {events['f1']:.1%}
- wrong-context extractions: {events['wrong_context_count']}

The benchmark includes explicit negated and historical/completed cases. Individual-type counts and examples are in the machine-readable JSON.

## Longitudinal features

Gold-observation-to-feature correctness: {results['longitudinal_features']['overall']['correct']}/{results['longitudinal_features']['overall']['total']} ({results['longitudinal_features']['overall']['rate']:.1%}). This compares features calculated independently from gold observations with features calculated from extracted observations.

## Review burden

- structured iXBRL fact matches: {results['review_workload']['structured_fact_match']['correct']}/{results['review_workload']['structured_fact_match']['total']}
- independent manual acceptance/correction/rejection rates: **not measured**
- median human review time: **not measured**

Because visual manual review timing and correction burden were not captured, the readiness gate cannot pass.

## Jobs collector

- sources succeeded: {jobs['companies_succeeded']}/{jobs['companies_attempted']}
- platforms: {', '.join(jobs['platforms'])}
- current postings collected: {jobs['jobs_collected']}
- reviewed sample: {jobs['gold_sample']}
- function accuracy: {jobs['function_accuracy']['correct']}/{jobs['function_accuracy']['total']} ({jobs['function_accuracy']['rate']:.1%})
- seniority accuracy: {jobs['seniority_accuracy']['correct']}/{jobs['seniority_accuracy']['total']} ({jobs['seniority_accuracy']['rate']:.1%})
- location accuracy: {jobs['location_accuracy']['correct']}/{jobs['location_accuracy']['total']} ({jobs['location_accuracy']['rate']:.1%})
- discovery recall and real false-closure rate: **not measurable from one live snapshot**

Repeated-miss confirmation, fetch-health checks, and suspicious-drop outage suppression are implemented and regression-tested. A real longitudinal jobs trial remains required.

## Provenance

Exact iXBRL source-span completeness is {results['provenance']['complete']}/{results['provenance']['total']} ({results['provenance']['rate']:.1%}). Each fact retains filing URL/document ID, context, period, unit, scale, taxonomy identity, and exact tagged span.

## Cost and scalability

- local deterministic parser median: {results['cost_and_scale']['compute_median_seconds_per_report']:.4f} seconds/report
- raw report storage: {results['cost_and_scale']['average_raw_bytes_per_report']:,} bytes/report average
- direct source/LLM cost: $0
- jobs collection runtime: {results['cost_and_scale']['jobs_runtime_seconds']:.1f} seconds
- jobs source failures: {results['cost_and_scale']['jobs_failure_frequency']['correct']}/{results['cost_and_scale']['jobs_failure_frequency']['total']}

At current raw-storage density, 100/1,000/10,000 companies with three reports each require approximately {results['cost_and_scale']['average_raw_bytes_per_report']*300/1e9:.2f} GB, {results['cost_and_scale']['average_raw_bytes_per_report']*3000/1e9:.2f} GB, and {results['cost_and_scale']['average_raw_bytes_per_report']*30000/1e9:.2f} GB respectively, before database indexes and future snapshots. Human review—not compute—is likely the binding cost.

## Failure analysis

The largest unresolved risk is **benchmark independence and visual-table coverage**: iXBRL gives strong structured provenance but does not prove extraction from PDF reading order, image tables, or issuer-defined adjusted metrics. Other open risks are current-only jobs coverage, incomplete discovery truth, one failed ATS source, sentence-level rather than page-level event provenance, and context ambiguity beyond the explicit negation/history rules.

See `data/evidence_engine_v0_2/extraction_failure_log.csv` and `data/evidence_engine_v0_2/review_workload_summary.csv`.
"""


def main() -> None:
    results = run(ROOT)
    output = ROOT / "data/derived/evidence_engine_v0_2_results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    document = ROOT / "docs/evidence-engine-v0.2-real-world-validation.md"
    document.write_text(report(results))
    failures = [
        ["F-001", "gold_independence", "high", "SEC iXBRL facts are source-grounded but not fully manually transcribed from visual tables", "open"],
        ["F-002", "review_timing", "high", "Median human review time was not captured", "open"],
        ["F-003", "jobs_history", "high", "One live snapshot cannot measure discovery recall or false closure", "open"],
        ["F-004", "jobs_source", "medium", "One configured Lever source returned 404", "open"],
        ["F-005", "event_location", "medium", "HTML events retain exact sentence but not PDF page number", "open"],
        ["F-006", "event_gold_independence", "high", "Event gold uses the frozen pattern lexicon and is not an independent exhaustive manual annotation", "open"],
        ["F-007", "jobs_gold_independence", "high", "Jobs labels reuse deterministic title rules and have only one live snapshot", "open"],
        ["F-008", "ordinary_numeric_coverage", "high", "Ordinary 8-K reports contain no numerical gold facts", "open"],
    ]
    with (ROOT / "data/evidence_engine_v0_2/extraction_failure_log.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n"); writer.writerow(["failure_id", "category", "severity", "description", "status"]); writer.writerows(failures)
    with (ROOT / "data/evidence_engine_v0_2/review_workload_summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n"); writer.writerow(["measure", "numerator", "denominator", "rate", "note"])
        acceptance = results["review_workload"]["structured_fact_match"]
        writer.writerow(["structured_fact_match", acceptance["correct"], acceptance["total"], acceptance["rate"], "Not a timed visual review"])
        writer.writerow(["manual_corrections", "", "", "", "not measured"])
        writer.writerow(["manual_review_time", "", "", "", "not measured"])
    print(json.dumps({"status": results["model2_readiness"]["status"], "corpus": results["corpus"],
                      "numeric": results["numerical_extraction"]["complete_observation_accuracy"],
                      "events": {key: results["event_extraction"][key] for key in ("precision", "recall", "f1")},
                      "longitudinal": results["longitudinal_features"]["overall"],
                      "jobs": {"succeeded": results["jobs"]["companies_succeeded"],
                               "attempted": results["jobs"]["companies_attempted"]}}, indent=2))


if __name__ == "__main__":
    main()
