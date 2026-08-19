# PIOTW careers history-depth audit v0.1

Status: development evidence audit, 19 August 2026. No historical snapshot was invented.

## Finding

The careers store contains 24 collection rows for 12 companies. Eleven companies have two healthy snapshots spanning 2.182 days; Anduril has two failed attempts and no factual vacancy evidence. The full raw role payload survives only for the 17 August run. The 15 August run survives as a total and collection-health record only.

The v0.1 backfill produced 11 `HISTORICAL_REPROCESSING` rich aggregates, 13 `LEGACY_SUMMARY_ONLY` aggregates, and 2,560 role rows linked to original snapshot IDs. It fabricated no role, mix or lifecycle fields for the earlier snapshot.

## Company inventory

| Company | Healthy snapshots | First / last | Span | Raw roles reconstructable | Persistence? | Mix change? |
|---|---:|---|---:|---:|---|---|
| Affirm | 2 | 15 / 17 Aug | 2.182d | 192 | No | No |
| Anduril | 0 | 2 failed attempts | n/a | 0 | No | No |
| Cloudflare | 2 | 15 / 17 Aug | 2.182d | 297 | No | No |
| Datadog | 2 | 15 / 17 Aug | 2.182d | 420 | No | No |
| Duolingo | 2 | 15 / 17 Aug | 2.182d | 67 | No | No |
| Linear | 2 | 15 / 17 Aug | 2.182d | 33 | No | No |
| MongoDB | 2 | 15 / 17 Aug | 2.182d | 404 | No | No |
| Notion | 2 | 15 / 17 Aug | 2.182d | 132 | No | No |
| Palantir | 2 | 15 / 17 Aug | 2.182d | 308 | No | No |
| Robinhood | 2 | 15 / 17 Aug | 2.182d | 124 | No | No |
| Samsara | 2 | 15 / 17 Aug | 2.182d | 269 | No | No |
| Toast | 2 | 15 / 17 Aug | 2.182d | 314 | No | No |

For each healthy company the latest snapshot now supports total and lifecycle counts (except absent-once in the historical payload), functional and seniority mix, geography/workplace mix and narrowly deterministic named technologies. The first snapshot lacks all role-level attributes. Anduril lacks all factual role data.

## Storage and reprocessing

`career_snapshot_roles` preserves snapshot-level role facts instead of only the latest lifecycle state. `career_snapshot_aggregates` stores versioned totals, lifecycle counts, distributions, missingness, derivation origin and an aggregate hash. Original raw JSON remains unchanged.

Classification fails to explicit `other_unknown` or `unknown`. Technology extraction v0.1 uses title and department only; broad job-description boilerplate is excluded because it can name company-wide platforms or competitors rather than role requirements.

## Cadence result

At 18:10 UTC on 19 August, every configured collector had a next eligible time of 21:23 UTC or later. None was due, so none ran and no third snapshot was created. The entry point now checks eligibility before network collection and records `NOT_DUE` without persisting evidence.

Historical totals support count trajectories. Historical role mix cannot be reconstructed. Future healthy runs will preserve both raw payloads and rich snapshot rows.

