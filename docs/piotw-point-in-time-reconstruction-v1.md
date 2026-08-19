# PIOTW Point-in-Time Reconstruction v1

## Contract

A snapshot with cutoff `T` may use only a source whose `publicationDate <= T`. Effective dates, publication dates and retrieval timestamps are stored separately. The publication date controls availability.

The Travis Perkins lab uses these checkpoints:

1. 2022-03-01 — FY 2021 results available.
2. 2023-02-28 — FY 2022 presentation available.
3. 2024-03-05 — FY 2023 results available.
4. 2025-03-18 — FY 2024 results available.
5. 2025-08-05 — H1 2025 results available.
6. 2026-03-17 — FY 2025 annual report available.
7. 2026-08-04 — H1 2026 presentation available.

Each snapshot carries only the observations first published at that checkpoint in its “What changed” and evidence-drill-down view. Dimension state may use the cumulative evidence available by the cutoff, but never evidence published later.

## Provenance path

`prototype conclusion → exploratory dimension relationship → atomic observation → exact evidence span → public source`

Source records retain URL, source type, publication/effective date, fixed retrieval time, bounded raw content, SHA-256 hash and entity scope.

## Leakage guard

Automated tests assert that every observation exposed by a snapshot has `observation.asOf <= snapshot.asOf` and that its source publication date is on or before the cutoff. A future-dated source cannot enter an earlier snapshot.

This lab does not read the Evidence Engine 0.3.7 unseen corpus and is not admissible evidence for its readiness decision.
