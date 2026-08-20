# PIOTW Procurement Signal Reliability Study v0.1 — Protocol

Status: **frozen before case retrieval and evaluation**

Methodological status: development source-first reliability study; not independent scientific validation

Cutoff: 20 August 2026 12:00 UTC

`scientific_gate_run`: `false`

## Question

Which factual features derived from UK Find a Tender contract-award notices may legitimately contribute to Detect, and in what role?

The study does not assume that publication-count movement represents company operational activity. It may retire that feature. Procurement does not need to qualify an independent condition for Detect to advance.

## Fixed source regime

The core study uses only UK Find a Tender **contract-award notices**. Contract, tender, modification, pipeline, planning and prior-information notices are excluded. Calendar publication year is the comparison period. The incomplete 2026 period is diagnostic only and cannot be compared as a full year.

Every retained record requires an immutable primary-source pointer, publication date, exact supplier legal name and UK company number, plus a traceable relationship to the canonical group. One underlying award or lot-supplier relationship is counted once; later notice versions and republications remain lineage.

No observed notice means unavailable publication coverage, never zero company activity.

## Frozen selection

Two previously reviewed exact-identifier entities are carried forward:

- Mears Limited, company number `02519234`;
- Kier Construction Limited, company number `02099533`.

The fixed additional candidate-group universe is Balfour Beatty plc, Capita plc, Mitie Group plc and Serco Group plc. For each group, retain the first operating legal entity found in primary award records only when the notice states the exact legal name and company number and a primary corporate or Companies House source establishes the group relationship. Reject rather than substitute when either boundary is ambiguous.

Retain four to six entities in total. Do not choose or replace entities because their notice patterns look useful. Frozen validation/holdout entities and entities represented only by ineligible notice types are excluded.

## Observation period

Use eligible publications from 2021 through the cutoff. Complete calendar years are compared separately. The incomplete current year is reported but excluded from full-year movement claims.

## Coverage diagnostics

For every entity and period record:

- retained unique awards;
- notice versions removed by deduplication;
- buyer count and buyer concentration;
- category coverage and mix;
- disclosed-value coverage and usable-value proportion;
- periods with no records;
- source/regime changes;
- exact legal-entity resolution rate.

Missing records, values or categories are never imputed.

## Features tested separately

1. raw award count;
2. buyer breadth;
3. award category mix;
4. disclosed contract value;
5. supplier concentration/diversification where the company is the buyer;
6. a new material, repeated or clearly strategic relationship;
7. a persistent procurement theme.

Each feature receives exactly one role:

- `INDEPENDENT CONDITION ELIGIBLE` — complete enough to create a standalone condition;
- `CORROBORATION ONLY` — independently sourced and relevant, but not sufficient alone;
- `FACTUAL ONLY` — traceable context without a reliable condition inference;
- `RETIRED` — the feature design systematically confounds source behaviour with company change.

An independent role requires a valid denominator or event-specific factual trigger, stable entity scope, adequate and comparable coverage, direct source support, no failed negative control and a defensible mechanism. Four complete comparable periods are required for aggregate movement claims.

## Negative controls

The study must explicitly test:

- repeated publications from one buyer;
- multiple notice versions for one award;
- mostly absent values;
- one large award dominating a period;
- volatile counts without broader buyer/category change;
- entity histories too shallow to interpret.

## Source-first review

For every proposed conclusion, inspect source records, deduplication lineage, coverage, buyer composition, category/value completeness, and only then the engine output. Classify it using the frozen review vocabulary in the machine-readable protocol. A technically correct number may still be a coverage or feature-design failure.

## Detect readiness

Estate and leadership decisions remain unchanged. Procurement decisions are reassessed only through the final versioned feature-role policy. If an unreliable procurement feature is retired or made factual/corroboration-only, it cannot remain a qualified condition or count as an ambiguous qualified decision.

Recompute the preserved development gate once. Return exactly one of:

- `READY_FOR_COMPARE`;
- `NOT_READY_PROCUREMENT_POLICY`;
- `NOT_READY_AMBIGUITY`;
- `NOT_READY_ENTITY_RESOLUTION`;
- `NOT_READY_OTHER`.

Detect may pass without an independently qualifying procurement feature when the remaining system meets the frozen factual, entity, precision, ambiguity, provenance, severe-error and contradiction criteria.

## Stop rule

Commit this protocol before retrieving or reviewing the fixed cases. Then run the study once through the cutoff, assign each feature one permitted role, apply the policy once and recompute Detect readiness once. Do not add replacement entities, tune thresholds, reopen estate or leadership policy, or build Compare.
