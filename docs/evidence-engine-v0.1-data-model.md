# Evidence Engine 0.1 — data model

## Intellectual object

The core object is an observable fact and its change over time, not a subjective predictive score.

```text
Feature snapshot
  -> validated observation or atomic event
     -> raw evidence record
        -> source document or careers posting
```

## Time fields

The engine keeps these separately:

- `reporting_period`: the financial/reporting period described;
- `publication_date`: the document publication date;
- `observation_date`: the period end or specific event date where known;
- `collected_at`: when PIOTW captured it;
- `information_available_at`: earliest supported time the information could enter a historical simulation.

`eligible_observations()` excludes anything whose `information_available_at` is after the requested cutoff. A dedicated test inserts/retains future-period evidence and proves it cannot enter the earlier snapshot.

## Contracts

### RawEvidence

Source identity/type/title/URL, company, reporting period, four dates, raw text, storage path, content hash, MIME type, and collector version.

### Observation

Atomic factual candidate: type, value, unit, currency, period, exact span, line/page/section, evidence ID, dates, confidence, parser version, extraction method, validation status, and optional metadata.

LLM-assisted records additionally require model and prompt version. The current demo makes zero LLM calls.

### Event

Atomic taxonomy type/group, period/date, exact evidence span, quantified flag, optional objective severity, novelty, confidence, taxonomy version, and source observation IDs.

### FeatureDefinition

Feature ID/name/version, definition, required observation types, calculation, unit, missing-data rule, lookback, and effective date. Core declarations live in `config/evidence/feature_definitions_v0_1.yaml`; `evidence_engine_v0_1/definitions.py` materializes a versioned definition for every numeric, taxonomy-derived, and jobs feature produced by the engine and persists it in SQLite.

### FeatureSnapshot

Company, feature/version, historical cutoff, value/unit, explicit calculation, input observation/event/evidence IDs, quality, and creation time.

### ReviewDecision

Observation, accept/correct/reject, reviewer, time, optional corrected value/unit, and note.

### JobRecord

Company, stable posting ID, title, inferred function/seniority, location, URL, collection time, first/last seen, and open/closed status.

## SQLite tables

All tables use the `ee01_` prefix and live in a separate database:

- `ee01_companies`
- `ee01_sources`
- `ee01_collector_runs`
- `ee01_raw_evidence`
- `ee01_extraction_runs`
- `ee01_observations`
- `ee01_review_decisions`
- `ee01_events`
- `ee01_event_evidence`
- `ee01_feature_definitions`
- `ee01_feature_snapshots`
- `ee01_feature_provenance`
- `ee01_jobs`

The schema is `database/evidence_engine_v0_1/0001_evidence_engine.sql`. Existing generic tables were not renamed or rewritten.

## Comparability controls

- A longitudinal numeric feature requires two accepted/corrected observations.
- Observations must share unit and currency.
- A zero denominator produces missing rather than an infinite percentage change.
- Missing pairs produce no snapshot; the engine does not hallucinate or zero-fill.
- Cutoff eligibility is applied before feature selection.
- Every numeric feature lists its two observation IDs and both evidence IDs.
- Language features list event IDs; event-to-observation-to-evidence joins preserve the remaining chain.

These controls do not yet resolve adjusted versus statutory definitions, restatements, or changing segment composition. Those remain explicit review responsibilities.
