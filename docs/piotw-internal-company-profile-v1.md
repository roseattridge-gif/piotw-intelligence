# PIOTW internal company profile v1

## Profile layout

The first internal profile is an evidence-led inspection page, not a dashboard scorecard.

1. **Identity and as-of time** — company, snapshot version and observation date.
2. **Source health** — last successful retrieval, next due collection, failures and unresolved entity matching.
3. **Eight dimensions** — factual observations/events, or an explicit coverage gap.
4. **Observable change** — state, change, velocity, novelty and persistence only when the stored time series supports them.
5. **Why PIOTW says this** — source URL, immutable hash, evidence time and collector/parser version.
6. **Unvalidated outputs** — prediction, overall score, benchmark, Pressure and Expansion visibly marked `NOT_YET_VALIDATED`.

## Current demonstration

The Affirm fixture has real careers evidence across two collection points. Workforce & Capability is therefore observed; the other seven dimensions are visibly incomplete. Two absent-once postings remain open because the lifecycle guard requires repeated healthy misses before closure. Find a Tender evidence remains collection-level because all supplier identities await resolution.

## Product handoff

`piotw-web` can consume this JSON later through a thin endpoint. The first UI should prioritise freshness, coverage and provenance before visualising changes. It must not manufacture unavailable scores or imply predictive validation.

