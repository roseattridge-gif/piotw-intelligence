# Evidence Engine 0.2 — real-world validation

## Decision

**NOT READY**

Reasons: jobs discovery recall not measured; real false-closure rate not measured; manual review timing and visually independent table transcription not completed; event gold uses the same frozen pattern lexicon and is not an independent exhaustive annotation; jobs classification gold is not independent and only one live snapshot exists; ordinary reports contain no numerical gold facts in this corpus.

No restructuring outcomes were used, no predictive model was trained, and no Pressure or Expansion score was created.

## Corpus

- 25 real US public companies
- 75 historical SEC filings across 75 company-periods
- report types: {"annual_report": 50, "interim_report": 13, "regulatory_results_announcement": 12}
- difficulty: {"difficult": 63, "ordinary": 12}
- 363 independently sourced iXBRL gold numerical facts
- 284 contextual event cases from 15 difficult filings

The corpus is separate from every frozen UK restructuring company and carries `external_us_development_no_outcomes` status.

## Numerical extraction

| Measure | Correct | Total | Rate |
|---|---:|---:|---:|
| Complete observation | 363 | 363 | 100.0% |
| Metric identity | 363 | 363 | 100.0% |
| Value | 363 | 363 | 100.0% |
| Reporting period | 363 | 363 | 100.0% |
| Currency | 363 | 363 | 100.0% |
| Unit | 363 | 363 | 100.0% |
| Accounting basis | 363 | 363 | 100.0% |
| Provenance span | 363 | 363 | 100.0% |
| Difficult reports | 363 | 363 | 100.0% |
| Ordinary reports | 0 | 0 | n/a |

Severe errors: 0/363 (0.0%).

Important limitation: the gold values are independently selected consolidated SEC iXBRL facts, not a complete manual visual transcription of every table. This benchmark validates iXBRL identity, period, unit, scale, and provenance handling; it does not prove OCR/PDF table accuracy.

The 12 reports tagged ordinary are regulatory 8-K primary documents with no selected numerical iXBRL gold facts, so ordinary-report numerical accuracy is `0/0`, not 100%. This missing benchmark stratum is a readiness failure.

## Event extraction

- true positives: 261
- false positives: 0
- false negatives: 0
- precision: 100.0%
- recall: 100.0%
- F1: 100.0%
- wrong-context extractions: 0

The benchmark includes explicit negated and historical/completed cases. Individual-type counts and examples are in the machine-readable JSON.

## Longitudinal features

Gold-observation-to-feature correctness: 141/141 (100.0%). This compares features calculated independently from gold observations with features calculated from extracted observations.

## Review burden

- structured iXBRL fact matches: 363/363
- independent manual acceptance/correction/rejection rates: **not measured**
- median human review time: **not measured**

Because visual manual review timing and correction burden were not captured, the readiness gate cannot pass.

## Jobs collector

- sources succeeded: 11/12
- platforms: ashby, greenhouse, lever
- current postings collected: 2540
- reviewed sample: 110
- function accuracy: 110/110 (100.0%)
- seniority accuracy: 110/110 (100.0%)
- location accuracy: 110/110 (100.0%)
- discovery recall and real false-closure rate: **not measurable from one live snapshot**

Repeated-miss confirmation, fetch-health checks, and suspicious-drop outage suppression are implemented and regression-tested. A real longitudinal jobs trial remains required.

## Provenance

Exact iXBRL source-span completeness is 363/363 (100.0%). Each fact retains filing URL/document ID, context, period, unit, scale, taxonomy identity, and exact tagged span.

## Cost and scalability

- local deterministic parser median: 0.0128 seconds/report
- raw report storage: 3,737,798 bytes/report average
- direct source/LLM cost: $0
- jobs collection runtime: 29.5 seconds
- jobs source failures: 1/12

At current raw-storage density, 100/1,000/10,000 companies with three reports each require approximately 1.12 GB, 11.21 GB, and 112.13 GB respectively, before database indexes and future snapshots. Human review—not compute—is likely the binding cost.

## Failure analysis

The largest unresolved risk is **benchmark independence and visual-table coverage**: iXBRL gives strong structured provenance but does not prove extraction from PDF reading order, image tables, or issuer-defined adjusted metrics. Other open risks are current-only jobs coverage, incomplete discovery truth, one failed ATS source, sentence-level rather than page-level event provenance, and context ambiguity beyond the explicit negation/history rules.

See `data/evidence_engine_v0_2/extraction_failure_log.csv` and `data/evidence_engine_v0_2/review_workload_summary.csv`.
