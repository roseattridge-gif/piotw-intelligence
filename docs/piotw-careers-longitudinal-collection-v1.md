# PIOTW Careers Longitudinal Collection v1

Status: development collection foundation; no predictive interpretation.

0.3.6 stability note (18 August 2026): 12 company sources have two collection points each; 11 are healthy and Anduril is fetch-failed. The store contains 2,619 open identities. Fifty-nine are absent on one healthy run and remain open pending confirmation. This proves lifecycle mechanics, but two points are not enough for stable longitudinal features.

## Implemented

`pipelines/careers/longitudinal.py` records a 48-hour desired cadence, successful-fetch time, next eligible fetch, consecutive failures, exponential backoff, source health and content hashes. It stores one lifecycle row per stable company/provider/job identity with title, deterministic function and seniority classifications, location, URL, first/last seen, status, confirmed-absence count, reopen count and record hash.

Each run also writes `source_health.json`, including last success, consecutive failures, posting-count delta, anomaly flag, source adapter, expected cadence, next due time and stale-source flag. Failed sources remain visible; they are never silently removed from the report.

Closure requires two healthy absent snapshots. Failed fetches and anomalous site-wide drops cannot close jobs. Reappearance after confirmed closure increments a reopen counter. Identical company/provider/timestamp snapshots are idempotent.

## Current coverage

The original live baseline attempted 12 companies, succeeded for 11 and captured 2,540 vacancies across Greenhouse, Lever and Ashby. A second live collection on 17 August 2026 captured 2,560 open postings across the same 11 healthy sources; Anduril failed again. Across the two snapshots, 2,481 stable identities persisted, 79 appeared newly and 59 were absent once. Those 59 remain open pending a second healthy absence; none was falsely closed. The lifecycle database now contains 24 company-source snapshots (12 sources × 2 collection times) and 2,619 open identities.

This is two-point longitudinal history, enough to exercise lifecycle safeguards but not enough to interpret trends or estimate false-closure rates empirically.

## Operating plan

- Collect eligible sources every two days.
- Persist raw response/snapshot before lifecycle processing.
- Treat source health separately from company change.
- Retain unsuccessful runs and backoff state.
- Review ambiguous reposts and classification changes.
- Do not emit change/velocity features until repeated real healthy snapshots exist.

No cloud scheduler was deployed. The database interface contains all scheduling metadata needed for a local/hosted runner later.

As of 18 August 2026 the most recent collection was not yet 48 hours old, so no premature third live fetch was forced. Anduril remains explicitly degraded/fetch-failed.
