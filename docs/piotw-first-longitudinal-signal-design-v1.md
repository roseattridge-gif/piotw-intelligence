# PIOTW first longitudinal signal design v1

Status: **DESIGN ONLY — NO SCORE, WEIGHT OR PREDICTIVE CLAIM**

## Purpose

The first future signal layer should convert repeated careers observations into transparent longitudinal features. It must preserve the distinction between a fact (a posting was observed), a derived feature (the observed count changed), an interpretation, and a future prediction. Nothing in this design says that more or fewer vacancies is inherently good, bad, expansionary or distressed.

## Canonical raw inputs

Each calculation uses only successful, point-in-time careers snapshots and the canonical job lifecycle record:

- company ID and source/ATS;
- retrieval timestamp and source-health status;
- stable job ID, posting URL and source hash;
- title, function, seniority and normalized location;
- first seen and last seen;
- open, absent-once, confirmed-closed or reopened status;
- consecutive healthy misses and collection failure state.

Failed or anomalous site collections are source-health evidence. They are not vacancy closures.

## Candidate transparent features

| Primitive | Definition | Minimum history | Missing-data behaviour | Potential future relevance | Test approach |
|---|---|---:|---|---|---|
| Current state | Count of open postings at cutoff T, optionally by function, seniority or geography | 1 healthy snapshot | Missing when no healthy snapshot exists | Describes observed hiring demand at one point, without interpretation | Reconcile count to unique open lifecycle rows and source snapshot |
| Change | Current state minus the immediately preceding comparable healthy snapshot | 2 healthy snapshots | Missing if either snapshot is unavailable or incomparable | Captures the direction and size of observable movement | Gold-check new, persistent, absent and reopened identities between two frozen snapshots |
| Velocity | Change divided by elapsed days, reported as postings per day and with the exact interval | 3 healthy snapshots preferred; 2 allowed as provisional | Missing across collection gaps above a declared maximum | Makes unequal collection intervals explicit | Verify timestamps, interval arithmetic and invariance to reruns of the same snapshot |
| Persistence | Number of consecutive healthy snapshots in which the same posting or aggregate condition remains observed | 2 healthy snapshots | Reset only by a confirmed state transition, never by a failed fetch | Separates one-off appearances from sustained observations | Test persistent IDs, temporary absence, closure confirmation and reopening |
| Novelty | First observed appearance of a job, function, seniority class or geography within the retained history | At least 3 healthy snapshots or a declared 30-day clean lookback | Unknown rather than new when earlier history is insufficient | Identifies genuinely new observed categories once history is deep enough | Backfill a frozen sequence and prove first-seen flags are stable at historical cutoffs |

## Minimum-history states

- One healthy snapshot: `CURRENT_STATE_ONLY`.
- Two healthy snapshots: `EARLY_CHANGE_HISTORY`; change may be shown, but not stable velocity.
- Three to five healthy snapshots: `PROVISIONAL_LONGITUDINAL_HISTORY`.
- Six or more healthy snapshots spanning at least 30 days: eligible for declared velocity, persistence and novelty calculations, subject to source health.

These labels describe data depth, not confidence in company performance.

## Point-in-time and missingness rules

1. A feature at cutoff T uses only snapshots retrieved at or before T.
2. Repeated ingestion of identical source content cannot create a new observation or alter first-seen time.
3. A failed fetch produces no zero-vacancy state and no closure.
4. Closure requires the existing repeated-healthy-miss rule.
5. A material ATS or page-structure change marks the series incomparable until reviewed.
6. Missing function, seniority or location stays missing; it is not assigned to an inferred category.
7. Counts always expose their denominator, interval and source-health coverage.

## Validation before use

Freeze a development corpus of real repeated snapshots, then independently verify job identity, lifecycle state and classifications. Test state, change, elapsed-time velocity, persistence and novelty against manually reconstructed histories. Report exact counts, severe lifecycle errors, source-outage behaviour and review burden. Only after these features are reproducible should a separate, preregistered experiment test whether any feature relates to a defined outcome.

## Explicit non-goals

This design does not create a careers signal score, risk score, Pressure, Expansion, benchmark, company rank or predictor weight. It makes observable change reproducible so later interpretation and prediction can be tested rather than assumed.
